from datetime import date
from pathlib import Path

from fastapi.testclient import TestClient
import pytest

from app import database
from app import main


def state(icao24: str = "abc123") -> dict[str, object]:
    return {
        "icao24": icao24,
        "callsign": "TEST123",
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


def test_lists_seeded_zones(client: TestClient) -> None:
    response = client.get("/api/zones")

    assert response.status_code == 200
    assert {zone["zone_id"] for zone in response.json()} >= {"mumbai", "chennai"}


def test_resolves_map_grid_zone(client: TestClient) -> None:
    response = client.get("/api/zones/R44C63")

    assert response.status_code == 200
    assert response.json()["zone_id"] == "R44C63"
    assert response.json()["lamin"] == 86
    assert response.json()["lomin"] == 72


def test_zone_fetch_saves_observations_and_caches_repeat(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = 0

    def fake_fetch_states(*bounds: float) -> dict[str, object]:
        nonlocal calls
        calls += 1
        assert len(bounds) == 4
        return {
            "time": 123,
            "aircraft": [state()],
            "credits_remaining": 2500,
        }

    monkeypatch.setattr(main, "fetch_states", fake_fetch_states)

    first = client.get("/api/zones/mumbai/aircraft")
    second = client.get("/api/zones/mumbai/aircraft")

    assert first.status_code == 200
    assert first.json()["count"] == 1
    assert first.json()["saved"] == 1
    assert second.json()["cached"] is True
    assert calls == 1

    history = client.get("/api/aircraft/abc123")
    assert history.status_code == 200
    assert history.json()["latest"]["callsign"] == "TEST123"


def test_unknown_zone_returns_404(client: TestClient) -> None:
    response = client.get("/api/zones/not-a-zone")

    assert response.status_code == 404


def test_unknown_aircraft_returns_404(client: TestClient) -> None:
    response = client.get("/api/aircraft/abc123")

    assert response.status_code == 404
