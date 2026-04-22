PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;

CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS properties (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    title             TEXT    NOT NULL,
    primary_link      TEXT,
    property_type     TEXT    NOT NULL CHECK(property_type IN ('apartment', 'house')),
    multi_floor       INTEGER NOT NULL DEFAULT 0,
    price_pln         INTEGER,
    area_m2           REAL,
    distance_km       REAL,
    rooms             INTEGER,
    floor             INTEGER,
    has_elevator      INTEGER NOT NULL DEFAULT 0,
    has_balcony       INTEGER NOT NULL DEFAULT 0,
    balcony_m2        REAL,
    has_terrace       INTEGER NOT NULL DEFAULT 0,
    terrace_m2        REAL,
    has_garden        INTEGER NOT NULL DEFAULT 0,
    garden_m2         REAL,
    plot_m2           REAL,
    has_garage        INTEGER NOT NULL DEFAULT 0,
    garage_spots      INTEGER NOT NULL DEFAULT 0,
    has_parking_spot  INTEGER NOT NULL DEFAULT 0,
    parking_spot_count INTEGER NOT NULL DEFAULT 0,
    year_built        INTEGER,
    has_cellar        INTEGER NOT NULL DEFAULT 0,
    cellar_m2         REAL,
    condition         TEXT    CHECK(condition IN ('shell', 'standard', 'turnkey')),
    nearest_supermarket_m         INTEGER,
    nearest_kindergarten_state_m  INTEGER,
    nearest_kindergarten_private_m INTEGER,
    nearest_hospital_m            INTEGER,
    living_room_m2        REAL,
    kitchen_m2            REAL,
    bathroom_largest_m2   REAL,
    bedroom_master_m2     REAL,
    has_pantry            INTEGER NOT NULL DEFAULT 0,
    separate_wc_count     INTEGER NOT NULL DEFAULT 0,
    status            TEXT    NOT NULL DEFAULT 'interested'
                         CHECK(status IN ('interested', 'visited', 'rejected', 'reserved')),
    notes             TEXT,
    index_score       REAL,
    index_breakdown   TEXT,
    created_at        TEXT    NOT NULL DEFAULT (datetime('now')),
    updated_at        TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_properties_status ON properties(status);
CREATE INDEX IF NOT EXISTS idx_properties_index_score ON properties(index_score DESC);

CREATE TABLE IF NOT EXISTS transit_stops (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    property_id INTEGER NOT NULL REFERENCES properties(id) ON DELETE CASCADE,
    kind        TEXT    NOT NULL CHECK(kind IN ('bus', 'tram', 'train', 'regional_bus')),
    distance_m  INTEGER NOT NULL,
    name        TEXT
);

CREATE INDEX IF NOT EXISTS idx_transit_stops_property ON transit_stops(property_id);

CREATE TABLE IF NOT EXISTS links (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    property_id INTEGER NOT NULL REFERENCES properties(id) ON DELETE CASCADE,
    url         TEXT    NOT NULL,
    label       TEXT
);

CREATE INDEX IF NOT EXISTS idx_links_property ON links(property_id);

CREATE TABLE IF NOT EXISTS photos (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    property_id INTEGER NOT NULL REFERENCES properties(id) ON DELETE CASCADE,
    file_name   TEXT    NOT NULL,
    is_primary  INTEGER NOT NULL DEFAULT 0,
    sort_order  INTEGER NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_photos_property ON photos(property_id);

CREATE TABLE IF NOT EXISTS tags (
    id   INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT    NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS property_tags (
    property_id INTEGER NOT NULL REFERENCES properties(id) ON DELETE CASCADE,
    tag_id      INTEGER NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
    PRIMARY KEY (property_id, tag_id)
);

CREATE INDEX IF NOT EXISTS idx_property_tags_tag ON property_tags(tag_id);

CREATE TABLE IF NOT EXISTS scoring_config (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT    NOT NULL,
    is_active   INTEGER NOT NULL DEFAULT 0,
    config_json TEXT    NOT NULL,
    updated_at  TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_scoring_config_active
    ON scoring_config(is_active) WHERE is_active = 1;

CREATE TABLE IF NOT EXISTS settings (
    key   TEXT PRIMARY KEY,
    value TEXT
);
