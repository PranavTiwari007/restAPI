import pytest

from app.state_mapping import map_state_vector


def test_maps_selected_fields_from_opensky_vector() -> None:
    state = [
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
        2,
    ]

    mapped = map_state_vector(state)

    assert mapped == {
        "icao24": "abc123",
        "callsign": "TEST123",
        "origin_country": "Exampleland",
        "last_contact": 101,
        "longitude": 12.5,
        "latitude": 45.6,
        "baro_altitude": 9000.0,
        "on_ground": False,
        "velocity": 220.5,
        "true_track": 180.0,
        "vertical_rate": -1.2,
        "geo_altitude": 9100.0,
        "squawk": "1234",
        "position_source": 0,
    }


def test_preserves_nullable_values_and_ignores_extended_category() -> None:
    state = [
        "abc123",
        None,
        "Exampleland",
        None,
        101,
        None,
        None,
        None,
        True,
        None,
        None,
        None,
        None,
        None,
        None,
        False,
        None,
        2,
    ]

    mapped = map_state_vector(state)

    assert mapped["callsign"] is None
    assert mapped["longitude"] is None
    assert mapped["latitude"] is None
    assert mapped["baro_altitude"] is None
    assert mapped["on_ground"] is True
    assert mapped["position_source"] is None
    assert "category" not in mapped


@pytest.mark.parametrize(
    ("state", "message"),
    [
        (["abc123"], "at least 17 fields"),
        (
            ["invalid", None, "Exampleland", 0, 1, None, None, None, False]
            + [None] * 8,
            "6-character hex address",
        ),
        (
            ["abc123", None, "Exampleland", 0, "101", None, None, None, False]
            + [None] * 8,
            "last_contact must be an integer",
        ),
        (
            ["abc123", None, "Exampleland", 0, 101, None, None, None, 0]
            + [None] * 8,
            "on_ground must be a boolean",
        ),
    ],
)
def test_rejects_invalid_vectors(state: list[object], message: str) -> None:
    with pytest.raises(ValueError, match=message):
        map_state_vector(state)
