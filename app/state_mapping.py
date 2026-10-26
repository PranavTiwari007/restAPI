import math
import re
from collections.abc import Sequence
from typing import TypedDict


class AircraftStateRecord(TypedDict):
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


def _required_text(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"State vector field {field} must be a non-empty string")
    return value.strip()


def _optional_text(value: object, field: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(f"State vector field {field} must be a string or null")
    return value.strip() or None


def _optional_number(value: object, field: str) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"State vector field {field} must be a number or null")
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"State vector field {field} must be finite")
    return number


def _optional_integer(value: object, field: str) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"State vector field {field} must be an integer or null")
    return value


def _required_integer(value: object, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"State vector field {field} must be an integer")
    return value


def map_state_vector(state: Sequence[object]) -> AircraftStateRecord:
    if isinstance(state, (str, bytes)) or len(state) < 17:
        raise ValueError("State vector must contain at least 17 fields")

    icao24 = _required_text(state[0], "icao24").lower()
    if re.fullmatch(r"[0-9a-f]{6}", icao24) is None:
        raise ValueError("State vector field icao24 must be a 6-character hex address")

    on_ground = state[8]
    if not isinstance(on_ground, bool):
        raise ValueError("State vector field on_ground must be a boolean")

    return {
        "icao24": icao24,
        "callsign": _optional_text(state[1], "callsign"),
        "origin_country": _required_text(state[2], "origin_country"),
        "last_contact": _required_integer(state[4], "last_contact"),
        "longitude": _optional_number(state[5], "longitude"),
        "latitude": _optional_number(state[6], "latitude"),
        "baro_altitude": _optional_number(state[7], "baro_altitude"),
        "on_ground": on_ground,
        "velocity": _optional_number(state[9], "velocity"),
        "true_track": _optional_number(state[10], "true_track"),
        "vertical_rate": _optional_number(state[11], "vertical_rate"),
        "geo_altitude": _optional_number(state[13], "geo_altitude"),
        "squawk": _optional_text(state[14], "squawk"),
        "position_source": _optional_integer(state[16], "position_source"),
    }
