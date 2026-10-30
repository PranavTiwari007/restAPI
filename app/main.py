import os
import time
from contextlib import asynccontextmanager
from datetime import date, datetime, timedelta, timezone
from typing import List

from fastapi import FastAPI, HTTPException, Path, Query
from fastapi.middleware.cors import CORSMiddleware

from app import database as db
from app.airports import (
    AirportRecord,
    airport_bounds,
    find_airport,
    search_airports,
)
from app.models import (
    Airport,
    AirportImportResponse,
    AirportLatestAircraft,
    AirportSnapshot,
    DailyObservationsResponse,
    Zone,
    ZoneAircraft,
)
from app.opensky_client import OpenSkyError, fetch_states

CACHE_SECONDS = 60                                        
DAILY_LIMIT = int(os.getenv("DAILY_CREDIT_LIMIT", "3000"))
cache = {}                                               
usage = {"day": date.today(), "credits": 0}


@asynccontextmanager
async def lifespan(app):
    db.init_db()  
    yield


app = FastAPI(title="Airzone", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
                   allow_methods=["GET"], allow_headers=["*"])


def credit_cost(z):
    """Estimated OpenSky cost by bounding-box area (square degrees)."""
    area = (z["lamax"] - z["lamin"]) * (z["lomax"] - z["lomin"])
    return 1 if area <= 25 else 2 if area <= 100 else 3 if area <= 400 else 4


def credits_today():
    if usage["day"] != date.today():
        usage.update(day=date.today(), credits=0)
    return usage["credits"]


def airport_response(airport_record: AirportRecord) -> Airport:
    bounds = airport_bounds(airport_record["latitude"], airport_record["longitude"])
    return Airport(
        **airport_record,
        lamin=bounds[0],
        lomin=bounds[1],
        lamax=bounds[2],
        lomax=bounds[3],
    )


@app.get("/api/health")
def health():
    return {"status": "ok", "credits_used_today": credits_today(), "daily_limit": DAILY_LIMIT}


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/api/zones", response_model=List[Zone])
def zones():
    return db.list_zones()


@app.get("/api/airports", response_model=List[Airport])
def airports(q: str | None = Query(default=None, max_length=100)) -> List[Airport]:
    return [airport_response(airport) for airport in search_airports(q)]


def get_airport_or_404(airport_id: str) -> AirportRecord:
    airport_record = find_airport(airport_id)
    if airport_record is None:
        raise HTTPException(404, "Airport not found in the curated airport catalog.")
    return airport_record


@app.post(
    "/api/airports/{airport_id}/imports",
    response_model=AirportImportResponse,
    status_code=201,
)
def import_airport_observations(
    airport_id: str = Path(pattern=r"^[A-Za-z]{3}$"),
) -> AirportImportResponse:
    airport_record = get_airport_or_404(airport_id)
    airport = airport_response(airport_record)
    bounds = (airport.lamin, airport.lomin, airport.lamax, airport.lomax)
    cost = credit_cost(
        {
            "lamin": airport.lamin,
            "lomin": airport.lomin,
            "lamax": airport.lamax,
            "lomax": airport.lomax,
        }
    )
    if credits_today() + cost > DAILY_LIMIT:
        raise HTTPException(
            429,
            "Local daily credit limit reached. Try again tomorrow or raise DAILY_CREDIT_LIMIT.",
        )
    try:
        result = fetch_states(*bounds)
    except OpenSkyError as error:
        raise HTTPException(error.status, error.message) from error

    provider_time = result["time"]
    if isinstance(provider_time, bool) or not isinstance(provider_time, int):
        raise HTTPException(502, "OpenSky returned an invalid state timestamp")

    now = int(time.time())
    aircraft = result["aircraft"]
    import_id = db.save_airport_import(
        airport.airport_id,
        provider_time,
        now,
        bounds,
        aircraft,
    )
    usage["credits"] += cost
    return AirportImportResponse(
        import_id=import_id,
        airport=airport,
        provider_time=provider_time,
        imported_at=now,
        state_count=len(aircraft),
        observed_aircraft_count=sum(record["has_position"] for record in aircraft),
        credits_used_today=usage["credits"],
        credits_remaining=result["credits_remaining"],
        data=[record for record in aircraft if record["has_position"]],
    )


