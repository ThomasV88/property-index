from __future__ import annotations

import pytest

from house_index.domain.enums import Condition, PropertyType, TransitKind
from house_index.domain.models import Property, TransitStop
from house_index.scoring.defaults import DEFAULT_SCORING_CONFIG
from house_index.scoring.engine import compute, effective_price, estimate_renovation_cost


def _apartment(**overrides) -> Property:
    base = dict(
        title="Test byt",
        property_type=PropertyType.APARTMENT,
        price_pln=450_000,
        area_m2=62.0,
        distance_km=3.2,
        rooms=3,
        floor=2,
        has_elevator=True,
        has_balcony=True,
        has_parking_spot=True,
        parking_spot_count=1,
        year_built=2015,
        condition=Condition.STANDARD,
        transit_stops=[TransitStop(kind=TransitKind.TRAM, distance_m=350)],
    )
    base.update(overrides)
    return Property(**base)


def test_compute_returns_all_breakdown_keys():
    prop = _apartment()
    result = compute(prop, DEFAULT_SCORING_CONFIG)

    assert set(result.breakdown.keys()) == set(DEFAULT_SCORING_CONFIG.keys())
    assert all("label" in b and "points" in b for b in result.breakdown.values())
    assert result.total > 0


def test_compute_is_deterministic():
    prop = _apartment()
    r1 = compute(prop, DEFAULT_SCORING_CONFIG)
    r2 = compute(prop, DEFAULT_SCORING_CONFIG)
    assert r1.total == r2.total
    assert r1.breakdown == r2.breakdown


def test_compute_higher_price_lower_score():
    cheap = _apartment(price_pln=350_000)
    expensive = _apartment(price_pln=1_500_000)

    r_cheap = compute(cheap, DEFAULT_SCORING_CONFIG)
    r_expensive = compute(expensive, DEFAULT_SCORING_CONFIG)

    assert r_cheap.total > r_expensive.total
    assert r_cheap.breakdown["price_pln"]["points"] > r_expensive.breakdown["price_pln"]["points"]


def test_compute_closer_distance_higher_score():
    near = _apartment(distance_km=2.0)
    far = _apartment(distance_km=20.0)

    assert compute(near, DEFAULT_SCORING_CONFIG).total > compute(far, DEFAULT_SCORING_CONFIG).total


def test_compute_apartment_vs_house_uses_correct_price_bands():
    apartment = _apartment(price_pln=900_000, property_type=PropertyType.APARTMENT)
    house = _apartment(price_pln=900_000, property_type=PropertyType.HOUSE)

    a_price = compute(apartment, DEFAULT_SCORING_CONFIG).breakdown["price_pln"]["points"]
    h_price = compute(house, DEFAULT_SCORING_CONFIG).breakdown["price_pln"]["points"]

    assert h_price > a_price


def test_config_change_changes_result_deterministically():
    prop = _apartment()
    r_default = compute(prop, DEFAULT_SCORING_CONFIG)

    modified = {**DEFAULT_SCORING_CONFIG}
    modified["price_pln"] = {
        **DEFAULT_SCORING_CONFIG["price_pln"],
        "max_points": 60,
    }

    r_modified = compute(prop, modified)

    assert r_modified.total > r_default.total
    assert r_modified.breakdown["price_pln"]["points"] > r_default.breakdown["price_pln"]["points"]


def test_missing_values_dont_crash():
    prop = Property(title="Prazdny", property_type=PropertyType.APARTMENT)
    result = compute(prop, DEFAULT_SCORING_CONFIG)
    assert result.total == 0.0
    assert all(b["points"] == 0 for b in result.breakdown.values())


def test_mhd_distance_extracted_per_mode():
    prop = _apartment(
        transit_stops=[
            TransitStop(kind=TransitKind.BUS, distance_m=800),
            TransitStop(kind=TransitKind.TRAM, distance_m=200),
            TransitStop(kind=TransitKind.TRAIN, distance_m=1200),
        ]
    )
    breakdown = compute(prop, DEFAULT_SCORING_CONFIG).breakdown
    assert breakdown["nearest_mhd_m"]["points"] == 6.0
    assert breakdown["nearest_train_m"]["points"] == 2.5
    assert breakdown["nearest_regional_bus_m"]["points"] == 0.0


def test_regional_bus_scored_separately():
    prop = _apartment(
        transit_stops=[
            TransitStop(kind=TransitKind.REGIONAL_BUS, distance_m=400),
        ]
    )
    breakdown = compute(prop, DEFAULT_SCORING_CONFIG).breakdown
    assert breakdown["nearest_regional_bus_m"]["points"] == 3.0
    assert breakdown["nearest_mhd_m"]["points"] == 0.0


def test_amenity_fields_scored():
    prop = _apartment(
        nearest_supermarket_m=250,
        nearest_kindergarten_state_m=400,
        nearest_kindergarten_private_m=1100,
        nearest_hospital_m=3000,
    )
    bd = compute(prop, DEFAULT_SCORING_CONFIG).breakdown
    assert bd["nearest_supermarket_m"]["points"] == 8.0
    assert bd["nearest_kindergarten_state_m"]["points"] == 3.0
    assert bd["nearest_kindergarten_private_m"]["points"] == 1.0
    assert bd["nearest_hospital_m"]["points"] == 1.5


def test_balcony_or_terrace_handles_either():
    a = _apartment(has_balcony=True, has_terrace=False)
    b = _apartment(has_balcony=False, has_terrace=True)
    c = _apartment(has_balcony=False, has_terrace=False)

    assert compute(a, DEFAULT_SCORING_CONFIG).breakdown["balcony_or_terrace"]["points"] == 3
    assert compute(b, DEFAULT_SCORING_CONFIG).breakdown["balcony_or_terrace"]["points"] == 3
    assert compute(c, DEFAULT_SCORING_CONFIG).breakdown["balcony_or_terrace"]["points"] == 0


