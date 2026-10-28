from typing import List, Optional

from pydantic import BaseModel


class Zone(BaseModel):
    zone_id: str
    name: str
    lamin: float
    lomin: float
    lamax: float
    lomax: float


class Aircraft(BaseModel):
    icao24: str
    callsign: Optional[str] = None
    origin_country: Optional[str] = None
    time_position: Optional[int] = None
    last_contact: Optional[int] = None
    longitude: Optional[float] = None
    latitude: Optional[float] = None
    baro_altitude: Optional[float] = None
    on_ground: Optional[bool] = None
    velocity: Optional[float] = None        
    velocity_kmh: Optional[float] = None    
    true_track: Optional[float] = None
    vertical_rate: Optional[float] = None
    sensors: Optional[List[int]] = None
    geo_altitude: Optional[float] = None
    squawk: Optional[str] = None
    spi: Optional[bool] = None
    position_source: Optional[int] = None
    has_position: bool


class ZoneAircraft(BaseModel):
    zone: Zone
    time: Optional[int] = None
    count: int
    with_position: int
    aircraft: List[Aircraft]
    cached: bool
    fetched_at: int
    saved: int
    credits_used_today: int
    credits_remaining: Optional[int] = None
