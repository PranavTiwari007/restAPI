from pathlib import Path

from fastapi.testclient import TestClient
import httpx
import pytest

from app.main import app, get_opensky_client
from app.opensky_client import BoundingBox


def state_vector(icao24: str = "abc123") -> list[object]:
    return [
        icao24,
        " TEST123 ",
        "Exampleland",
        100,
        101,
        12.5,
        45.6,
        9000.0,
        False,
        220.5,
        180.0,
        -1.2,
        None,
        9100.0,
        "1234",
        False,
        0,
    ]


class FakeOpenSkyClient:
    def __init__(self, states: list[list[object]]) -> None:
        self.states = states
        self.bounds: BoundingBox | None = None

    async def fetch_states(self, bounds: BoundingBox) -> dict[str, object]:
        self.bounds = bounds
        return {"time": 123, "states": self.states}


class FailingOpenSkyClient:
    async def fetch_states(self, bounds: BoundingBox) -> dict[str, object]:
        raise httpx.ConnectError(
            "mock connection failure",
            request=httpx.Request("GET", "https://opensky-network.org/api/states/all"),
        )


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "aircraft.db"))
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.pop(get_opensky_client, None)


def test_imports_snapshot_and_reads_latest_aircraft_states(
    client: TestClient,
) -> None:
    fake_opensky = FakeOpenSkyClient([state_vector()])
    app.dependency_overrides[get_opensky_client] = lambda: fake_opensky

    imported = client.post(
        "/api/v1/state-imports",
        json={"lamin": 45, "lomin": 5, "lamax": 47, "lomax": 8},
    )

    assert imported.status_code == 201
    assert imported.json()["provider_time"] == 123
    assert imported.json()["imported_count"] == 1
    assert fake_opensky.bounds == BoundingBox(45, 5, 47, 8)

    latest = client.get("/api/v1/aircraft-states")

    assert latest.status_code == 200
    assert latest.json()["snapshot"]["state_count"] == 1
    assert latest.json()["data"][0]["icao24"] == "abc123"
    assert latest.json()["data"][0]["callsign"] == "TEST123"
    assert latest.json()["data"][0]["on_ground"] is False

    state_id = latest.json()["data"][0]["id"]
    detail = client.get(f"/api/v1/aircraft-states/{state_id}")
    assert detail.status_code == 200
    assert detail.json()["provider_time"] == 123


def test_malformed_vector_rolls_back_entire_snapshot(client: TestClient) -> None:
    fake_opensky = FakeOpenSkyClient([state_vector(), ["not", "a", "complete", "vector"]])
    app.dependency_overrides[get_opensky_client] = lambda: fake_opensky

    imported = client.post(
        "/api/v1/state-imports",
        json={"lamin": 45, "lomin": 5, "lamax": 47, "lomax": 8},
    )

    assert imported.status_code == 502
    assert imported.json()["detail"] == "OpenSky returned a malformed aircraft state vector"
    assert client.get("/api/v1/aircraft-states").json() == {
        "snapshot": None,
        "data": [],
    }


def test_import_rejects_reversed_bounds(client: TestClient) -> None:
    imported = client.post(
        "/api/v1/state-imports",
        json={"lamin": 47, "lomin": 5, "lamax": 45, "lomax": 8},
    )

    assert imported.status_code == 422


def test_import_reports_missing_opensky_credentials(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("OPENSKY_CLIENT_ID", raising=False)
    monkeypatch.delenv("OPENSKY_CLIENT_SECRET", raising=False)

    imported = client.post(
        "/api/v1/state-imports",
        json={"lamin": 45, "lomin": 5, "lamax": 47, "lomax": 8},
    )

    assert imported.status_code == 503
    assert imported.json()["detail"] == "OpenSky client credentials are not configured"


def test_import_reports_network_failure_without_logging_secrets(
    client: TestClient,
    caplog: pytest.LogCaptureFixture,
) -> None:
    app.dependency_overrides[get_opensky_client] = lambda: FailingOpenSkyClient()

    imported = client.post(
        "/api/v1/state-imports",
        json={"lamin": 45, "lomin": 5, "lamax": 47, "lomax": 8},
    )

    assert imported.status_code == 502
    assert imported.json()["detail"] == "Unable to contact the OpenSky service"
    assert "ConnectError" in caplog.text
    assert "test-secret" not in caplog.text


def test_unknown_aircraft_state_returns_404(client: TestClient) -> None:
    response = client.get("/api/v1/aircraft-states/999")

    assert response.status_code == 404
