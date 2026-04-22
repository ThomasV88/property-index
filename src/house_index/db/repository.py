from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterable, Iterator

from house_index.db.migrations import migrate
from house_index.domain.enums import (
    Condition,
    PropertyType,
    Status,
    TransitKind,
)
from house_index.domain.models import Link, Photo, Property, TransitStop

_PROPERTY_COLUMNS = (
    "title, primary_link, property_type, multi_floor, price_pln, area_m2, distance_km, "
    "rooms, floor, has_elevator, has_balcony, balcony_m2, has_terrace, terrace_m2, "
    "has_garden, garden_m2, plot_m2, has_garage, garage_spots, has_parking_spot, "
    "parking_spot_count, year_built, has_cellar, cellar_m2, condition, "
    "nearest_supermarket_m, nearest_kindergarten_state_m, nearest_kindergarten_private_m, "
    "nearest_hospital_m, living_room_m2, kitchen_m2, bathroom_largest_m2, "
    "bedroom_master_m2, has_pantry, separate_wc_count, "
    "status, notes, index_score, index_breakdown"
)
_PROPERTY_COL_COUNT = len(_PROPERTY_COLUMNS.split(","))


@contextmanager
def open_connection(db_path: Path | str) -> Iterator[sqlite3.Connection]:
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def initialize(db_path: Path | str) -> None:
    with open_connection(db_path) as conn:
        migrate(conn)


def _property_params(p: Property) -> tuple[Any, ...]:
    return (
        p.title,
        p.primary_link,
        p.property_type.value,
        int(p.multi_floor),
        p.price_pln,
        p.area_m2,
        p.distance_km,
        p.rooms,
        p.floor,
        int(p.has_elevator),
        int(p.has_balcony),
        p.balcony_m2,
        int(p.has_terrace),
        p.terrace_m2,
        int(p.has_garden),
        p.garden_m2,
        p.plot_m2,
        int(p.has_garage),
        p.garage_spots,
        int(p.has_parking_spot),
        p.parking_spot_count,
        p.year_built,
        int(p.has_cellar),
        p.cellar_m2,
        p.condition.value if p.condition else None,
        p.nearest_supermarket_m,
        p.nearest_kindergarten_state_m,
        p.nearest_kindergarten_private_m,
        p.nearest_hospital_m,
        p.living_room_m2,
        p.kitchen_m2,
        p.bathroom_largest_m2,
        p.bedroom_master_m2,
        int(p.has_pantry),
        p.separate_wc_count,
        p.status.value,
        p.notes,
        p.index_score,
        json.dumps(p.index_breakdown) if p.index_breakdown is not None else None,
    )


