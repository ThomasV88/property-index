from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from house_index.domain.models import Property
from house_index.scoring import rules


@dataclass
class IndexResult:
    total: float
    breakdown: dict[str, dict[str, Any]] = field(default_factory=dict)


def _extract_value(prop: Property, key: str) -> Any:
    if key == "transit_nearest_m":
        return prop.nearest_transit_m
    if key == "nearest_mhd_m":
        return prop.nearest_mhd_m
    if key == "nearest_train_m":
        return prop.nearest_train_m
    if key == "nearest_regional_bus_m":
        return prop.nearest_regional_bus_m
    if key == "balcony_or_terrace":
        return prop.has_balcony or prop.has_terrace
    if key == "garden":
        return prop.has_garden
    if key == "cellar":
        return prop.has_cellar
    if key == "rooms":
        return str(prop.rooms) if prop.rooms is not None else None
    return getattr(prop, key, None)


def estimate_renovation_cost(prop: Property, renovation_map: dict[str, float] | None) -> float:
    if not renovation_map or prop.area_m2 is None or prop.condition is None:
        return 0.0
    per_m2 = float(renovation_map.get(prop.condition.value, 0) or 0)
    return per_m2 * prop.area_m2


def effective_price(prop: Property, rule: dict[str, Any]) -> float | None:
    if prop.price_pln is None:
        return None
    renov = estimate_renovation_cost(prop, rule.get("renovation_cost_per_m2"))
    return prop.price_pln + renov


def _apply_rule(prop: Property, key: str, rule: dict[str, Any]) -> float:
    only_for = rule.get("only_for_type")
    if only_for and prop.property_type.value != only_for:
        return 0.0

    rule_type = rule["type"]

    if rule_type == "band_desc":
        if key == "price_pln":
            value = effective_price(prop, rule)
        else:
            value = _extract_value(prop, key)
        bands = _resolve_bands(prop, rule)
        return rules.band_desc(value, rule["max_points"], bands)

    if rule_type == "band_asc":
        value = _extract_value(prop, key)
        bands = _resolve_bands(prop, rule)
        return rules.band_asc(value, rule["max_points"], bands)

    if rule_type == "enum":
        value = _extract_value(prop, key)
        value_str = value.value if hasattr(value, "value") else (str(value) if value is not None else None)
        return rules.enum_score(value_str, rule["points"])

    if rule_type == "bool":
        return rules.bool_score(_extract_value(prop, key), rule["points"])

    if rule_type == "bool_plus_area":
        if key == "garden":
            return rules.bool_plus_area_score(
                prop.has_garden, prop.garden_m2, rule["base"], rule["per_m2"], rule["cap"]
            )
        if key == "cellar":
            return rules.bool_plus_area_score(
                prop.has_cellar, prop.cellar_m2, rule["base"], rule["per_m2"], rule["cap"]
            )
        if key == "garage":
            return rules.bool_plus_area_score(
                prop.has_garage, prop.garage_spots, rule["base"], rule["per_m2"], rule["cap"]
            )
        if key == "parking_spot":
            return rules.bool_plus_area_score(
                prop.has_parking_spot, prop.parking_spot_count,
                rule["base"], rule["per_m2"], rule["cap"]
            )
        return 0.0

    if rule_type == "conditional_bool":
        cond_field = rule.get("condition_field", "floor")
        cond_gt = rule.get("condition_gt", 0)
        target_field = rule.get("target_field", key)
        cond_value = getattr(prop, cond_field, None)
        target_value = getattr(prop, target_field, False)
        cond_met = (lambda v: v is not None and v > cond_gt)
        return rules.conditional_bool_score(cond_value, cond_met, target_value, rule["max_points"])

    return 0.0


def _resolve_bands(prop: Property, rule: dict[str, Any]) -> list[list[float]]:
    if "bands_by_type" in rule:
        by_type = rule["bands_by_type"]
        return by_type.get(prop.property_type.value, next(iter(by_type.values())))
    return rule["bands"]


def compute(prop: Property, config: dict[str, dict[str, Any]]) -> IndexResult:
    breakdown: dict[str, dict[str, Any]] = {}
    total = 0.0
    for key, rule in config.items():
        points = _apply_rule(prop, key, rule)
        total += points
        breakdown[key] = {
            "label": rule.get("label", key),
            "points": round(points, 2),
        }
    return IndexResult(total=round(total, 2), breakdown=breakdown)
