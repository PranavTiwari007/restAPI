from pathlib import Path

import pytest

from app import database


def observation(
    icao24: str = "abc123",
    last_contact: int = 100,
) -> dict[str, object]:
    return {
        "icao24": icao24,
        "callsign": "TEST123",
        "origin_country": "Exampleland",
        "latitude": 19.0,
        "longitude": 72.0,
        "baro_altitude": 9000.0,
        "velocity": 220.5,
        "true_track": 180.0,
        "on_ground": False,
        "last_contact": last_contact,
        "has_position": True,
    }


@pytest.fixture
def initialized_database(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> Path:
    path = tmp_path / "airzone.db"
    monkeypatch.setattr(database, "DB_FILE", path)
    database.init_db()
    return path


def test_init_db_is_repeatable_and_seeds_default_zones(
    initialized_database: Path,
) -> None:
    database.init_db()

    zones = database.list_zones()

    assert {zone["zone_id"] for zone in zones} >= {"mumbai", "chennai"}


def test_cell_zone_calculates_map_bounds(
    initialized_database: Path,
) -> None:
    zone = database.get_zone("R44C63")

    assert zone is not None
    assert (zone["lamin"], zone["lomin"], zone["lamax"], zone["lomax"]) == (
        86,
        72,
        90,
        76,
    )
    assert database.get_zone("R45C63") is None


def test_observation_storage_deduplicates_unchanged_contact(
    initialized_database: Path,
) -> None:
    first_saved = database.save_observations([observation()], observed_at=1000)
    repeated_saved = database.save_observations([observation()], observed_at=1010)
    changed_saved = database.save_observations(
        [observation(last_contact=101)],
        observed_at=1020,
    )

    history = database.aircraft_history("abc123")

    assert (first_saved, repeated_saved, changed_saved) == (1, 0, 1)
    assert len(history) == 2
    assert history[0]["last_contact"] == 101
