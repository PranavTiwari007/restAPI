from contextlib import closing
from pathlib import Path
import sqlite3

from app.state_mapping import AircraftStateRecord


DEFAULT_DATABASE_PATH = Path("data/aircraft.db")
SCHEMA_PATH = Path(__file__).resolve().parent.parent / "schema.sql"
BoundsValues = tuple[float, float, float, float]


def connect(database_path: Path | str = DEFAULT_DATABASE_PATH) -> sqlite3.Connection:
    path = str(database_path)
    if path != ":memory:":
        Path(path).parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize_database(database_path: Path | str = DEFAULT_DATABASE_PATH) -> None:
    schema = SCHEMA_PATH.read_text(encoding="utf-8")
    with closing(connect(database_path)) as connection:
        connection.executescript(schema)


def save_snapshot(
    connection: sqlite3.Connection,
    provider_time: int,
    bounds: BoundsValues,
    states: list[AircraftStateRecord],
) -> int:
    with connection:
        cursor = connection.execute(
            """
            INSERT INTO snapshots (provider_time, lamin, lomin, lamax, lomax)
            VALUES (?, ?, ?, ?, ?)
            """,
            (provider_time, *bounds),
        )
        snapshot_id = cursor.lastrowid
        if snapshot_id is None:
            raise sqlite3.DatabaseError("SQLite did not return a snapshot ID")

        connection.executemany(
            """
            INSERT INTO aircraft_states (
                snapshot_id, icao24, callsign, origin_country, last_contact,
                longitude, latitude, baro_altitude, on_ground, velocity,
                true_track, vertical_rate, geo_altitude, squawk, position_source
            )
            VALUES (
                :snapshot_id, :icao24, :callsign, :origin_country, :last_contact,
                :longitude, :latitude, :baro_altitude, :on_ground, :velocity,
                :true_track, :vertical_rate, :geo_altitude, :squawk,
                :position_source
            )
            """,
            [
                {
                    **state,
                    "snapshot_id": snapshot_id,
                    "on_ground": int(state["on_ground"]),
                }
                for state in states
            ],
        )

    return snapshot_id


def get_latest_snapshot(connection: sqlite3.Connection) -> sqlite3.Row | None:
    return connection.execute(
        """
        SELECT snapshots.*, COUNT(aircraft_states.id) AS state_count
        FROM snapshots
        LEFT JOIN aircraft_states ON aircraft_states.snapshot_id = snapshots.id
        WHERE snapshots.id = (SELECT id FROM snapshots ORDER BY id DESC LIMIT 1)
        GROUP BY snapshots.id
        """
    ).fetchone()


def list_latest_aircraft_states(
    connection: sqlite3.Connection,
) -> list[sqlite3.Row]:
    return connection.execute(
        """
        SELECT aircraft_states.*, snapshots.provider_time, snapshots.imported_at
        FROM aircraft_states
        JOIN snapshots ON snapshots.id = aircraft_states.snapshot_id
        WHERE snapshots.id = (
            SELECT id FROM snapshots ORDER BY id DESC LIMIT 1
        )
        ORDER BY aircraft_states.icao24
        """
    ).fetchall()


def get_aircraft_state(
    connection: sqlite3.Connection,
    state_id: int,
) -> sqlite3.Row | None:
    return connection.execute(
        """
        SELECT aircraft_states.*, snapshots.provider_time, snapshots.imported_at
        FROM aircraft_states
        JOIN snapshots ON snapshots.id = aircraft_states.snapshot_id
        WHERE aircraft_states.id = ?
        """,
        (state_id,),
    ).fetchone()
