"""Curated international airport catalog and area geometry helpers."""

from math import cos, radians
from typing import TypedDict


class AirportRecord(TypedDict):
    airport_id: str
    iata_code: str
    name: str
    city: str
    country: str
    airport_type: str
    latitude: float
    longitude: float


AIRPORTS: tuple[AirportRecord, ...] = (
    {"airport_id": "TIR", "iata_code": "TIR", "name": "Tirupati Airport", "city": "Tirupati", "country": "India", "airport_type": "International", "latitude": 13.631988, "longitude": 79.539869},
    {"airport_id": "VGA", "iata_code": "VGA", "name": "Vijayawada Airport", "city": "Vijayawada", "country": "India", "airport_type": "International", "latitude": 16.530011, "longitude": 80.804888},
    {"airport_id": "VTZ", "iata_code": "VTZ", "name": "Alluri Sitarama Raju International Airport", "city": "Visakhapatnam", "country": "India", "airport_type": "International", "latitude": 17.971512, "longitude": 83.503617},
    {"airport_id": "GAU", "iata_code": "GAU", "name": "Lokpriya Gopinath Bordoloi International Airport", "city": "Guwahati", "country": "India", "airport_type": "International", "latitude": 26.106654, "longitude": 91.585226},
    {"airport_id": "GOI", "iata_code": "GOI", "name": "Dabolim Airport", "city": "Dabolim", "country": "India", "airport_type": "International (CE)", "latitude": 15.380062, "longitude": 73.833328},
    {"airport_id": "GOX", "iata_code": "GOX", "name": "Manohar International Airport", "city": "Mopa", "country": "India", "airport_type": "International", "latitude": 15.744257, "longitude": 73.860625},
    {"airport_id": "AMD", "iata_code": "AMD", "name": "Sardar Vallabhbhai Patel International Airport", "city": "Ahmedabad", "country": "India", "airport_type": "International", "latitude": 23.0772, "longitude": 72.634697},
    {"airport_id": "HSR", "iata_code": "HSR", "name": "Rajkot International Airport", "city": "Rajkot", "country": "India", "airport_type": "International", "latitude": 22.378824, "longitude": 71.039391},
    {"airport_id": "STV", "iata_code": "STV", "name": "Surat International Airport", "city": "Surat", "country": "India", "airport_type": "International", "latitude": 21.115531, "longitude": 72.743251},
    {"airport_id": "BLR", "iata_code": "BLR", "name": "Kempegowda International Airport", "city": "Bengaluru", "country": "India", "airport_type": "International", "latitude": 13.1979, "longitude": 77.706299},
    {"airport_id": "IXE", "iata_code": "IXE", "name": "Mangaluru International Airport", "city": "Mangaluru", "country": "India", "airport_type": "International", "latitude": 12.95471, "longitude": 74.886812},
    {"airport_id": "CNN", "iata_code": "CNN", "name": "Kannur International Airport", "city": "Kannur", "country": "India", "airport_type": "International", "latitude": 11.916343, "longitude": 75.544979},
    {"airport_id": "COK", "iata_code": "COK", "name": "Cochin International Airport", "city": "Kochi", "country": "India", "airport_type": "International", "latitude": 10.151047, "longitude": 76.400838},
    {"airport_id": "CCJ", "iata_code": "CCJ", "name": "Kozhikode International Airport", "city": "Kozhikode", "country": "India", "airport_type": "International", "latitude": 11.135996, "longitude": 75.955152},
    {"airport_id": "TRV", "iata_code": "TRV", "name": "Thiruvananthapuram International Airport", "city": "Thiruvananthapuram", "country": "India", "airport_type": "International", "latitude": 8.481889, "longitude": 76.920029},
    {"airport_id": "BOM", "iata_code": "BOM", "name": "Chhatrapati Shivaji Maharaj International Airport", "city": "Mumbai", "country": "India", "airport_type": "International", "latitude": 19.088699, "longitude": 72.867897},
    {"airport_id": "NAG", "iata_code": "NAG", "name": "Dr. Babasaheb Ambedkar International Airport", "city": "Nagpur", "country": "India", "airport_type": "International", "latitude": 21.092199, "longitude": 79.047203},
    {"airport_id": "NMI", "iata_code": "NMI", "name": "Navi Mumbai International Airport", "city": "Navi Mumbai", "country": "India", "airport_type": "International", "latitude": 18.984597, "longitude": 73.065253},
    {"airport_id": "SAG", "iata_code": "SAG", "name": "Shirdi Airport", "city": "Shirdi", "country": "India", "airport_type": "International", "latitude": 19.689211, "longitude": 74.373655},
    {"airport_id": "IMF", "iata_code": "IMF", "name": "Bir Tikendrajit International Airport", "city": "Imphal", "country": "India", "airport_type": "International", "latitude": 24.76, "longitude": 93.896698},
    {"airport_id": "BBI", "iata_code": "BBI", "name": "Biju Patnaik Airport", "city": "Bhubaneswar", "country": "India", "airport_type": "International", "latitude": 20.251021, "longitude": 85.814747},
    {"airport_id": "ATQ", "iata_code": "ATQ", "name": "Sri Guru Ram Dass Jee International Airport", "city": "Amritsar", "country": "India", "airport_type": "International", "latitude": 31.7096, "longitude": 74.797302},
    {"airport_id": "JAI", "iata_code": "JAI", "name": "Jaipur International Airport", "city": "Jaipur", "country": "India", "airport_type": "International", "latitude": 26.8242, "longitude": 75.812202},
    {"airport_id": "MAA", "iata_code": "MAA", "name": "Chennai International Airport", "city": "Chennai", "country": "India", "airport_type": "International", "latitude": 12.990005, "longitude": 80.169296},
    {"airport_id": "CJB", "iata_code": "CJB", "name": "Coimbatore International Airport", "city": "Coimbatore", "country": "India", "airport_type": "International", "latitude": 11.03, "longitude": 77.043404},
    {"airport_id": "IXM", "iata_code": "IXM", "name": "Madurai International Airport", "city": "Madurai", "country": "India", "airport_type": "International", "latitude": 9.83451, "longitude": 78.093399},
    {"airport_id": "TRZ", "iata_code": "TRZ", "name": "Tiruchirappalli International Airport", "city": "Tiruchirappalli", "country": "India", "airport_type": "International", "latitude": 10.762915, "longitude": 78.717741},
    {"airport_id": "HYD", "iata_code": "HYD", "name": "Rajiv Gandhi International Airport", "city": "Hyderabad", "country": "India", "airport_type": "International", "latitude": 17.231318, "longitude": 78.429855},
    {"airport_id": "AYJ", "iata_code": "AYJ", "name": "Maharishi Valmiki International Airport", "city": "Ayodhya", "country": "India", "airport_type": "International", "latitude": 26.747736, "longitude": 82.163664},
    {"airport_id": "KBK", "iata_code": "KBK", "name": "Kushinagar International Airport", "city": "Kushinagar", "country": "India", "airport_type": "International", "latitude": 26.776534, "longitude": 83.889214},
    {"airport_id": "LKO", "iata_code": "LKO", "name": "Chaudhary Charan Singh International Airport", "city": "Lucknow", "country": "India", "airport_type": "International", "latitude": 26.760599, "longitude": 80.889297},
    {"airport_id": "DXN", "iata_code": "DXN", "name": "Noida International Airport", "city": "Noida", "country": "India", "airport_type": "International", "latitude": 28.179868, "longitude": 77.611843},
    {"airport_id": "VNS", "iata_code": "VNS", "name": "Lal Bahadur Shastri Airport", "city": "Varanasi", "country": "India", "airport_type": "International", "latitude": 25.452171, "longitude": 82.862549},
    {"airport_id": "CCU", "iata_code": "CCU", "name": "Netaji Subhas Chandra Bose International Airport", "city": "Kolkata", "country": "India", "airport_type": "International", "latitude": 22.654012, "longitude": 88.44765},
    {"airport_id": "IXZ", "iata_code": "IXZ", "name": "Veer Savarkar International Airport", "city": "Port Blair", "country": "India", "airport_type": "International (CE)", "latitude": 11.640194, "longitude": 92.72902},
    {"airport_id": "DEL", "iata_code": "DEL", "name": "Indira Gandhi International Airport", "city": "Delhi", "country": "India", "airport_type": "International", "latitude": 28.55563, "longitude": 77.09519},
    {"airport_id": "SXR", "iata_code": "SXR", "name": "Srinagar International Airport", "city": "Srinagar", "country": "India", "airport_type": "International", "latitude": 33.987099, "longitude": 74.7742},
    {"airport_id": "LHR", "iata_code": "LHR", "name": "Heathrow Airport", "city": "London", "country": "United Kingdom", "airport_type": "International", "latitude": 51.4700, "longitude": -0.4543},
    {"airport_id": "CDG", "iata_code": "CDG", "name": "Charles de Gaulle Airport", "city": "Paris", "country": "France", "airport_type": "International", "latitude": 49.0097, "longitude": 2.5479},
    {"airport_id": "FRA", "iata_code": "FRA", "name": "Frankfurt Airport", "city": "Frankfurt", "country": "Germany", "airport_type": "International", "latitude": 50.0379, "longitude": 8.5622},
    {"airport_id": "JFK", "iata_code": "JFK", "name": "John F. Kennedy International Airport", "city": "New York", "country": "United States", "airport_type": "International", "latitude": 40.6413, "longitude": -73.7781},
    {"airport_id": "SFO", "iata_code": "SFO", "name": "San Francisco International Airport", "city": "San Francisco", "country": "United States", "airport_type": "International", "latitude": 37.6213, "longitude": -122.3790},
    {"airport_id": "LAX", "iata_code": "LAX", "name": "Los Angeles International Airport", "city": "Los Angeles", "country": "United States", "airport_type": "International", "latitude": 33.9416, "longitude": -118.4085},
    {"airport_id": "DXB", "iata_code": "DXB", "name": "Dubai International Airport", "city": "Dubai", "country": "United Arab Emirates", "airport_type": "International", "latitude": 25.2532, "longitude": 55.3657},
    {"airport_id": "DOH", "iata_code": "DOH", "name": "Hamad International Airport", "city": "Doha", "country": "Qatar", "airport_type": "International", "latitude": 25.2731, "longitude": 51.6081},
    {"airport_id": "SIN", "iata_code": "SIN", "name": "Singapore Changi Airport", "city": "Singapore", "country": "Singapore", "airport_type": "International", "latitude": 1.3644, "longitude": 103.9915},
    {"airport_id": "HND", "iata_code": "HND", "name": "Tokyo Haneda Airport", "city": "Tokyo", "country": "Japan", "airport_type": "International", "latitude": 35.5494, "longitude": 139.7798},
    {"airport_id": "SYD", "iata_code": "SYD", "name": "Sydney Kingsford Smith Airport", "city": "Sydney", "country": "Australia", "airport_type": "International", "latitude": -33.9399, "longitude": 151.1753},
)


def find_airport(airport_id: str) -> AirportRecord | None:
    normalized_id = airport_id.upper()
    return next(
        (airport for airport in AIRPORTS if airport["airport_id"] == normalized_id),
        None,
    )


def search_airports(query: str | None = None) -> list[AirportRecord]:
    if not query:
        return list(AIRPORTS)

    normalized_query = query.strip().casefold()
    return [
        airport
        for airport in AIRPORTS
        if normalized_query
        in " ".join(
            str(airport[field])
            for field in ("iata_code", "name", "city", "country")
        ).casefold()
    ]


def airport_bounds(
    latitude: float,
    longitude: float,
    side_length_km: float = 22,
) -> tuple[float, float, float, float]:
    half_side_km = side_length_km / 2
    latitude_delta = half_side_km / 111.32
    longitude_scale = cos(radians(latitude))
    if longitude_scale <= 0.01:
        raise ValueError("Airport is too close to the poles for a square area")
    longitude_delta = half_side_km / (111.32 * longitude_scale)
    return (
        latitude - latitude_delta,
        max(-180.0, longitude - longitude_delta),
        latitude + latitude_delta,
        min(180.0, longitude + longitude_delta),
    )
