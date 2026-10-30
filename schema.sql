CREATE TABLE IF NOT EXISTS zones (
    zone_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    lamin REAL,
    lomin REAL,
    lamax REAL,
    lomax REAL
);

CREATE TABLE IF NOT EXISTS aircraft_observations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    icao24 TEXT NOT NULL,
    callsign TEXT,
    origin_country TEXT,
    latitude REAL,
    longitude REAL,
    baro_altitude REAL,
    velocity REAL,
    true_track REAL,
    on_ground INTEGER,
    last_contact INTEGER,
    observed_at INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_obs
    ON aircraft_observations (icao24, id);

CREATE TABLE IF NOT EXISTS airport_imports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    airport_id TEXT NOT NULL,
    provider_time INTEGER NOT NULL,
    imported_at INTEGER NOT NULL,
    lamin REAL NOT NULL,
    lomin REAL NOT NULL,
    lamax REAL NOT NULL,
    lomax REAL NOT NULL,
    state_count INTEGER NOT NULL,
    position_count INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_airport_imports_airport_time
    ON airport_imports (airport_id, provider_time);

CREATE TABLE IF NOT EXISTS airport_observations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    import_id INTEGER NOT NULL REFERENCES airport_imports(id) ON DELETE CASCADE,
    icao24 TEXT NOT NULL,
    callsign TEXT,
    origin_country TEXT,
    latitude REAL NOT NULL,
    longitude REAL NOT NULL,
    baro_altitude REAL,
    geo_altitude REAL,
    velocity REAL,
    velocity_kmh REAL,
    true_track REAL,
    vertical_rate REAL,
    on_ground INTEGER,
    last_contact INTEGER,
    time_position INTEGER,
    squawk TEXT,
    position_source INTEGER
);

CREATE INDEX IF NOT EXISTS idx_airport_observations_import
    ON airport_observations (import_id);

CREATE INDEX IF NOT EXISTS idx_airport_observations_icao
    ON airport_observations (icao24, id);