def _row_to_property(row: sqlite3.Row) -> Property:
    breakdown = json.loads(row["index_breakdown"]) if row["index_breakdown"] else None
    return Property(
        id=row["id"],
        title=row["title"],
        primary_link=row["primary_link"],
        property_type=PropertyType(row["property_type"]),
        multi_floor=bool(row["multi_floor"]),
        price_pln=row["price_pln"],
        area_m2=row["area_m2"],
        distance_km=row["distance_km"],
        rooms=row["rooms"],
        floor=row["floor"],
        has_elevator=bool(row["has_elevator"]),
        has_balcony=bool(row["has_balcony"]),
        balcony_m2=row["balcony_m2"],
        has_terrace=bool(row["has_terrace"]),
        terrace_m2=row["terrace_m2"],
        has_garden=bool(row["has_garden"]),
        garden_m2=row["garden_m2"],
        plot_m2=row["plot_m2"],
        has_garage=bool(row["has_garage"]),
        garage_spots=row["garage_spots"],
        has_parking_spot=bool(row["has_parking_spot"]),
        parking_spot_count=row["parking_spot_count"],
        year_built=row["year_built"],
        has_cellar=bool(row["has_cellar"]),
        cellar_m2=row["cellar_m2"],
        condition=Condition(row["condition"]) if row["condition"] else None,
        nearest_supermarket_m=row["nearest_supermarket_m"],
        nearest_kindergarten_state_m=row["nearest_kindergarten_state_m"],
        nearest_kindergarten_private_m=row["nearest_kindergarten_private_m"],
        nearest_hospital_m=row["nearest_hospital_m"],
        living_room_m2=row["living_room_m2"],
        kitchen_m2=row["kitchen_m2"],
        bathroom_largest_m2=row["bathroom_largest_m2"],
        bedroom_master_m2=row["bedroom_master_m2"],
        has_pantry=bool(row["has_pantry"]),
        separate_wc_count=row["separate_wc_count"],
        status=Status(row["status"]),
        notes=row["notes"],
        index_score=row["index_score"],
        index_breakdown=breakdown,
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def save_property(conn: sqlite3.Connection, prop: Property) -> int:
    placeholders = ", ".join(["?"] * _PROPERTY_COL_COUNT)
    if prop.id is None:
        sql = f"INSERT INTO properties ({_PROPERTY_COLUMNS}) VALUES ({placeholders})"
        cur = conn.execute(sql, _property_params(prop))
        prop.id = cur.lastrowid
    else:
        assignments = ", ".join(f"{c.strip()} = ?" for c in _PROPERTY_COLUMNS.split(","))
        sql = f"UPDATE properties SET {assignments}, updated_at = datetime('now') WHERE id = ?"
        conn.execute(sql, (*_property_params(prop), prop.id))

    _replace_relations(conn, prop)
    return prop.id


def _replace_relations(conn: sqlite3.Connection, prop: Property) -> None:
    pid = prop.id
    assert pid is not None

    conn.execute("DELETE FROM links WHERE property_id = ?", (pid,))
    for link in prop.links:
        conn.execute(
            "INSERT INTO links (property_id, url, label) VALUES (?, ?, ?)",
            (pid, link.url, link.label),
        )

    conn.execute("DELETE FROM transit_stops WHERE property_id = ?", (pid,))
    for stop in prop.transit_stops:
        conn.execute(
            "INSERT INTO transit_stops (property_id, kind, distance_m, name) "
            "VALUES (?, ?, ?, ?)",
            (pid, stop.kind.value, stop.distance_m, stop.name),
        )

    conn.execute("DELETE FROM photos WHERE property_id = ?", (pid,))
    for photo in prop.photos:
        conn.execute(
            "INSERT INTO photos (property_id, file_name, is_primary, sort_order) "
            "VALUES (?, ?, ?, ?)",
            (pid, photo.file_name, int(photo.is_primary), photo.sort_order),
        )

    set_property_tags(conn, pid, prop.tags)


def set_property_tags(conn: sqlite3.Connection, property_id: int, tags: Iterable[str]) -> None:
    conn.execute("DELETE FROM property_tags WHERE property_id = ?", (property_id,))
    for name in tags:
        name = name.strip()
        if not name:
            continue
        conn.execute("INSERT OR IGNORE INTO tags (name) VALUES (?)", (name,))
        tag_id = conn.execute("SELECT id FROM tags WHERE name = ?", (name,)).fetchone()[0]
        conn.execute(
            "INSERT OR IGNORE INTO property_tags (property_id, tag_id) VALUES (?, ?)",
            (property_id, tag_id),
        )


def get_property(conn: sqlite3.Connection, property_id: int) -> Property | None:
    row = conn.execute("SELECT * FROM properties WHERE id = ?", (property_id,)).fetchone()
    if row is None:
        return None
    prop = _row_to_property(row)
    _load_relations(conn, prop)
    return prop


def list_properties(
    conn: sqlite3.Connection,
    order_by: str = "index_score DESC, id DESC",
    status: Status | None = None,
) -> list[Property]:
    sql = "SELECT * FROM properties"
    params: tuple[Any, ...] = ()
    if status is not None:
        sql += " WHERE status = ?"
        params = (status.value,)
    sql += f" ORDER BY {order_by}"
    rows = conn.execute(sql, params).fetchall()
    props = [_row_to_property(r) for r in rows]
    for p in props:
        _load_relations(conn, p)
    return props


def _load_relations(conn: sqlite3.Connection, prop: Property) -> None:
    pid = prop.id
    assert pid is not None

    rows = conn.execute(
        "SELECT * FROM links WHERE property_id = ? ORDER BY id", (pid,)
    ).fetchall()
    prop.links = [Link(id=r["id"], property_id=pid, url=r["url"], label=r["label"]) for r in rows]

    rows = conn.execute(
        "SELECT * FROM transit_stops WHERE property_id = ? ORDER BY distance_m", (pid,)
    ).fetchall()
    prop.transit_stops = [
        TransitStop(
            id=r["id"],
            property_id=pid,
            kind=TransitKind(r["kind"]),
            distance_m=r["distance_m"],
            name=r["name"],
        )
        for r in rows
    ]

    rows = conn.execute(
        "SELECT * FROM photos WHERE property_id = ? ORDER BY is_primary DESC, sort_order, id",
        (pid,),
    ).fetchall()
    prop.photos = [
        Photo(
            id=r["id"],
            property_id=pid,
            file_name=r["file_name"],
            is_primary=bool(r["is_primary"]),
            sort_order=r["sort_order"],
        )
        for r in rows
    ]

    rows = conn.execute(
        "SELECT t.name FROM tags t JOIN property_tags pt ON pt.tag_id = t.id "
        "WHERE pt.property_id = ? ORDER BY t.name",
        (pid,),
    ).fetchall()
    prop.tags = [r["name"] for r in rows]


def delete_property(conn: sqlite3.Connection, property_id: int) -> None:
    conn.execute("DELETE FROM properties WHERE id = ?", (property_id,))


def list_all_tags(conn: sqlite3.Connection) -> list[str]:
    rows = conn.execute("SELECT name FROM tags ORDER BY name").fetchall()
    return [r["name"] for r in rows]


def get_active_config(conn: sqlite3.Connection) -> dict[str, Any] | None:
    row = conn.execute(
        "SELECT config_json FROM scoring_config WHERE is_active = 1 LIMIT 1"
    ).fetchone()
    if row is None:
        return None
    return json.loads(row["config_json"])


def save_active_config(conn: sqlite3.Connection, name: str, config: dict[str, Any]) -> int:
    conn.execute("UPDATE scoring_config SET is_active = 0 WHERE is_active = 1")
    cur = conn.execute(
        "INSERT INTO scoring_config (name, is_active, config_json) VALUES (?, 1, ?)",
        (name, json.dumps(config)),
    )
    return cur.lastrowid


def list_configs(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    return conn.execute(
        "SELECT id, name, is_active, updated_at FROM scoring_config ORDER BY id DESC"
    ).fetchall()


def update_index_cache(
    conn: sqlite3.Connection,
    property_id: int,
    score: float,
    breakdown: dict[str, Any],
) -> None:
    conn.execute(
        "UPDATE properties SET index_score = ?, index_breakdown = ? WHERE id = ?",
        (score, json.dumps(breakdown), property_id),
    )


def get_setting(conn: sqlite3.Connection, key: str, default: str | None = None) -> str | None:
    row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
    return row["value"] if row else default


def set_setting(conn: sqlite3.Connection, key: str, value: str) -> None:
    conn.execute(
        "INSERT INTO settings (key, value) VALUES (?, ?) "
        "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
        (key, value),
    )
