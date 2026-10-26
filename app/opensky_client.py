from dataclasses import dataclass
import math
from typing import TypedDict

import httpx


TOKEN_URL = (
    "https://auth.opensky-network.org/auth/realms/opensky-network"
    "/protocol/openid-connect/token"
)
STATES_URL = "https://opensky-network.org/api/states/all"


class StateVectorSnapshot(TypedDict):
    time: int
    states: list[list[object]]


class OpenSkyResponseError(ValueError):
    """Raised when OpenSky returns a response that does not match its API shape."""


@dataclass(frozen=True)
class BoundingBox:
    lamin: float
    lomin: float
    lamax: float
    lomax: float

    def __post_init__(self) -> None:
        coordinates = {
            "lamin": self.lamin,
            "lomin": self.lomin,
            "lamax": self.lamax,
            "lomax": self.lomax,
        }
        for name, value in coordinates.items():
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise ValueError(f"{name} must be a number")
            if not math.isfinite(value):
                raise ValueError(f"{name} must be finite")

        if not -90 <= self.lamin < self.lamax <= 90:
            raise ValueError("Latitude bounds must be ordered and within -90 to 90")
        if not -180 <= self.lomin < self.lomax <= 180:
            raise ValueError("Longitude bounds must be ordered and within -180 to 180")


def _response_json(response: httpx.Response, context: str) -> object:
    try:
        return response.json()
    except ValueError as error:
        raise OpenSkyResponseError(f"OpenSky returned invalid JSON for {context}") from error


class OpenSkyClient:
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        http_client: httpx.AsyncClient,
    ) -> None:
        if not client_id.strip() or not client_secret.strip():
            raise ValueError("OpenSky client ID and client secret are required")
        self._client_id = client_id
        self._client_secret = client_secret
        self._http_client = http_client

    async def fetch_states(self, bounds: BoundingBox) -> StateVectorSnapshot:
        token_response = await self._http_client.post(
            TOKEN_URL,
            data={
                "grant_type": "client_credentials",
                "client_id": self._client_id,
                "client_secret": self._client_secret,
            },
        )
        token_response.raise_for_status()
        token_data = _response_json(token_response, "OAuth token")
        if not isinstance(token_data, dict):
            raise OpenSkyResponseError("OpenSky returned an invalid OAuth token response")
        access_token = token_data.get("access_token")
        if not isinstance(access_token, str) or not access_token:
            raise OpenSkyResponseError("OpenSky OAuth response did not contain an access token")

        states_response = await self._http_client.get(
            STATES_URL,
            params={
                "lamin": bounds.lamin,
                "lomin": bounds.lomin,
                "lamax": bounds.lamax,
                "lomax": bounds.lomax,
            },
            headers={"Authorization": f"Bearer {access_token}"},
        )
        states_response.raise_for_status()
        payload = _response_json(states_response, "state vectors")
        if not isinstance(payload, dict):
            raise OpenSkyResponseError("OpenSky returned an invalid state-vector response")

        provider_time = payload.get("time")
        if isinstance(provider_time, bool) or not isinstance(provider_time, int):
            raise OpenSkyResponseError("OpenSky state-vector response is missing a valid time")

        states = payload.get("states")
        if states is None:
            states = []
        if not isinstance(states, list) or any(not isinstance(state, list) for state in states):
            raise OpenSkyResponseError("OpenSky state-vector response contains invalid states")

        return {"time": provider_time, "states": states}
