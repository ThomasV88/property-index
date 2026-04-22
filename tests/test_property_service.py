from __future__ import annotations

from pathlib import Path

import pytest

from house_index.domain.enums import Condition, PropertyType, Status, TransitKind
from house_index.domain.models import Property, TransitStop
from house_index.services.property_service import PropertyService


@pytest.fixture()
def service(tmp_path: Path) -> PropertyService:
    return PropertyService(tmp_path / "test.db")


def _good_apartment() -> Property:
    return Property(
        title="Brynow 3+kk",
        property_type=PropertyType.APARTMENT,
        price_pln=450_000,
        area_m2=62.0,
        distance_km=3.2,
        rooms=3,
        has_parking_spot=True,
        parking_spot_count=1,
        year_built=2015,
        condition=Condition.STANDARD,
        transit_stops=[TransitStop(kind=TransitKind.TRAM, distance_m=350)],
    )


def _mid_apartment() -> Property:
    return Property(
        title="Ligota",
        property_type=PropertyType.APARTMENT,
        price_pln=620_000,
        area_m2=72.0,
        distance_km=6.5,
        rooms=3,
        has_parking_spot=True,
        parking_spot_count=1,
        year_built=2005,
        condition=Condition.STANDARD,
        transit_stops=[TransitStop(kind=TransitKind.BUS, distance_m=550)],
    )


def _expensive_house() -> Property:
    return Property(
        title="Dom Podlesie",
        property_type=PropertyType.HOUSE,
        price_pln=1_700_000,
        area_m2=180.0,
        distance_km=14.0,
        rooms=5,
        has_garage=True,
        garage_spots=2,
        year_built=2008,
        condition=Condition.TURNKEY,
        has_garden=True,
        garden_m2=400,
    )


def test_first_run_seeds_default_scoring_config(service):
    assert service.scoring_config  # non-empty dict
    assert "price_pln" in service.scoring_config


def test_save_computes_and_persists_index(service):
    prop = _good_apartment()
    pid = service.save(prop)
    assert prop.index_score is not None
    assert prop.index_score > 0

    loaded = service.get(pid)
    assert loaded.index_score == prop.index_score
    assert loaded.index_breakdown is not None


def test_listing_sorted_by_index_desc_by_default(service):
    service.save(_good_apartment())   # highest expected
    service.save(_mid_apartment())    # medium
    service.save(_expensive_house())  # lowest among these

    items = service.list_all()
    scores = [p.index_score for p in items]
    assert scores == sorted(scores, reverse=True)


def test_update_recomputes_index(service):
    prop = _good_apartment()
    pid = service.save(prop)
    before = prop.index_score

    loaded = service.get(pid)
    loaded.price_pln = 1_500_000
    service.save(loaded)

    after = service.get(pid).index_score
    assert after < before


def test_delete_removes(service):
    pid = service.save(_good_apartment())
    service.save(_mid_apartment())

    service.delete(pid)
    remaining = service.list_all()
    assert len(remaining) == 1
    assert remaining[0].id != pid


def test_filter_by_status(service):
    a = _good_apartment()
    a.status = Status.INTERESTED
    service.save(a)

    b = _mid_apartment()
    b.status = Status.REJECTED
    service.save(b)

    interested = service.list_all(status=Status.INTERESTED)
    assert len(interested) == 1
    assert interested[0].title == "Brynow 3+kk"


def test_recompute_all_after_config_change(service):
    service.save(_good_apartment())
    service.save(_mid_apartment())

    before = [p.index_score for p in service.list_all()]

    new_config = service.scoring_config.copy()
    new_config["price_pln"] = {**new_config["price_pln"], "max_points": 60}
    service.save_config(new_config)
    service.recompute_all()

    after = [p.index_score for p in service.list_all()]
    assert after != before
    assert all(a > b for a, b in zip(after, before, strict=True))


def test_settings_round_trip(service):
    assert service.get_setting("lang", "sk") == "sk"
    service.set_setting("lang", "pl")
    assert service.get_setting("lang") == "pl"


def test_eur_rate_default_and_round_trip(service):
    assert service.get_eur_rate() == pytest.approx(0.235)
    service.set_eur_rate(0.231)
    assert service.get_eur_rate() == pytest.approx(0.231)


def test_eur_rate_invalid_falls_back_to_default(service):
    service.set_setting("pln_to_eur_rate", "not-a-number")
    assert service.get_eur_rate() == pytest.approx(0.235)


def test_effective_price_includes_renovation_for_shell(service):
    prop = _good_apartment()
    prop.condition = Condition.SHELL
    pid = service.save(prop)
    loaded = service.get(pid)

    raw = loaded.price_pln
    eff = service.effective_price(loaded)
    assert eff is not None
    assert eff > raw
    assert eff == pytest.approx(raw + loaded.area_m2 * 3500)


def test_effective_price_equals_raw_for_turnkey(service):
    prop = _good_apartment()
    prop.condition = Condition.TURNKEY
    pid = service.save(prop)
    loaded = service.get(pid)

    assert service.effective_price(loaded) == pytest.approx(loaded.price_pln)
