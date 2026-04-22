from __future__ import annotations

from typing import Any


def band_desc(value: float | None, max_points: float, bands: list[list[float]]) -> float:
    """Menšia hodnota = lepšie (cena, vzdialenosť).

    Bands: zoznam [threshold, multiplier] zoradený ASC podľa threshold.
    Vráti max_points * multiplier pre prvé pásmo, kde value <= threshold.
    Nad najvyšším pásmom → 0.
    """
    if value is None:
        return 0.0
    for threshold, mult in bands:
        if value <= threshold:
            return max_points * mult
    return 0.0


def band_asc(value: float | None, max_points: float, bands: list[list[float]]) -> float:
    """Väčšia hodnota = lepšie (plocha, rok výstavby).

    Bands: zoznam [threshold, multiplier] zoradený ASC podľa threshold.
    Vráti max_points * multiplier najvyššieho pásma, kde value >= threshold.
    Pod najnižším pásmom → 0.
    """
    if value is None:
        return 0.0
    best = 0.0
    for threshold, mult in bands:
        if value >= threshold:
            best = max_points * mult
    return best


def enum_score(value: str | None, points_map: dict[str, float]) -> float:
    if value is None:
        return 0.0
    return float(points_map.get(value, 0.0))


def bool_score(value: Any, points: float) -> float:
    return float(points) if bool(value) else 0.0


def bool_plus_area_score(
    has: Any, area: float | None, base: float, per_m2: float, cap: float
) -> float:
    if not has:
        return 0.0
    area_val = area or 0.0
    return min(base + per_m2 * area_val, cap)


def conditional_bool_score(
    condition_value: Any,
    condition_met: Any,
    target_value: Any,
    points: float,
) -> float:
    """Ak je podmienka splnená a cieľ je pravdivý → body; ak podmienka nie je splnená → 0 (neutrálne)."""
    if not condition_met(condition_value):
        return 0.0
    return float(points) if bool(target_value) else 0.0
