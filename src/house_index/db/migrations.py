from __future__ import annotations

import sqlite3
from pathlib import Path

SCHEMA_FILE = Path(__file__).resolve().parent / "schema.sql"
CURRENT_VERSION = 4


def _read_schema() -> str:
    return SCHEMA_FILE.read_text(encoding="utf-8")


def _get_version(conn: sqlite3.Connection) -> int:
    cur = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='schema_version'"
    )
    if cur.fetchone() is None:
        return 0
    row = conn.execute("SELECT MAX(version) FROM schema_version").fetchone()
    return row[0] or 0


def _set_version(conn: sqlite3.Connection, version: int) -> None:
    conn.execute("DELETE FROM schema_version")
    conn.execute("INSERT INTO schema_version (version) VALUES (?)", (version,))


def _has_column(conn: sqlite3.Connection, table: str, column: str) -> bool:
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    return any(r[1] == column for r in rows)


def _migrate_v1_to_v2(conn: sqlite3.Connection) -> None:
    """Pridá plot_m2 + rozdelí parking_kind/parking_spots na garage + parking_spot."""
    if not _has_column(conn, "properties", "plot_m2"):
        conn.execute("ALTER TABLE properties ADD COLUMN plot_m2 REAL")
    if not _has_column(conn, "properties", "has_garage"):
        conn.execute("ALTER TABLE properties ADD COLUMN has_garage INTEGER NOT NULL DEFAULT 0")
    if not _has_column(conn, "properties", "garage_spots"):
        conn.execute("ALTER TABLE properties ADD COLUMN garage_spots INTEGER NOT NULL DEFAULT 0")
    if not _has_column(conn, "properties", "has_parking_spot"):
        conn.execute(
            "ALTER TABLE properties ADD COLUMN has_parking_spot INTEGER NOT NULL DEFAULT 0"
        )
    if not _has_column(conn, "properties", "parking_spot_count"):
        conn.execute(
            "ALTER TABLE properties ADD COLUMN parking_spot_count INTEGER NOT NULL DEFAULT 0"
        )

    if _has_column(conn, "properties", "parking_kind"):
        conn.execute(
            """
            UPDATE properties SET
                has_garage = CASE WHEN parking_kind = 'garage' THEN 1 ELSE 0 END,
                garage_spots = CASE WHEN parking_kind = 'garage' THEN parking_spots ELSE 0 END,
                has_parking_spot = CASE WHEN parking_kind IN ('street', 'lot') THEN 1 ELSE 0 END,
                parking_spot_count = CASE WHEN parking_kind IN ('street', 'lot') THEN parking_spots ELSE 0 END
            """
        )
        conn.execute("ALTER TABLE properties DROP COLUMN parking_kind")
        conn.execute("ALTER TABLE properties DROP COLUMN parking_spots")


def _migrate_v2_to_v3(conn: sqlite3.Connection) -> None:
    """Pridá amenity polia (supermarket, 2× kindergarten, hospital) a regional_bus kind."""
    for col in (
        "nearest_supermarket_m",
        "nearest_kindergarten_state_m",
        "nearest_kindergarten_private_m",
        "nearest_hospital_m",
    ):
        if not _has_column(conn, "properties", col):
            conn.execute(f"ALTER TABLE properties ADD COLUMN {col} INTEGER")

    row = conn.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name='transit_stops'"
    ).fetchone()
    if row and "'regional_bus'" not in row[0]:
        conn.executescript(
            """
            CREATE TABLE transit_stops_new (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                property_id INTEGER NOT NULL REFERENCES properties(id) ON DELETE CASCADE,
                kind        TEXT    NOT NULL CHECK(kind IN ('bus', 'tram', 'train', 'regional_bus')),
                distance_m  INTEGER NOT NULL,
                name        TEXT
            );
            INSERT INTO transit_stops_new (id, property_id, kind, distance_m, name)
                SELECT id, property_id, kind, distance_m, name FROM transit_stops;
            DROP TABLE transit_stops;
            ALTER TABLE transit_stops_new RENAME TO transit_stops;
            CREATE INDEX IF NOT EXISTS idx_transit_stops_property ON transit_stops(property_id);
            """
        )


def _migrate_v3_to_v4(conn: sqlite3.Connection) -> None:
    """Pridá plochy izieb (obývačka/kuchyňa/kúpeľňa/spálňa) + špajzu + počet samostatných WC."""
    for col, col_type in (
        ("living_room_m2", "REAL"),
        ("kitchen_m2", "REAL"),
        ("bathroom_largest_m2", "REAL"),
        ("bedroom_master_m2", "REAL"),
    ):
        if not _has_column(conn, "properties", col):
            conn.execute(f"ALTER TABLE properties ADD COLUMN {col} {col_type}")
    if not _has_column(conn, "properties", "has_pantry"):
        conn.execute("ALTER TABLE properties ADD COLUMN has_pantry INTEGER NOT NULL DEFAULT 0")
    if not _has_column(conn, "properties", "separate_wc_count"):
        conn.execute(
            "ALTER TABLE properties ADD COLUMN separate_wc_count INTEGER NOT NULL DEFAULT 0"
        )


def migrate(conn: sqlite3.Connection) -> int:
    """Apply pending migrations. Returns new schema version."""
    current = _get_version(conn)
    if current >= CURRENT_VERSION:
        return current

    if current == 0:
        conn.executescript(_read_schema())
        _set_version(conn, CURRENT_VERSION)
        conn.commit()
        return CURRENT_VERSION

    if current < 2:
        _migrate_v1_to_v2(conn)
    if current < 3:
        _migrate_v2_to_v3(conn)
    if current < 4:
        _migrate_v3_to_v4(conn)

    _set_version(conn, CURRENT_VERSION)
    conn.commit()
    return CURRENT_VERSION
