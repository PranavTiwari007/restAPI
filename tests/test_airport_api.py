from datetime import date, datetime, timezone
from math import cos, radians
from pathlib import Path

from fastapi.testclient import TestClient
import pytest

from app import database
from app import main
from app.airports import airport_bounds


def aircraft_record(icao24: str, callsign: str) -> dict[str, object]:
    return {
        "icao24": icao24,
        "callsign": callsign,
        "origin_country": "Exampleland",
        "time_position": 100,
        "last_contact": 101,
        "longitude": 72.8656,
        "latitude": 19.0896,
        "baro_altitude": 9000.0,
        "on_ground": False,
        "velocity": 220.5,
        "velocity_kmh": 793.8,
        "true_track": 180.0,
        "vertical_rate": -1.2,
        "geo_altitude": 9100.0,
        "squawk": "1234",
        "position_source": 0,
        "has_position": True,
    }


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setattr(database, "DB_FILE", tmp_path / "airzone.db")
    main.cache.clear()
    main.usage.update(day=date.today(), credits=0)
    with TestClient(main.app) as test_client:
        yield test_client


def test_airport_search_matches_airport_code_and_city(client: TestClient) -> None:
    by_code = client.get("/api/airports?q=maa")
    by_city = client.get("/api/airports?q=chennai")

    assert by_code.status_code == 200
    assert [airport["airport_id"] for airport in by_code.json()] == ["MAA"]
    assert [airport["airport_id"] for airport in by_city.json()] == ["MAA"]
    airport = by_city.json()[0]
    assert airport["lamax"] > airport["latitude"]
    assert airport["lomax"] > airport["longitude"]


def test_airport_catalog_includes_all_designated_indian_airports(
    client: TestClient,
) -> None:
    response = client.get("/api/airports?q=India")
    indian_airports = response.json()

    assert response.status_code == 200
    assert len(indian_airports) == 37
    assert {airport["airport_id"] for airport in indian_airports} >= {
        "AYJ",
        "BOM",
        "BLR",
        "CCU",
        "DEL",
        "GOI",
        "GOX",
        "HSR",
        "IXM",
        "MAA",
        "NMI",
        "SXR",
    }
    assert all(airport["country"] == "India" for airport in indian_airports)


def test_airport_bounds_approximate_a_22_km_square() -> None:
    latitude = 19.0896
    longitude = 72.8656

    lamin, lomin, lamax, lomax = airport_bounds(latitude, longitude)
    north_south_km = (lamax - lamin) * 111.32
    east_west_km = (lomax - lomin) * 111.32 * cos(radians(latitude))

    assert abs(north_south_km - 22) < 1e-6
    assert abs(east_west_km - 22) < 1e-6
    assert (lamin + lamax) / 2 == pytest.approx(latitude)
    assert (lomin + lomax) / 2 == pytest.approx(longitude)


def test_airport_import_persists_latest_states_and_daily_observations(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    provider_time = int(datetime.now(timezone.utc).timestamp())
    imports = [
        {
            "time": provider_time,
            "aircraft": [
                aircraft_record("abc123", "TEST123"),
                aircraft_record("def456", "TEST456"),
            ],
            "credits_remaining": 2500,
        },
        {
            "time": provider_time,
            "aircraft": [aircraft_record("abc123", "TEST123")],
            "credits_remaining": 2499,
        },
    ]

    def fake_fetch_states(*bounds: float) -> dict[str, object]:
        assert len(bounds) == 4
        return imports.pop(0)

    monkeypatch.setattr(main, "fetch_states", fake_fetch_states)

    first_import = client.post("/api/airports/MAA/imports")
    second_import = client.post("/api/airports/MAA/imports")

    assert first_import.status_code == 201
    assert first_import.json()["state_count"] == 2
    assert first_import.json()["observed_aircraft_count"] == 2
    assert second_import.status_code == 201
    assert second_import.json()["observed_aircraft_count"] == 1

    latest = client.get("/api/airports/MAA/aircraft").json()
    assert latest["snapshot"]["id"] == second_import.json()["import_id"]
    assert [record["icao24"] for record in latest["data"]] == ["abc123"]

    history = client.get("/api/airports/MAA/aircraft/abc123/history")
    assert history.status_code == 200
    assert len(history.json()["history"]) == 2

    daily = client.get("/api/airports/MAA/daily-observations?days=1").json()
    assert daily["metric"] == "distinct_aircraft_observed"
    assert daily["timezone"] == "UTC"
    assert daily["days"][0]["observed_aircraft_count"] == 2
    assert daily["days"][0]["sample_count"] == 2


def test_airport_import_rejects_unknown_airport(client: TestClient) -> None:
    response = client.post("/api/airports/ZZZ/imports")

    assert response.status_code == 404


def test_daily_observations_marks_unsampled_days_as_missing(client: TestClient) -> None:
    response = client.get("/api/airports/MAA/daily-observations?days=2")

    assert response.status_code == 200
    assert [day["observed_aircraft_count"] for day in response.json()["days"]] == [
        None,
        None,
    ]
    assert [day["sample_count"] for day in response.json()["days"]] == [0, 0]
