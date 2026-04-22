from __future__ import annotations

from typing import Any

DEFAULT_SCORING_CONFIG: dict[str, dict[str, Any]] = {
    "price_pln": {
        "type": "band_desc",
        "label": "Cena (s odhadom renovácie)",
        "max_points": 30,
        "renovation_cost_per_m2": {
            "turnkey": 0,
            "standard": 800,
            "shell": 3500,
        },
        "bands_by_type": {
            "apartment": [
                [400_000, 1.0],
                [600_000, 0.75],
                [800_000, 0.50],
                [1_000_000, 0.25],
            ],
            "house": [
                [800_000, 1.0],
                [1_200_000, 0.75],
                [1_800_000, 0.50],
                [2_500_000, 0.25],
            ],
        },
    },
    "distance_km": {
        "type": "band_desc",
        "label": "Vzdialenosť od centra Katowíc",
        "max_points": 25,
        "bands": [
            [3, 1.0],
            [6, 0.8],
            [10, 0.55],
            [15, 0.3],
        ],
    },
    "area_m2": {
        "type": "band_asc",
        "label": "Plocha",
        "max_points": 15,
        "bands": [
            [40, 0.3],
            [55, 0.6],
            [70, 0.85],
            [90, 1.0],
        ],
    },
    "nearest_mhd_m": {
        "type": "band_desc",
        "label": "Najbližšia MHD (bus/tram)",
        "max_points": 6,
        "bands": [
            [300, 1.0],
            [600, 0.75],
            [1000, 0.5],
            [1500, 0.25],
        ],
    },
    "nearest_train_m": {
        "type": "band_desc",
        "label": "Najbližšia vlaková stanica",
        "max_points": 5,
        "bands": [
            [500, 1.0],
            [1000, 0.75],
            [2000, 0.5],
            [3000, 0.25],
        ],
    },
    "nearest_regional_bus_m": {
        "type": "band_desc",
        "label": "Najbližší regionálny bus",
        "max_points": 3,
        "bands": [
            [500, 1.0],
            [1000, 0.75],
            [2000, 0.5],
            [3000, 0.25],
        ],
    },
    "nearest_supermarket_m": {
        "type": "band_desc",
        "label": "Najbližší supermarket",
        "max_points": 8,
        "bands": [
            [300, 1.0],
            [800, 0.75],
            [1500, 0.5],
            [2500, 0.25],
        ],
    },
    "nearest_kindergarten_state_m": {
        "type": "band_desc",
        "label": "Najbližšia štátna škôlka",
        "max_points": 3,
        "bands": [
            [500, 1.0],
            [1000, 0.75],
            [2000, 0.5],
            [3000, 0.25],
        ],
    },
    "nearest_kindergarten_private_m": {
        "type": "band_desc",
        "label": "Najbližšia súkromná škôlka",
        "max_points": 2,
        "bands": [
            [500, 1.0],
            [1000, 0.75],
            [2000, 0.5],
            [3000, 0.25],
        ],
    },
    "nearest_hospital_m": {
        "type": "band_desc",
        "label": "Najbližšia nemocnica",
        "max_points": 2,
        "bands": [
            [2000, 1.0],
            [5000, 0.75],
            [10000, 0.5],
            [15000, 0.25],
        ],
    },
    "garage": {
        "type": "bool_plus_area",
        "label": "Garáž",
        "base": 6,
        "per_m2": 1.0,
        "cap": 8,
    },
    "parking_spot": {
        "type": "bool_plus_area",
        "label": "Parkovacie miesto",
        "base": 3,
        "per_m2": 1.0,
        "cap": 5,
    },
    "plot_m2": {
        "type": "band_asc",
        "label": "Plocha pozemku (iba dom)",
        "max_points": 8,
        "only_for_type": "house",
        "bands": [
            [200, 0.3],
            [400, 0.6],
            [700, 0.85],
            [1000, 1.0],
        ],
    },
    "condition": {
        "type": "enum",
        "label": "Stav nehnuteľnosti",
        "points": {"turnkey": 6, "standard": 4, "shell": 1},
    },
    "balcony_or_terrace": {
        "type": "bool",
        "label": "Balkón alebo terasa",
        "points": 3,
    },
    "garden": {
        "type": "bool_plus_area",
        "label": "Záhrada",
        "base": 2,
        "per_m2": 0.05,
        "cap": 6,
    },
    "cellar": {
        "type": "bool_plus_area",
        "label": "Pivnica",
        "base": 1,
        "per_m2": 0.1,
        "cap": 4,
    },
    "year_built": {
        "type": "band_asc",
        "label": "Rok výstavby",
        "max_points": 5,
        "bands": [
            [1960, 0.2],
            [1990, 0.5],
            [2010, 0.8],
            [2020, 1.0],
        ],
    },
    "has_elevator": {
        "type": "conditional_bool",
        "label": "Výťah (ak je poschodie > 3)",
        "max_points": 5,
        "condition_field": "floor",
        "condition_gt": 3,
        "target_field": "has_elevator",
    },
    "rooms": {
        "type": "enum",
        "label": "Počet izieb",
        "points": {"1": 2, "2": 5, "3": 8, "4": 7, "5": 5, "6": 3},
    },
    "multi_floor": {
        "type": "bool",
        "label": "Viacpodlažnosť (±, podľa preferencie)",
        "points": 0,
    },
    "living_room_m2": {
        "type": "band_asc",
        "label": "Plocha obývačky",
        "max_points": 2,
        "bands": [
            [15, 0.3],
            [20, 0.5],
            [30, 0.8],
            [40, 1.0],
        ],
    },
    "kitchen_m2": {
        "type": "band_asc",
        "label": "Plocha kuchyne",
        "max_points": 2,
        "bands": [
            [6, 0.3],
            [10, 0.5],
            [15, 0.8],
            [20, 1.0],
        ],
    },
    "bathroom_largest_m2": {
        "type": "band_asc",
        "label": "Plocha najväčšej kúpeľne",
        "max_points": 1,
        "bands": [
            [4, 0.3],
            [6, 0.6],
            [8, 0.85],
            [10, 1.0],
        ],
    },
    "bedroom_master_m2": {
        "type": "band_asc",
        "label": "Plocha hlavnej spálne",
        "max_points": 1,
        "bands": [
            [10, 0.3],
            [14, 0.6],
            [18, 0.85],
            [22, 1.0],
        ],
    },
    "has_pantry": {
        "type": "bool",
        "label": "Špajza",
        "points": 1,
    },
    "separate_wc_count": {
        "type": "band_asc",
        "label": "Počet samostatných WC",
        "max_points": 1,
        "bands": [
            [1, 0.5],
            [2, 1.0],
        ],
    },
}
