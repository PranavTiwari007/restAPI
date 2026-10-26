from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
import logging
import os
from pathlib import Path
import sqlite3
import ssl
from typing import Literal

import httpx
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.database import (
    DEFAULT_DATABASE_PATH,
    connect,
    get_aircraft_state,
    get_latest_snapshot,
    initialize_database,
    list_latest_aircraft_states,
    save_snapshot,
)
from app.opensky_client import (
    BoundingBox,
    OpenSkyClient,
    OpenSkyResponseError,
)
from app.state_mapping import AircraftStateRecord, map_state_vector


PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env", override=False)
logger = logging.getLogger(__name__)


class StateImportRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    lamin: float = Field(ge=-90, le=90, allow_inf_nan=False)
    lomin: float = Field(ge=-180, le=180, allow_inf_nan=False)
    lamax: float = Field(ge=-90, le=90, allow_inf_nan=False)
    lomax: float = Field(ge=-180, le=180, allow_inf_nan=False)

    @model_validator(mode="after")
    def validate_order(self) -> "StateImportRequest":
        if self.lamin >= self.lamax:
            raise ValueError("lamin must be less than lamax")
        if self.lomin >= self.lomax:
            raise ValueError("lomin must be less than lomax")
        return self

    def to_bounds(self) -> BoundingBox:
        return BoundingBox(self.lamin, self.lomin, self.lamax, self.lomax)


class StateImportResponse(BaseModel):
    snapshot_id: int
    provider_time: int
    imported_count: int


class SnapshotResponse(BaseModel):
    id: int
    provider_time: int
    imported_at: str
    lamin: float
    lomin: float
    lamax: float
    lomax: float
    state_count: int


class AircraftStateResponse(BaseModel):
    id: int
    snapshot_id: int
    icao24: str
    callsign: str | None
    origin_country: str
    last_contact: int
    longitude: float | None
    latitude: float | None
    baro_altitude: float | None
    on_ground: bool
    velocity: float | None
    true_track: float | None
    vertical_rate: float | None
    geo_altitude: float | None
    squawk: str | None
    position_source: int | None
    provider_time: int
    imported_at: str


class LatestStatesResponse(BaseModel):
    snapshot: SnapshotResponse | None
    data: list[AircraftStateResponse]


@asynccontextmanager
async def lifespan(application: FastAPI) -> AsyncIterator[None]:
    database_path = Path(os.getenv("DATABASE_PATH", str(DEFAULT_DATABASE_PATH)))
    initialize_database(database_path)
    application.state.database_path = database_path
    ssl_context = ssl.create_default_context()
    async with httpx.AsyncClient(timeout=20.0, verify=ssl_context) as http_client:
        application.state.http_client = http_client
        yield


app = FastAPI(
    title="Aircraft State API",
    description="A REST API for importing and querying saved aircraft state snapshots.",
    version="0.1.0",
    lifespan=lifespan,
)


async def get_database_connection(
    request: Request,
) -> AsyncIterator[sqlite3.Connection]:
    connection = connect(request.app.state.database_path)
    try:
        yield connection
    finally:
        connection.close()


def get_opensky_client(request: Request) -> OpenSkyClient | None:
    client_id = os.getenv("OPENSKY_CLIENT_ID")
    client_secret = os.getenv("OPENSKY_CLIENT_SECRET")
    if not client_id or not client_secret:
        return None
    return OpenSkyClient(client_id, client_secret, request.app.state.http_client)


def _state_response(row: sqlite3.Row) -> dict[str, object]:
    response = dict(row)
    response["on_ground"] = bool(response["on_ground"])
    return response


@app.get("/health", tags=["health"])
def health_check() -> dict[str, Literal["ok"]]:
    return {"status": "ok"}


@app.post(
    "/api/v1/state-imports",
    response_model=StateImportResponse,
    status_code=201,
    tags=["imports"],
)
async def import_states(
    request_body: StateImportRequest,
    connection: sqlite3.Connection = Depends(get_database_connection),
    opensky: OpenSkyClient | None = Depends(get_opensky_client),
) -> StateImportResponse:
    bounds = request_body.to_bounds()
    if opensky is None:
        raise HTTPException(
            status_code=503,
            detail="OpenSky client credentials are not configured",
        )
    try:
        snapshot = await opensky.fetch_states(bounds)
    except httpx.HTTPStatusError as error:
        raise HTTPException(
            status_code=502,
            detail=f"OpenSky returned HTTP {error.response.status_code}",
        ) from error
    except httpx.RequestError as error:
        logger.warning(
            "OpenSky request to %s failed (%s)",
            error.request.url.host,
            type(error).__name__,
        )
        raise HTTPException(
            status_code=502,
            detail="Unable to contact the OpenSky service",
        ) from error
    except OpenSkyResponseError as error:
        raise HTTPException(status_code=502, detail=str(error)) from error

    try:
        states: list[AircraftStateRecord] = [
            map_state_vector(state) for state in snapshot["states"]
        ]
    except ValueError as error:
        raise HTTPException(
            status_code=502,
            detail="OpenSky returned a malformed aircraft state vector",
        ) from error

    snapshot_id = save_snapshot(
        connection,
        snapshot["time"],
        (bounds.lamin, bounds.lomin, bounds.lamax, bounds.lomax),
        states,
    )
    return StateImportResponse(
        snapshot_id=snapshot_id,
        provider_time=snapshot["time"],
        imported_count=len(states),
    )


@app.get(
    "/api/v1/aircraft-states",
    response_model=LatestStatesResponse,
    tags=["aircraft states"],
)
async def read_latest_states(
    connection: sqlite3.Connection = Depends(get_database_connection),
) -> LatestStatesResponse:
    snapshot = get_latest_snapshot(connection)
    rows = list_latest_aircraft_states(connection)
    return LatestStatesResponse(
        snapshot=SnapshotResponse(**dict(snapshot)) if snapshot is not None else None,
        data=[AircraftStateResponse(**_state_response(row)) for row in rows],
    )


@app.get(
    "/api/v1/aircraft-states/{state_id}",
    response_model=AircraftStateResponse,
    tags=["aircraft states"],
)
async def read_aircraft_state(
    state_id: int,
    connection: sqlite3.Connection = Depends(get_database_connection),
) -> AircraftStateResponse:
    row = get_aircraft_state(connection, state_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Aircraft state was not found")
    return AircraftStateResponse(**_state_response(row))
