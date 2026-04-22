from __future__ import annotations

import sqlite3

import pytest

from house_index.db.migrations import CURRENT_VERSION, migrate


V1_SCHEMA = """
CREATE TABLE schema_version (version INTEGER PRIMARY KEY);
INSERT INTO schema_version (version) VALUES (1);

CREATE TABLE properties (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    primary_link TEXT,
    property_type TEXT NOT NULL,
    multi_floor INTEGER NOT NULL DEFAULT 0,
    price_pln INTEGER,
    area_m2 REAL,
    distance_km REAL,
    rooms INTEGER,
    floor INTEGER,
    has_elevator INTEGER NOT NULL DEFAULT 0,
    has_balcony INTEGER NOT NULL DEFAULT 0,
    balcony_m2 REAL,
    has_terrace INTEGER NOT NULL DEFAULT 0,
    terrace_m2 REAL,
    has_garden INTEGER NOT NULL DEFAULT 0,
    garden_m2 REAL,
    parking_kind TEXT NOT NULL DEFAULT 'none',
    parking_spots INTEGER NOT NULL DEFAULT 0,
    year_built INTEGER,
    has_cellar INTEGER NOT NULL DEFAULT 0,
    cellar_m2 REAL,
    condition TEXT,
    status TEXT NOT NULL DEFAULT 'interested',
    notes TEXT,
    index_score REAL,
    index_breakdown TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
"""


@pytest.fixture()
def v1_db() -> sqlite3.Connection:
    c = sqlite3.connect(":memory:")
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA foreign_keys = ON")
    c.executescript(V1_SCHEMA)
    yield c
    c.close()


def test_migrate_v1_adds_new_columns(v1_db):
    v1_db.execute(
        "INSERT INTO properties (title, property_type, parking_kind, parking_spots) "
        "VALUES ('Test', 'apartment', 'garage', 2)"
    )
    v1_db.commit()

    new_version = migrate(v1_db)
    assert new_version == CURRENT_VERSION

    cols = [r["name"] for r in v1_db.execute("PRAGMA table_info(properties)").fetchall()]
    assert "plot_m2" in cols
    assert "has_garage" in cols
    assert "garage_spots" in cols
    assert "has_parking_spot" in cols
    assert "parking_spot_count" in cols
    assert "parking_kind" not in cols
    assert "parking_spots" not in cols


def test_migrate_v1_maps_garage_correctly(v1_db):
    v1_db.execute(
        "INSERT INTO properties (title, property_type, parking_kind, parking_spots) "
        "VALUES ('Garage house', 'house', 'garage', 2)"
    )
    v1_db.commit()
    migrate(v1_db)

    row = v1_db.execute(
        "SELECT has_garage, garage_spots, has_parking_spot, parking_spot_count "
        "FROM properties WHERE title = 'Garage house'"
    ).fetchone()
    assert row["has_garage"] == 1
    assert row["garage_spots"] == 2
    assert row["has_parking_spot"] == 0
    assert row["parking_spot_count"] == 0


def test_migrate_v1_maps_parking_spot_correctly(v1_db):
    v1_db.execute(
        "INSERT INTO properties (title, property_type, parking_kind, parking_spots) "
        "VALUES ('Lot byt', 'apartment', 'lot', 1)"
    )
    v1_db.commit()
    migrate(v1_db)

    row = v1_db.execute(
        "SELECT has_garage, garage_spots, has_parking_spot, parking_spot_count "
        "FROM properties WHERE title = 'Lot byt'"
    ).fetchone()
    assert row["has_garage"] == 0
    assert row["has_parking_spot"] == 1
    assert row["parking_spot_count"] == 1


def test_migrate_is_idempotent(v1_db):
    migrate(v1_db)
    assert migrate(v1_db) == CURRENT_VERSION
    assert migrate(v1_db) == CURRENT_VERSION