def test_garden_area_adds_bonus():
    no_garden = _apartment(has_garden=False, garden_m2=None)
    small = _apartment(has_garden=True, garden_m2=20.0)
    large = _apartment(has_garden=True, garden_m2=500.0)

    no_p = compute(no_garden, DEFAULT_SCORING_CONFIG).breakdown["garden"]["points"]
    s_p = compute(small, DEFAULT_SCORING_CONFIG).breakdown["garden"]["points"]
    l_p = compute(large, DEFAULT_SCORING_CONFIG).breakdown["garden"]["points"]

    assert no_p == 0
    assert s_p > 0
    assert l_p >= s_p
    assert l_p <= DEFAULT_SCORING_CONFIG["garden"]["cap"]


def test_conditional_elevator_only_counts_for_high_floors():
    low = _apartment(floor=2, has_elevator=True)
    high_with = _apartment(floor=5, has_elevator=True)
    high_without = _apartment(floor=5, has_elevator=False)

    assert compute(low, DEFAULT_SCORING_CONFIG).breakdown["has_elevator"]["points"] == 0
    assert compute(high_with, DEFAULT_SCORING_CONFIG).breakdown["has_elevator"]["points"] == 5
    assert compute(high_without, DEFAULT_SCORING_CONFIG).breakdown["has_elevator"]["points"] == 0


def test_expected_range_for_good_apartment():
    prop = _apartment(
        nearest_supermarket_m=400,
        nearest_kindergarten_state_m=600,
        nearest_hospital_m=3500,
    )
    result = compute(prop, DEFAULT_SCORING_CONFIG)
    assert 85 <= result.total <= 150


def test_renovation_cost_shell_higher_than_turnkey():
    rule = DEFAULT_SCORING_CONFIG["price_pln"]
    shell = _apartment(condition=Condition.SHELL, area_m2=60.0)
    turnkey = _apartment(condition=Condition.TURNKEY, area_m2=60.0)

    assert estimate_renovation_cost(shell, rule["renovation_cost_per_m2"]) > 0
    assert estimate_renovation_cost(turnkey, rule["renovation_cost_per_m2"]) == 0


def test_effective_price_penalizes_shell_condition():
    shell = _apartment(price_pln=500_000, area_m2=60.0, condition=Condition.SHELL)
    turnkey = _apartment(price_pln=500_000, area_m2=60.0, condition=Condition.TURNKEY)

    shell_score = compute(shell, DEFAULT_SCORING_CONFIG).breakdown["price_pln"]["points"]
    turnkey_score = compute(turnkey, DEFAULT_SCORING_CONFIG).breakdown["price_pln"]["points"]

    assert turnkey_score > shell_score


def test_effective_price_returns_none_when_price_missing():
    prop = _apartment(price_pln=None)
    assert effective_price(prop, DEFAULT_SCORING_CONFIG["price_pln"]) is None


def test_engine_ignores_renovation_when_map_absent():
    rule_no_renov = {**DEFAULT_SCORING_CONFIG["price_pln"]}
    rule_no_renov.pop("renovation_cost_per_m2", None)
    config = {**DEFAULT_SCORING_CONFIG, "price_pln": rule_no_renov}

    shell = _apartment(price_pln=500_000, area_m2=60.0, condition=Condition.SHELL)
    turnkey = _apartment(price_pln=500_000, area_m2=60.0, condition=Condition.TURNKEY)

    assert (
        compute(shell, config).breakdown["price_pln"]["points"]
        == compute(turnkey, config).breakdown["price_pln"]["points"]
    )


def test_room_area_fields_scored():
    prop = _apartment(
        living_room_m2=32.0,
        kitchen_m2=12.0,
        bathroom_largest_m2=7.0,
        bedroom_master_m2=15.0,
    )
    bd = compute(prop, DEFAULT_SCORING_CONFIG).breakdown
    assert bd["living_room_m2"]["points"] == pytest.approx(1.6)
    assert bd["kitchen_m2"]["points"] == pytest.approx(1.0)
    assert bd["bathroom_largest_m2"]["points"] == pytest.approx(0.6)
    assert bd["bedroom_master_m2"]["points"] == pytest.approx(0.6)


def test_pantry_and_wc_scored():
    without = _apartment(has_pantry=False, separate_wc_count=0)
    with_pantry = _apartment(has_pantry=True, separate_wc_count=1)
    two_wc = _apartment(has_pantry=True, separate_wc_count=2)

    bd1 = compute(without, DEFAULT_SCORING_CONFIG).breakdown
    bd2 = compute(with_pantry, DEFAULT_SCORING_CONFIG).breakdown
    bd3 = compute(two_wc, DEFAULT_SCORING_CONFIG).breakdown

    assert bd1["has_pantry"]["points"] == 0
    assert bd1["separate_wc_count"]["points"] == 0
    assert bd2["has_pantry"]["points"] == 1
    assert bd2["separate_wc_count"]["points"] == pytest.approx(0.5)
    assert bd3["separate_wc_count"]["points"] == 1.0


def test_rooms_mapped_as_string_key():
    three = _apartment(rooms=3)
    six = _apartment(rooms=6)
    unknown = _apartment(rooms=99)

    assert compute(three, DEFAULT_SCORING_CONFIG).breakdown["rooms"]["points"] == 8
    assert compute(six, DEFAULT_SCORING_CONFIG).breakdown["rooms"]["points"] == 3
    assert compute(unknown, DEFAULT_SCORING_CONFIG).breakdown["rooms"]["points"] == 0
