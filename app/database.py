import re
import sqlite3
from pathlib import Path

DB_FILE = Path(__file__).resolve().parent.parent / "data" / "airzone.db"
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
    return conn


def init_db():
    with connect() as c:
        
        c.execute("""CREATE TABLE IF NOT EXISTS zones (
            zone_id TEXT PRIMARY KEY, name TEXT NOT NULL,
            lamin REAL, lomin REAL, lamax REAL, lomax REAL)""")
        
        c.execute("""CREATE TABLE IF NOT EXISTS aircraft_observations (
            id INTEGER PRIMARY KEY AUTOINCREMENT, icao24 TEXT NOT NULL, callsign TEXT,
            origin_country TEXT, latitude REAL, longitude REAL, baro_altitude REAL,
            velocity REAL, true_track REAL, on_ground INTEGER, last_contact INTEGER,
            observed_at INTEGER NOT NULL)""")
        c.execute("CREATE INDEX IF NOT EXISTS idx_obs ON aircraft_observations (icao24, id)")
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
