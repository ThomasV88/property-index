from __future__ import annotations

from typing import Any

from PySide6.QtWidgets import (
    QFormLayout,
    QGroupBox,
    QLabel,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from house_index.ui.widgets.bands_editor import (
    BandsTable,
    EnumPointsTable,
    RenovationCostTable,
    make_double_spin,
)


class RuleCard(QGroupBox):
    """Karta pre editáciu jedného pravidla zo scoring_config."""

    def __init__(self, key: str, rule: dict[str, Any], parent: QWidget | None = None):
        label = rule.get("label", key)
        super().__init__(f"{label}  ·  {key}", parent)
        self.key = key
        self._rule_type = rule.get("type", "")
        self._original_rule = rule
        self._renovation_editor: RenovationCostTable | None = None

        layout = QVBoxLayout(self)

        meta_form = QFormLayout()
        meta_form.addRow("Typ pravidla", QLabel(self._rule_type))
        layout.addLayout(meta_form)

        if self._rule_type in ("band_desc", "band_asc"):
            self._build_band_editor(rule, layout)
        elif self._rule_type == "enum":
            self._build_enum_editor(rule, layout)
        elif self._rule_type == "bool":
            self._build_bool_editor(rule, layout)
        elif self._rule_type == "bool_plus_area":
            self._build_bool_plus_area_editor(rule, layout)
        elif self._rule_type == "conditional_bool":
            self._build_conditional_editor(rule, layout)
        else:
            layout.addWidget(QLabel(f"Neznámy typ: {self._rule_type}"))

        if "renovation_cost_per_m2" in rule:
            note = QLabel(
                "Odhadované náklady na dokončenie do stavu <b>turnkey</b>. "
                "Engine pripočíta <i>plocha × odhad</i> k cene pred skórovaním, "
                "takže nehnuteľnosti v horšom stave dostanú nižšie skóre."
            )
            note.setWordWrap(True)
            layout.addWidget(note)
            self._renovation_editor = RenovationCostTable(rule["renovation_cost_per_m2"])
            layout.addWidget(self._renovation_editor)

    def _build_band_editor(self, rule: dict[str, Any], layout: QVBoxLayout) -> None:
        self._max_points = make_double_spin(rule.get("max_points", 0), 0, 200)
        form = QFormLayout()
        form.addRow("Max body", self._max_points)
        layout.addLayout(form)

        if "bands_by_type" in rule:
            self._bands_tables: dict[str, BandsTable] = {}
            tabs = QTabWidget()
            for tkey, bands in rule["bands_by_type"].items():
                table = BandsTable(bands)
                self._bands_tables[tkey] = table
                tabs.addTab(table, tkey)
            layout.addWidget(tabs)
            self._has_bands_by_type = True
        else:
            self._bands_table = BandsTable(rule.get("bands", []))
            layout.addWidget(self._bands_table)
            self._has_bands_by_type = False

    def _build_enum_editor(self, rule: dict[str, Any], layout: QVBoxLayout) -> None:
        self._enum_table = EnumPointsTable(rule.get("points", {}))
        layout.addWidget(self._enum_table)

    def _build_bool_editor(self, rule: dict[str, Any], layout: QVBoxLayout) -> None:
        self._bool_points = make_double_spin(rule.get("points", 0), -100, 100)
        form = QFormLayout()
        form.addRow("Body ak áno (môže byť aj záporné)", self._bool_points)
        layout.addLayout(form)

    def _build_bool_plus_area_editor(self, rule: dict[str, Any], layout: QVBoxLayout) -> None:
        self._base = make_double_spin(rule.get("base", 0), 0, 100)
        self._per_m2 = make_double_spin(rule.get("per_m2", 0), 0, 10, 0.01, 3)
        self._cap = make_double_spin(rule.get("cap", 10), 0, 100)
        form = QFormLayout()
        form.addRow("Základ (keď áno)", self._base)
        form.addRow("Bonus / m²", self._per_m2)
        form.addRow("Strop (cap)", self._cap)
        layout.addLayout(form)

    def _build_conditional_editor(self, rule: dict[str, Any], layout: QVBoxLayout) -> None:
        self._cond_max_points = make_double_spin(rule.get("max_points", 0), 0, 100)
        self._cond_gt = make_double_spin(rule.get("condition_gt", 0), -100, 100)
        form = QFormLayout()
        form.addRow("Max body", self._cond_max_points)
        form.addRow("Podmienka > (hodnota)", self._cond_gt)
        form.addRow("Podmienkové pole", QLabel(rule.get("condition_field", "")))
        form.addRow("Cieľové pole", QLabel(rule.get("target_field", "")))
        layout.addLayout(form)

    def to_rule(self) -> dict[str, Any]:
        rule: dict[str, Any] = {
            "type": self._rule_type,
            "label": self._original_rule.get("label", self.key),
        }
        if "only_for_type" in self._original_rule:
            rule["only_for_type"] = self._original_rule["only_for_type"]

        if self._rule_type in ("band_desc", "band_asc"):
            rule["max_points"] = self._max_points.value()
            if self._has_bands_by_type:
                rule["bands_by_type"] = {k: t.bands() for k, t in self._bands_tables.items()}
            else:
                rule["bands"] = self._bands_table.bands()
        elif self._rule_type == "enum":
            rule["points"] = self._enum_table.points()
        elif self._rule_type == "bool":
            rule["points"] = self._bool_points.value()
        elif self._rule_type == "bool_plus_area":
            rule["base"] = self._base.value()
            rule["per_m2"] = self._per_m2.value()
            rule["cap"] = self._cap.value()
        elif self._rule_type == "conditional_bool":
            rule["max_points"] = self._cond_max_points.value()
            rule["condition_field"] = self._original_rule.get("condition_field", "floor")
            rule["condition_gt"] = self._cond_gt.value()
            rule["target_field"] = self._original_rule.get("target_field", self.key)

        if self._renovation_editor is not None:
            rule["renovation_cost_per_m2"] = self._renovation_editor.cost_map()

        return rule