def test_migrate_fresh_db_goes_straight_to_current():
    c = sqlite3.connect(":memory:")
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA foreign_keys = ON")
    version = migrate(c)
    assert version == CURRENT_VERSION
    cols = [r["name"] for r in c.execute("PRAGMA table_info(properties)").fetchall()]
    assert "plot_m2" in cols
    assert "parking_kind" not in cols
    assert "nearest_supermarket_m" in cols
    assert "nearest_kindergarten_state_m" in cols
    assert "nearest_kindergarten_private_m" in cols
    assert "nearest_hospital_m" in cols
    assert "living_room_m2" in cols
    assert "kitchen_m2" in cols
    assert "bathroom_largest_m2" in cols
    assert "bedroom_master_m2" in cols
    assert "has_pantry" in cols
    assert "separate_wc_count" in cols

    transit_sql = c.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name='transit_stops'"
    ).fetchone()[0]
    assert "regional_bus" in transit_sql
    c.close()


def test_migrate_v3_to_v4_adds_room_fields():
    c = sqlite3.connect(":memory:")
    c.row_factory = sqlite3.Row
    c.executescript("""
        CREATE TABLE schema_version (version INTEGER PRIMARY KEY);
        INSERT INTO schema_version VALUES (3);
        CREATE TABLE properties (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            property_type TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'interested',
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at TEXT NOT NULL DEFAULT (datetime('now'))
        );
    """)
    c.commit()

    version = migrate(c)
    assert version == CURRENT_VERSION

    cols = [r["name"] for r in c.execute("PRAGMA table_info(properties)").fetchall()]
    for col in (
        "living_room_m2",
        "kitchen_m2",
        "bathroom_largest_m2",
        "bedroom_master_m2",
        "has_pantry",
        "separate_wc_count",
    ):
        assert col in cols
    c.close()


def test_migrate_v1_to_v3_full_chain(v1_db):
    v1_db.execute(
        "INSERT INTO properties (title, property_type, parking_kind, parking_spots) "
        "VALUES ('Old', 'apartment', 'lot', 1)"
    )
    v1_db.commit()
    migrate(v1_db)

    cols = [r["name"] for r in v1_db.execute("PRAGMA table_info(properties)").fetchall()]
    for amenity in (
        "nearest_supermarket_m",
        "nearest_kindergarten_state_m",
        "nearest_kindergarten_private_m",
        "nearest_hospital_m",
    ):
        assert amenity in cols


def test_migrate_v2_to_v3_adds_amenities():
    c = sqlite3.connect(":memory:")
    c.row_factory = sqlite3.Row
    c.executescript("""
        CREATE TABLE schema_version (version INTEGER PRIMARY KEY);
        INSERT INTO schema_version VALUES (2);
        CREATE TABLE properties (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            property_type TEXT NOT NULL,
            multi_floor INTEGER NOT NULL DEFAULT 0,
            has_elevator INTEGER NOT NULL DEFAULT 0,
            has_balcony INTEGER NOT NULL DEFAULT 0,
            has_terrace INTEGER NOT NULL DEFAULT 0,
            has_garden INTEGER NOT NULL DEFAULT 0,
            plot_m2 REAL,
            has_garage INTEGER NOT NULL DEFAULT 0,
            garage_spots INTEGER NOT NULL DEFAULT 0,
            has_parking_spot INTEGER NOT NULL DEFAULT 0,
            parking_spot_count INTEGER NOT NULL DEFAULT 0,
            has_cellar INTEGER NOT NULL DEFAULT 0,
            condition TEXT,
            status TEXT NOT NULL DEFAULT 'interested',
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at TEXT NOT NULL DEFAULT (datetime('now'))
        );
        CREATE TABLE transit_stops (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            property_id INTEGER NOT NULL,
            kind TEXT NOT NULL CHECK(kind IN ('bus', 'tram', 'train')),
            distance_m INTEGER NOT NULL,
            name TEXT
        );
    """)
    c.commit()

    version = migrate(c)
    assert version == CURRENT_VERSION

    transit_sql = c.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name='transit_stops'"
    ).fetchone()[0]
    assert "regional_bus" in transit_sql
    c.close()
