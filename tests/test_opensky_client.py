import httpx
import pytest

from app import opensky_client
from app.opensky_client import OpenSkyError


def test_normalizes_opensky_state_fields() -> None:
    record = opensky_client.normalize(
        [
            "ABC123",
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
            [1, 2],
            9100.0,
            "1234",
            False,
            0,
        ]
    )

    assert record["icao24"] == "ABC123"
    assert record["callsign"] == "TEST123"
    assert record["latitude"] == 45.6
    assert record["longitude"] == 12.5
    assert record["velocity_kmh"] == 793.8
    assert record["has_position"] is True


def test_fetches_states_with_access_token_and_bounding_box(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(opensky_client.tokens, "get", lambda force=False: "test-token")
    requests: list[dict[str, object]] = []

    def fake_get(url: str, *, params: dict[str, float], headers: dict[str, str]):
        requests.append({"url": url, "params": params, "headers": headers})
        return httpx.Response(
            200,
            json={
                "time": 123,
                "states": [
                    [
                        "abc123",
                        "TEST123",
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
                ],
            },
            headers={"X-Rate-Limit-Remaining": "250"},
        )

    monkeypatch.setattr(opensky_client.http, "get", fake_get)

    result = opensky_client.fetch_states(45, 5, 47, 8)

    assert result["time"] == 123
    assert result["aircraft"][0]["icao24"] == "abc123"
    assert result["credits_remaining"] == 250
    assert requests == [
        {
            "url": opensky_client.API_URL,
            "params": {"lamin": 45, "lomin": 5, "lamax": 47, "lomax": 8},
            "headers": {"Authorization": "Bearer test-token"},
        }
    ]


def test_open_sky_rate_limit_error_is_preserved(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(opensky_client.tokens, "get", lambda force=False: "test-token")

    def fake_get(*args, **kwargs):
        return httpx.Response(
            429,
            headers={"X-Rate-Limit-Retry-After-Seconds": "30"},
        )

    monkeypatch.setattr(opensky_client.http, "get", fake_get)

    with pytest.raises(OpenSkyError, match="Retry in 30s") as error:
        opensky_client.fetch_states(45, 5, 47, 8)

    assert error.value.status == 429
