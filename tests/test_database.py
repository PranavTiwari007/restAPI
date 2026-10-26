from pathlib import Path

from app.database import connect, initialize_database, list_latest_aircraft_states


def test_latest_state_query_returns_only_newest_snapshot(tmp_path: Path) -> None:
    database_path = tmp_path / "aircraft.db"
    initialize_database(database_path)

    with connect(database_path) as connection:
        older_snapshot = connection.execute(
            """
            INSERT INTO snapshots (provider_time, lamin, lomin, lamax, lomax)
            VALUES (100, 45, 5, 47, 8)
            """
        ).lastrowid
        connection.execute(
            """
            INSERT INTO aircraft_states
                (snapshot_id, icao24, origin_country, last_contact, on_ground)
            VALUES (?, 'abc123', 'Exampleland', 100, 0)
            """,
            (older_snapshot,),
        )

        latest_snapshot = connection.execute(
            """
            INSERT INTO snapshots (provider_time, lamin, lomin, lamax, lomax)
            VALUES (200, 45, 5, 47, 8)
            """
        ).lastrowid
        connection.execute(
            """
            INSERT INTO aircraft_states
                (snapshot_id, icao24, origin_country, last_contact, on_ground)
            VALUES (?, 'def456', 'Exampleland', 200, 0)
            """,
            (latest_snapshot,),
        )

        latest_states = list_latest_aircraft_states(connection)

    assert [state["icao24"] for state in latest_states] == ["def456"]
    assert latest_states[0]["provider_time"] == 200
