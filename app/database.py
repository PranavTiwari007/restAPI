import re
import sqlite3
from pathlib import Path
from typing import Any

DB_FILE = Path(__file__).resolve().parent.parent / "data" / "airzone.db"
SCHEMA_PATH = Path(__file__).resolve().parent.parent / "schema.sql"
CELL = 4  


SEED = [
    ("mumbai", "Mumbai region", 17.5, 71.5, 20.5, 74.5),
    ("chennai", "Chennai region", 11.0, 78.0, 14.0, 81.0),
    ("london", "London region", 50.0, -3.0, 53.0, 1.0),
    ("new-york", "New York region", 39.0, -76.0, 42.0, -72.0),
]


def connect():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    with connect() as c:
        c.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
        c.executemany("INSERT OR IGNORE INTO zones VALUES (?,?,?,?,?,?)", SEED)


def cell_zone(zone_id):
    """Grid zone ids look like R12C40 (row/column). Bounds are computed from the id."""
    m = re.fullmatch(r"R(\d+)C(\d+)", zone_id)
    if not m:
        return None
    row, col = int(m[1]), int(m[2])
    if row >= 180 // CELL or col >= 360 // CELL:
        return None
    lamin, lomin = row * CELL - 90, col * CELL - 180
    return (zone_id, f"Grid {zone_id}", lamin, lomin, lamin + CELL, lomin + CELL)


def list_zones():
    with connect() as c:
        return [dict(r) for r in c.execute("SELECT * FROM zones ORDER BY name")]


def get_zone(zone_id):
    with connect() as c:
        row = c.execute("SELECT * FROM zones WHERE zone_id=?", (zone_id,)).fetchone()
        if row is None and cell_zone(zone_id):
            c.execute("INSERT INTO zones VALUES (?,?,?,?,?,?)", cell_zone(zone_id))
            row = c.execute("SELECT * FROM zones WHERE zone_id=?", (zone_id,)).fetchone()
        return dict(row) if row else None


def save_observations(aircraft, observed_at):
    saved = 0
    with connect() as c:
        for a in aircraft:
            if not a["has_position"]:
                continue
            last = c.execute("SELECT last_contact FROM aircraft_observations WHERE icao24=? "
                             "ORDER BY id DESC LIMIT 1", (a["icao24"],)).fetchone()
            if last and last["last_contact"] == a["last_contact"]:
                continue  
            c.execute("""INSERT INTO aircraft_observations (icao24, callsign, origin_country, latitude,
                longitude, baro_altitude, velocity, true_track, on_ground, last_contact, observed_at)
                VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                      (a["icao24"], a["callsign"], a["origin_country"], a["latitude"], a["longitude"],
                       a["baro_altitude"], a["velocity"], a["true_track"], int(bool(a["on_ground"])),
                       a["last_contact"], observed_at))
            saved += 1
    return saved


def aircraft_history(icao24, limit=50):
    with connect() as c:
        rows = c.execute("SELECT * FROM aircraft_observations WHERE icao24=? ORDER BY id DESC LIMIT ?",
                         (icao24, limit)).fetchall()
    return [dict(r) for r in rows]


def save_airport_import(
    airport_id: str,
    provider_time: int,
    imported_at: int,
    bounds: tuple[float, float, float, float],
    aircraft: list[dict[str, Any]],
) -> int:
    positioned_aircraft = [record for record in aircraft if record["has_position"]]
    with connect() as connection:
        cursor = connection.execute(
            """
            INSERT INTO airport_imports (
                airport_id, provider_time, imported_at, lamin, lomin, lamax, lomax,
                state_count, position_count
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                airport_id,
                provider_time,
                imported_at,
                *bounds,
                len(aircraft),
                len(positioned_aircraft),
            ),
        )
        import_id = cursor.lastrowid
        if import_id is None:
            raise sqlite3.DatabaseError("SQLite did not return an airport import ID")
        connection.executemany(
            """
            INSERT INTO airport_observations (
                import_id, icao24, callsign, origin_country, latitude, longitude,
                baro_altitude, geo_altitude, velocity, velocity_kmh, true_track,
                vertical_rate, on_ground, last_contact, time_position, squawk,
                position_source
            ) VALUES (
                :import_id, :icao24, :callsign, :origin_country, :latitude, :longitude,
                :baro_altitude, :geo_altitude, :velocity, :velocity_kmh, :true_track,
                :vertical_rate, :on_ground, :last_contact, :time_position, :squawk,
                :position_source
            )
            """,
            [
                {
                    **record,
                    "import_id": import_id,
                    "on_ground": (
                        int(record["on_ground"])
                        if record["on_ground"] is not None
                        else None
                    ),
                }
                for record in positioned_aircraft
            ],
        )
    return import_id


def get_latest_airport_import(airport_id: str) -> dict[str, Any] | None:
    with connect() as connection:
        latest = connection.execute(
            """
            SELECT * FROM airport_imports
            WHERE airport_id = ?
            ORDER BY id DESC LIMIT 1
            """,
            (airport_id,),
        ).fetchone()
        if latest is None:
            return None
        aircraft = connection.execute(
            """
            SELECT * FROM airport_observations
            WHERE import_id = ?
            ORDER BY callsign, icao24
            """,
            (latest["id"],),
        ).fetchall()
    return {
        "id": latest["id"],
        "airport_id": latest["airport_id"],
        "provider_time": latest["provider_time"],
        "imported_at": latest["imported_at"],
        "lamin": latest["lamin"],
        "lomin": latest["lomin"],
        "lamax": latest["lamax"],
        "lomax": latest["lomax"],
        "state_count": latest["state_count"],
        "position_count": latest["position_count"],
        "aircraft": [
            {
                **dict(record),
                "on_ground": (
                    bool(record["on_ground"])
                    if record["on_ground"] is not None
                    else None
                ),
                "has_position": True,
            }
            for record in aircraft
        ],
    }


def get_daily_airport_counts(
    airport_id: str,
    start_date: str,
    end_date: str,
) -> list[dict[str, int | str]]:
    with connect() as connection:
        rows = connection.execute(
            """
            SELECT
                date(imports.provider_time, 'unixepoch') AS day,
                COUNT(DISTINCT observations.icao24) AS observed_aircraft_count,
                COUNT(DISTINCT imports.id) AS sample_count
            FROM airport_imports AS imports
            LEFT JOIN airport_observations AS observations
                ON observations.import_id = imports.id
            WHERE imports.airport_id = ?
                AND date(imports.provider_time, 'unixepoch') BETWEEN ? AND ?
            GROUP BY date(imports.provider_time, 'unixepoch')
            ORDER BY day
            """,
            (airport_id, start_date, end_date),
        ).fetchall()
    return [dict(row) for row in rows]


def get_airport_aircraft_history(
    airport_id: str,
    icao24: str,
    limit: int = 50,
) -> list[dict[str, Any]]:
    with connect() as connection:
        rows = connection.execute(
            """
            SELECT observations.*, imports.airport_id, imports.provider_time,
                imports.imported_at
            FROM airport_observations AS observations
            JOIN airport_imports AS imports ON imports.id = observations.import_id
            WHERE imports.airport_id = ? AND observations.icao24 = ?
            ORDER BY imports.provider_time DESC, imports.id DESC
            LIMIT ?
            """,
            (airport_id, icao24, limit),
        ).fetchall()
    return [dict(row) for row in rows]
