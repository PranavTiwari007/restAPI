from typing import List, Literal, Optional

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


class Airport(BaseModel):
    airport_id: str
    iata_code: str
    name: str
    city: str
    country: str
    airport_type: str
    latitude: float
    longitude: float
    lamin: float
    lomin: float
    lamax: float
    lomax: float


class AirportSnapshot(BaseModel):
    id: int
    provider_time: int
    imported_at: int
    state_count: int
    position_count: int
    lamin: float
    lomin: float
    lamax: float
    lomax: float


class AirportLatestAircraft(BaseModel):
    airport: Airport
    snapshot: AirportSnapshot | None
    data: List[Aircraft]


class AirportImportResponse(BaseModel):
    import_id: int
    airport: Airport
    provider_time: int
    imported_at: int
    state_count: int
    observed_aircraft_count: int
    credits_used_today: int
    credits_remaining: Optional[int] = None
    data: List[Aircraft]


class DailyObservationDay(BaseModel):
    day: str
    observed_aircraft_count: int | None
    sample_count: int


class DailyObservationsResponse(BaseModel):
    airport: Airport
    metric: Literal["distinct_aircraft_observed"]
    timezone: Literal["UTC"]
    days: List[DailyObservationDay]
