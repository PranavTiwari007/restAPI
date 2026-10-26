import asyncio
from urllib.parse import parse_qs

import httpx
import pytest

from app.opensky_client import (
    BoundingBox,
    OpenSkyClient,
    OpenSkyResponseError,
    STATES_URL,
    TOKEN_URL,
)


def test_fetches_bounded_states_with_oauth_bearer_token() -> None:
    requests: list[httpx.Request] = []

    def respond(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if request.url == httpx.URL(TOKEN_URL):
            form = parse_qs(request.content.decode())
            assert form["grant_type"] == ["client_credentials"]
            assert form["client_id"] == ["test-client"]
            assert form["client_secret"] == ["test-secret"]
            return httpx.Response(200, json={"access_token": "test-token"})

        assert request.url == httpx.URL(STATES_URL).copy_merge_params(
            {"lamin": 45, "lomin": 5, "lamax": 47, "lomax": 8}
        )
        assert request.headers["Authorization"] == "Bearer test-token"
        return httpx.Response(200, json={"time": 123, "states": [["abc123"]]})

    async def run() -> dict[str, object]:
        async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as http:
            client = OpenSkyClient("test-client", "test-secret", http)
            return await client.fetch_states(BoundingBox(45, 5, 47, 8))

    result = asyncio.run(run())

    assert result == {"time": 123, "states": [["abc123"]]}
    assert len(requests) == 2


def test_treats_null_states_as_empty_snapshot() -> None:
    def respond(request: httpx.Request) -> httpx.Response:
        if request.url == httpx.URL(TOKEN_URL):
            return httpx.Response(200, json={"access_token": "test-token"})
        return httpx.Response(200, json={"time": 123, "states": None})

    async def run() -> dict[str, object]:
        async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as http:
            client = OpenSkyClient("test-client", "test-secret", http)
            return await client.fetch_states(BoundingBox(45, 5, 47, 8))

    assert asyncio.run(run()) == {"time": 123, "states": []}


@pytest.mark.parametrize(
    ("bounds", "message"),
    [
        ((91, 5, 92, 8), "Latitude bounds"),
        ((45, 8, 47, 5), "Longitude bounds"),
        ((45, 5, 47, float("inf")), "must be finite"),
    ],
)
def test_rejects_invalid_bounding_boxes(
    bounds: tuple[float, float, float, float],
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        BoundingBox(*bounds)


def test_rejects_invalid_token_response() -> None:
    def respond(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"token_type": "Bearer"})

    async def run() -> None:
        async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as http:
            client = OpenSkyClient("test-client", "test-secret", http)
            await client.fetch_states(BoundingBox(45, 5, 47, 8))

    with pytest.raises(OpenSkyResponseError, match="did not contain an access token"):
        asyncio.run(run())