@app.get(
    "/api/airports/{airport_id}/aircraft",
    response_model=AirportLatestAircraft,
)
def latest_airport_aircraft(
    airport_id: str = Path(pattern=r"^[A-Za-z]{3}$"),
) -> AirportLatestAircraft:
    airport = airport_response(get_airport_or_404(airport_id))
    latest = db.get_latest_airport_import(airport.airport_id)
    snapshot = None
    aircraft = []
    if latest is not None:
        snapshot = AirportSnapshot(
            id=latest["id"],
            provider_time=latest["provider_time"],
            imported_at=latest["imported_at"],
            state_count=latest["state_count"],
            position_count=latest["position_count"],
            lamin=latest["lamin"],
            lomin=latest["lomin"],
            lamax=latest["lamax"],
            lomax=latest["lomax"],
        )
        aircraft = latest["aircraft"]
    return AirportLatestAircraft(airport=airport, snapshot=snapshot, data=aircraft)


@app.get("/api/airports/{airport_id}/aircraft/{icao24}/history")
def airport_aircraft_history(
    airport_id: str = Path(pattern=r"^[A-Za-z]{3}$"),
    icao24: str = Path(pattern=r"^[0-9a-fA-F]{6}$"),
) -> dict[str, object]:
    airport_record = get_airport_or_404(airport_id)
    history = db.get_airport_aircraft_history(
        airport_record["airport_id"],
        icao24.lower(),
    )
    if not history:
        raise HTTPException(404, "No saved observations for this aircraft at this airport.")
    return {
        "airport_id": airport_record["airport_id"],
        "icao24": icao24.lower(),
        "history": history,
    }


@app.get(
    "/api/airports/{airport_id}/daily-observations",
    response_model=DailyObservationsResponse,
)
def daily_airport_observations(
    airport_id: str = Path(pattern=r"^[A-Za-z]{3}$"),
    days: int = Query(default=7, ge=1, le=90),
) -> DailyObservationsResponse:
    airport = airport_response(get_airport_or_404(airport_id))
    end_date = datetime.now(timezone.utc).date()
    start_date = end_date - timedelta(days=days - 1)
    counts = {
        row["day"]: row
        for row in db.get_daily_airport_counts(
            airport.airport_id,
            start_date.isoformat(),
            end_date.isoformat(),
        )
    }
    day_rows = []
    for offset in range(days):
        day = start_date + timedelta(days=offset)
        row = counts.get(day.isoformat())
        day_rows.append(
            {
                "day": day.isoformat(),
                "observed_aircraft_count": (
                    row["observed_aircraft_count"] if row is not None else None
                ),
                "sample_count": row["sample_count"] if row is not None else 0,
            }
        )
    return DailyObservationsResponse(
        airport=airport,
        metric="distinct_aircraft_observed",
        timezone="UTC",
        days=day_rows,
    )


@app.get("/api/zones/{zone_id}", response_model=Zone)
def zone(zone_id: str = Path(pattern=r"^[A-Za-z0-9-]{1,30}$")):
    found = db.get_zone(zone_id)
    if not found:
        raise HTTPException(404, "Zone not found.")
    return found


@app.get("/api/zones/{zone_id}/aircraft", response_model=ZoneAircraft)
def zone_aircraft(zone_id: str = Path(pattern=r"^[A-Za-z0-9-]{1,30}$")):
    z = db.get_zone(zone_id)
    if not z:
        raise HTTPException(404, "Zone not found.")

    hit = cache.get(zone_id)
    if hit and time.time() - hit["fetched_at"] < CACHE_SECONDS:
        return {**hit, "cached": True, "credits_used_today": credits_today()}

    cost = credit_cost(z)
    if credits_today() + cost > DAILY_LIMIT:
        raise HTTPException(429, "Local daily credit limit reached. Try again tomorrow or raise DAILY_CREDIT_LIMIT.")
    try:
        result = fetch_states(z["lamin"], z["lomin"], z["lamax"], z["lomax"])
    except OpenSkyError as e:
        raise HTTPException(e.status, e.message)

    usage["credits"] += cost
    now = int(time.time())
    saved = db.save_observations(result["aircraft"], now)
    payload = {"zone": z, "time": result["time"], "count": len(result["aircraft"]),
               "with_position": sum(a["has_position"] for a in result["aircraft"]),
               "aircraft": result["aircraft"], "fetched_at": now, "saved": saved,
               "credits_remaining": result["credits_remaining"]}
    cache[zone_id] = payload
    return {**payload, "cached": False, "credits_used_today": usage["credits"]}


@app.get("/api/aircraft/{icao24}")
def aircraft(icao24: str = Path(pattern=r"^[0-9a-fA-F]{6}$")):
    history = db.aircraft_history(icao24.lower())
    if not history:
        raise HTTPException(404, "No saved observations for this aircraft yet.")
    return {"icao24": icao24.lower(), "latest": history[0], "history": history}


@app.get("/", tags=["health"])
def root() -> dict[str, str]:
    return {
        "message": "Aircraft State API",
        "docs": "/docs",
        "health": "/health",
    }
