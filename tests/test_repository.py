from __future__ import annotations

import sqlite3

import pytest

from house_index.db import repository as repo
from house_index.db.migrations import CURRENT_VERSION, migrate
from house_index.domain.enums import (
    Condition,
    PropertyType,
    Status,
    TransitKind,
)
from house_index.domain.models import Link, Photo, Property, TransitStop


@pytest.fixture()
def conn() -> sqlite3.Connection:
    c = sqlite3.connect(":memory:")
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA foreign_keys = ON")
    migrate(c)
    yield c
    c.close()


def _sample_property() -> Property:
    return Property(
        title="Brynów 3+kk",
        property_type=PropertyType.APARTMENT,
        primary_link="https://otodom.pl/xyz",
        price_pln=450_000,
        area_m2=62.0,
        distance_km=3.2,
        rooms=3,
        floor=4,
        has_elevator=True,
        has_balcony=True,
        balcony_m2=6.0,
        has_parking_spot=True,
        parking_spot_count=1,
        year_built=2015,
        condition=Condition.STANDARD,
        status=Status.INTERESTED,
        links=[Link(url="https://maps.google.com/xyz", label="Mapa")],
        transit_stops=[TransitStop(kind=TransitKind.TRAM, distance_m=350, name="Brynów")],
        photos=[Photo(file_name="a.jpg", is_primary=True)],
        tags=["centrum", "nova"],
    )


def test_migrate_is_idempotent(conn):
    assert migrate(conn) == CURRENT_VERSION
    assert migrate(conn) == CURRENT_VERSION


def test_save_and_get_property_round_trip(conn):
    prop = _sample_property()
    pid = repo.save_property(conn, prop)
    assert pid is not None

    loaded = repo.get_property(conn, pid)
    assert loaded is not None
    assert loaded.title == "Brynów 3+kk"
    assert loaded.property_type is PropertyType.APARTMENT
    assert loaded.price_pln == 450_000
    assert loaded.has_elevator is True
    assert loaded.has_parking_spot is True
    assert loaded.parking_spot_count == 1
    assert loaded.condition is Condition.STANDARD
    assert len(loaded.links) == 1
    assert loaded.links[0].url == "https://maps.google.com/xyz"
    assert len(loaded.transit_stops) == 1
    assert loaded.transit_stops[0].kind is TransitKind.TRAM
    assert len(loaded.photos) == 1
    assert loaded.photos[0].is_primary is True
    assert set(loaded.tags) == {"centrum", "nova"}


def test_update_property_replaces_relations(conn):
    prop = _sample_property()
    pid = repo.save_property(conn, prop)

    loaded = repo.get_property(conn, pid)
    loaded.price_pln = 420_000
    loaded.links = [Link(url="https://new.link")]
    loaded.tags = ["super"]
    repo.save_property(conn, loaded)

    reloaded = repo.get_property(conn, pid)
    assert reloaded.price_pln == 420_000
    assert len(reloaded.links) == 1
    assert reloaded.links[0].url == "https://new.link"
    assert reloaded.tags == ["super"]


def test_delete_cascades(conn):
    prop = _sample_property()
    pid = repo.save_property(conn, prop)
    repo.delete_property(conn, pid)

    assert repo.get_property(conn, pid) is None
    assert conn.execute("SELECT COUNT(*) FROM links").fetchone()[0] == 0
    assert conn.execute("SELECT COUNT(*) FROM transit_stops").fetchone()[0] == 0
    assert conn.execute("SELECT COUNT(*) FROM photos").fetchone()[0] == 0
    assert conn.execute("SELECT COUNT(*) FROM property_tags").fetchone()[0] == 0


def test_list_filters_by_status_and_sorts(conn):
    a = _sample_property()
    a.title = "A"
    a.index_score = 80.0
    repo.save_property(conn, a)

    b = _sample_property()
    b.title = "B"
    b.status = Status.REJECTED
    b.index_score = 95.0
    repo.save_property(conn, b)

    c = _sample_property()
    c.title = "C"
    c.index_score = 90.0
    repo.save_property(conn, c)

    all_props = repo.list_properties(conn)
    assert [p.title for p in all_props] == ["B", "C", "A"]

    interested = repo.list_properties(conn, status=Status.INTERESTED)
    assert [p.title for p in interested] == ["C", "A"]


def test_scoring_config_active(conn):
    assert repo.get_active_config(conn) is None
    cfg1 = {"price_pln": {"max_points": 30}}
    repo.save_active_config(conn, "v1", cfg1)
    assert repo.get_active_config(conn) == cfg1

    cfg2 = {"price_pln": {"max_points": 40}}
    repo.save_active_config(conn, "v2", cfg2)
    assert repo.get_active_config(conn) == cfg2

    rows = repo.list_configs(conn)
    assert len(rows) == 2


def test_settings_kv(conn):
    assert repo.get_setting(conn, "lang", "sk") == "sk"
    repo.set_setting(conn, "lang", "pl")
    assert repo.get_setting(conn, "lang") == "pl"
    repo.set_setting(conn, "lang", "sk")
    assert repo.get_setting(conn, "lang") == "sk"


def test_update_index_cache(conn):
    prop = _sample_property()
    pid = repo.save_property(conn, prop)
    repo.update_index_cache(conn, pid, 92.5, {"price_pln": 30})

    loaded = repo.get_property(conn, pid)
    assert loaded.index_score == 92.5
    assert loaded.index_breakdown == {"price_pln": 30}


def test_price_per_m2_property():
    p = Property(title="x", price_pln=620_000, area_m2=62.0)
    assert p.price_per_m2 == pytest.approx(10_000.0)

    p2 = Property(title="y")
    assert p2.price_per_m2 is None


def test_nearest_transit_m():
    p = Property(
        title="x",
        transit_stops=[
            TransitStop(kind=TransitKind.BUS, distance_m=800),
            TransitStop(kind=TransitKind.TRAM, distance_m=400),
            TransitStop(kind=TransitKind.TRAIN, distance_m=1500),
        ],
    )
    assert p.nearest_transit_m == 400
    assert Property(title="y").nearest_transit_m is None
