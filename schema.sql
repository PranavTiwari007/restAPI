CREATE TABLE IF NOT EXISTS snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    provider_time INTEGER NOT NULL,
    imported_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    lamin REAL NOT NULL CHECK (lamin >= -90 AND lamin <= 90),
    lomin REAL NOT NULL CHECK (lomin >= -180 AND lomin <= 180),
    lamax REAL NOT NULL CHECK (lamax >= -90 AND lamax <= 90),
    lomax REAL NOT NULL CHECK (lomax >= -180 AND lomax <= 180),
    CHECK (lamin < lamax),
    CHECK (lomin < lomax)
);

CREATE TABLE IF NOT EXISTS aircraft_states (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    snapshot_id INTEGER NOT NULL REFERENCES snapshots(id) ON DELETE CASCADE,
    icao24 TEXT NOT NULL CHECK (length(icao24) = 6),
    callsign TEXT,
    origin_country TEXT NOT NULL,
    last_contact INTEGER NOT NULL,
    longitude REAL,
    latitude REAL,
    baro_altitude REAL,
    on_ground INTEGER NOT NULL CHECK (on_ground IN (0, 1)),
    velocity REAL,
    true_track REAL,
    vertical_rate REAL,
    geo_altitude REAL,
    squawk TEXT,
    position_source INTEGER,
    UNIQUE (snapshot_id, icao24)
);

CREATE INDEX IF NOT EXISTS idx_aircraft_states_snapshot_icao24
    ON aircraft_states(snapshot_id, icao24);
