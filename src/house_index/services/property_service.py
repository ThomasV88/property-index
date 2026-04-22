from __future__ import annotations

import copy
from pathlib import Path
from typing import Any, Callable

from house_index.db import repository as repo
from house_index.db.repository import open_connection
from house_index.domain.enums import Status
from house_index.domain.models import Property
from house_index.scoring.defaults import DEFAULT_SCORING_CONFIG
from house_index.scoring.engine import compute
from house_index.scoring.recompute import recompute_all


class PropertyService:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._scoring_config: dict[str, Any] = {}
        repo.initialize(db_path)
        self._load_or_seed_config()

    def _load_or_seed_config(self) -> None:
        with open_connection(self.db_path) as conn:
            cfg = repo.get_active_config(conn)
            if cfg is None:
                cfg = copy.deepcopy(DEFAULT_SCORING_CONFIG)
                repo.save_active_config(conn, "default", cfg)
            else:
                cfg = self._merge_new_defaults(cfg)
            self._scoring_config = cfg

    @staticmethod
    def _merge_new_defaults(cfg: dict[str, Any]) -> dict[str, Any]:
        price = cfg.get("price_pln")
        if isinstance(price, dict) and "renovation_cost_per_m2" not in price:
            price["renovation_cost_per_m2"] = copy.deepcopy(
                DEFAULT_SCORING_CONFIG["price_pln"]["renovation_cost_per_m2"]
            )

        cfg.pop("transit_nearest_m", None)
        for key in (
            "nearest_mhd_m",
            "nearest_train_m",
            "nearest_regional_bus_m",
            "nearest_supermarket_m",
            "nearest_kindergarten_state_m",
            "nearest_kindergarten_private_m",
            "nearest_hospital_m",
            "multi_floor",
            "living_room_m2",
            "kitchen_m2",
            "bathroom_largest_m2",
            "bedroom_master_m2",
            "has_pantry",
            "separate_wc_count",
        ):
            if key not in cfg:
                cfg[key] = copy.deepcopy(DEFAULT_SCORING_CONFIG[key])

        return cfg

    @property
    def scoring_config(self) -> dict[str, Any]:
        return self._scoring_config

    def list_all(
        self,
        status: Status | None = None,
        order_by: str | None = None,
    ) -> list[Property]:
        with open_connection(self.db_path) as conn:
            if order_by is None:
                return repo.list_properties(conn, status=status)
            return repo.list_properties(conn, order_by=order_by, status=status)

    def get(self, property_id: int) -> Property | None:
        with open_connection(self.db_path) as conn:
            return repo.get_property(conn, property_id)

    def save(self, prop: Property) -> int:
        result = compute(prop, self._scoring_config)
        prop.index_score = result.total
        prop.index_breakdown = result.breakdown
        with open_connection(self.db_path) as conn:
            return repo.save_property(conn, prop)

    def delete(self, property_id: int) -> None:
        with open_connection(self.db_path) as conn:
            repo.delete_property(conn, property_id)

    def save_config(self, config: dict[str, Any], name: str = "custom") -> None:
        with open_connection(self.db_path) as conn:
            repo.save_active_config(conn, name, config)
        self._scoring_config = config

    def recompute_all(self, progress: Callable[[int, int], None] | None = None) -> int:
        with open_connection(self.db_path) as conn:
            return recompute_all(conn, self._scoring_config, progress)

    def all_tags(self) -> list[str]:
        with open_connection(self.db_path) as conn:
            return repo.list_all_tags(conn)

    def get_setting(self, key: str, default: str | None = None) -> str | None:
        with open_connection(self.db_path) as conn:
            return repo.get_setting(conn, key, default)

    def set_setting(self, key: str, value: str) -> None:
        with open_connection(self.db_path) as conn:
            repo.set_setting(conn, key, value)

    def get_eur_rate(self) -> float:
        raw = self.get_setting("pln_to_eur_rate", "0.235")
        try:
            val = float(raw.replace(",", "."))
            return val if val > 0 else 0.235
        except (ValueError, AttributeError):
            return 0.235

    def set_eur_rate(self, rate: float) -> None:
        self.set_setting("pln_to_eur_rate", f"{rate:.4f}")

    def renovation_cost_estimate(self, prop: Property) -> float:
        rule = self._scoring_config.get("price_pln", {})
        from house_index.scoring.engine import estimate_renovation_cost
        return estimate_renovation_cost(prop, rule.get("renovation_cost_per_m2"))

    def effective_price(self, prop: Property) -> float | None:
        if prop.price_pln is None:
            return None
        return prop.price_pln + self.renovation_cost_estimate(prop)
