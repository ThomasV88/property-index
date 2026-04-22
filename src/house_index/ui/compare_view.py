from __future__ import annotations

from pathlib import Path
from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPixmap
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QScrollArea,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from house_index.domain.enums import (
    CONDITION_LABELS_SK,
    PROPERTY_TYPE_LABELS_SK,
    STATUS_LABELS_SK,
    Condition,
)
from house_index.domain.models import Property
from house_index.ui.utils import fit_to_screen


def _parking_summary(p: Property) -> str:
    parts = []
    if p.has_garage:
        parts.append(f"Garáž ×{p.garage_spots}" if p.garage_spots else "Garáž")
    if p.has_parking_spot:
        parts.append(
            f"Parking ×{p.parking_spot_count}" if p.parking_spot_count else "Parking"
        )
    return " + ".join(parts) if parts else "—"

BEST_COLOR = QColor("#1b9e3f")
WORST_COLOR = QColor("#c94b4b")

Better = "better"
BetterLower = "lower"


def _fmt_price(v: int | None) -> str:
    if v is None:
        return "—"
    return f"{v:,} PLN".replace(",", " ")


ROWS: list[tuple[str, callable, str]] = [
    ("Typ", lambda p: PROPERTY_TYPE_LABELS_SK[p.property_type], ""),
    ("Index", lambda p: p.index_score, Better),
    ("Cena", lambda p: p.price_pln, BetterLower),
    ("Plocha (m²)", lambda p: p.area_m2, Better),
    ("Cena / m²", lambda p: p.price_per_m2, BetterLower),
    ("Vzdialenosť (km)", lambda p: p.distance_km, BetterLower),
    ("Izby", lambda p: p.rooms, Better),
    ("Poschodie", lambda p: p.floor, ""),
    ("Výťah", lambda p: "áno" if p.has_elevator else "nie", ""),
    ("Balkón / terasa", lambda p: "áno" if p.has_balcony or p.has_terrace else "nie", ""),
    ("Záhrada", lambda p: "áno" if p.has_garden else "nie", ""),
    ("Parkovanie", lambda p: _parking_summary(p), ""),
    ("Plocha pozemku (m²)", lambda p: p.plot_m2, Better),
    ("Rok výstavby", lambda p: p.year_built, Better),
    ("Stav", lambda p: CONDITION_LABELS_SK[p.condition] if p.condition else "—", ""),
    ("MHD (m)", lambda p: p.nearest_mhd_m, BetterLower),
    ("Vlak (m)", lambda p: p.nearest_train_m, BetterLower),
    ("Regionálny bus (m)", lambda p: p.nearest_regional_bus_m, BetterLower),
    ("Supermarket (m)", lambda p: p.nearest_supermarket_m, BetterLower),
    ("Štátna škôlka (m)", lambda p: p.nearest_kindergarten_state_m, BetterLower),
    ("Súkromná škôlka (m)", lambda p: p.nearest_kindergarten_private_m, BetterLower),
    ("Nemocnica (m)", lambda p: p.nearest_hospital_m, BetterLower),
    ("Obývačka (m²)", lambda p: p.living_room_m2, Better),
    ("Kuchyňa (m²)", lambda p: p.kitchen_m2, Better),
    ("Najväčšia kúpeľňa (m²)", lambda p: p.bathroom_largest_m2, Better),
    ("Hlavná spálňa (m²)", lambda p: p.bedroom_master_m2, Better),
    ("Špajza", lambda p: "áno" if p.has_pantry else "nie", ""),
    ("Samostatné WC", lambda p: p.separate_wc_count, Better),
    ("Status", lambda p: STATUS_LABELS_SK[p.status], ""),
]


MIN_VISIBLE_TABLE_ROWS = 10
TABLE_ROW_HEIGHT = 30


def rule_max_points(rule: dict[str, Any]) -> float:
    t = rule.get("type")
    if t in ("band_desc", "band_asc", "conditional_bool"):
        return float(rule.get("max_points", 0))
    if t == "bool":
        return abs(float(rule.get("points", 0)))
    if t == "bool_plus_area":
        return float(rule.get("cap", 0))
    if t == "enum":
        pts = rule.get("points", {})
        return max((abs(float(v)) for v in pts.values()), default=0.0)
    return 0.0


def describe_rule_input(prop: Property, key: str, rule: dict[str, Any]) -> str:
    if key == "price_pln":
        if prop.price_pln is None:
            return "—"
        renov_map = rule.get("renovation_cost_per_m2") or {}
        if prop.area_m2 and prop.condition:
            per = float(renov_map.get(prop.condition.value, 0) or 0)
            renov = per * prop.area_m2
            if renov > 0:
                base = f"{prop.price_pln:,}".replace(",", " ")
                r = f"{renov:,.0f}".replace(",", " ")
                return f"{base} PLN + {r} renov."
        return f"{prop.price_pln:,} PLN".replace(",", " ")
    if key == "distance_km":
        return f"{prop.distance_km:g} km" if prop.distance_km is not None else "—"
    if key == "area_m2":
        return f"{prop.area_m2:g} m²" if prop.area_m2 else "—"
    if key == "transit_nearest_m":
        return f"{prop.nearest_transit_m} m" if prop.nearest_transit_m is not None else "žiadna MHD"
    if key == "nearest_mhd_m":
        return f"{prop.nearest_mhd_m} m" if prop.nearest_mhd_m is not None else "žiadna MHD"
    if key == "nearest_train_m":
        return f"{prop.nearest_train_m} m" if prop.nearest_train_m is not None else "žiadny vlak"
    if key == "nearest_regional_bus_m":
        return f"{prop.nearest_regional_bus_m} m" if prop.nearest_regional_bus_m is not None else "žiadny reg. bus"
    if key == "nearest_supermarket_m":
        return f"{prop.nearest_supermarket_m} m" if prop.nearest_supermarket_m is not None else "—"
    if key == "nearest_kindergarten_state_m":
        return f"{prop.nearest_kindergarten_state_m} m" if prop.nearest_kindergarten_state_m is not None else "—"
    if key == "nearest_kindergarten_private_m":
        return f"{prop.nearest_kindergarten_private_m} m" if prop.nearest_kindergarten_private_m is not None else "—"
    if key == "nearest_hospital_m":
        return f"{prop.nearest_hospital_m} m" if prop.nearest_hospital_m is not None else "—"
    if key == "garage":
        return f"Garáž ×{prop.garage_spots}" if prop.has_garage else "bez garáže"
    if key == "parking_spot":
        if prop.has_parking_spot:
            return f"Parkovacie ×{prop.parking_spot_count}"
        return "bez parkovania"
    if key == "plot_m2":
        if prop.property_type.value != "house":
            return "N/A (byt)"
        return f"{prop.plot_m2:g} m²" if prop.plot_m2 else "—"
    if key == "condition":
        return CONDITION_LABELS_SK[prop.condition] if prop.condition else "—"
    if key == "balcony_or_terrace":
        if prop.has_balcony and prop.has_terrace:
            return "balkón + terasa"
        if prop.has_balcony:
            return "balkón"
        if prop.has_terrace:
            return "terasa"
        return "nie"
    if key == "garden":
        if not prop.has_garden:
            return "bez záhrady"
        return f"záhrada {prop.garden_m2:g} m²" if prop.garden_m2 else "záhrada"
    if key == "cellar":
        if not prop.has_cellar:
            return "bez pivnice"
        return f"pivnica {prop.cellar_m2:g} m²" if prop.cellar_m2 else "pivnica"
    if key == "year_built":
        return str(prop.year_built) if prop.year_built else "—"
    if key == "has_elevator":
        floor = prop.floor
        if floor is None or floor <= 3:
            return f"{floor or '—'}. posch. (výťah nerelevantný)"
        return f"{floor}. posch. · {'výťah' if prop.has_elevator else 'bez výťahu'}"
    if key == "rooms":
        return f"{prop.rooms} izieb" if prop.rooms else "—"
    if key == "multi_floor":
        return "áno" if prop.multi_floor else "nie"
    if key == "living_room_m2":
        return f"{prop.living_room_m2:g} m²" if prop.living_room_m2 else "—"
    if key == "kitchen_m2":
        return f"{prop.kitchen_m2:g} m²" if prop.kitchen_m2 else "—"
    if key == "bathroom_largest_m2":
        return f"{prop.bathroom_largest_m2:g} m²" if prop.bathroom_largest_m2 else "—"
    if key == "bedroom_master_m2":
        return f"{prop.bedroom_master_m2:g} m²" if prop.bedroom_master_m2 else "—"
    if key == "has_pantry":
        return "áno" if prop.has_pantry else "nie"
    if key == "separate_wc_count":
        return f"{prop.separate_wc_count}×" if prop.separate_wc_count else "0"
    return "—"


class CompareDialog(QDialog):
    def __init__(
        self,
        properties: list[Property],
        photos_dir: Path,
        parent: QWidget | None = None,
        scoring_config: dict[str, dict[str, Any]] | None = None,
    ):
        super().__init__(parent)
        self.setWindowTitle(f"Porovnanie ({len(properties)} nehnuteľností)")
        self.resize(1100, 860)
        self._properties = properties
        self._photos_dir = photos_dir
        self._scoring_config = scoring_config or {}

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        outer.addWidget(scroll, 1)

        content = QWidget()
        scroll.setWidget(content)
        layout = QVBoxLayout(content)

        layout.addWidget(self._build_header_row())
        layout.addWidget(self._build_table())
        layout.addWidget(self._build_scoring_table())
        layout.addWidget(self._build_breakdown())
        layout.addStretch(1)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.reject)
        buttons.accepted.connect(self.accept)
        outer.addWidget(buttons)

    def showEvent(self, event) -> None:  # noqa: N802
        super().showEvent(event)
        fit_to_screen(self, margin=50)

    def _build_header_row(self) -> QWidget:
        container = QWidget()
        container.setMaximumHeight(220)
        row = QHBoxLayout(container)
        for p in self._properties:
            col = QVBoxLayout()
            primary = p.primary_photo
            if primary is not None:
                pm = QPixmap(str(self._photos_dir / primary.file_name))
                if not pm.isNull():
                    pm = pm.scaled(220, 160, Qt.AspectRatioMode.KeepAspectRatio,
                                   Qt.TransformationMode.SmoothTransformation)
                    img = QLabel()
                    img.setPixmap(pm)
                    col.addWidget(img)
            title = QLabel(p.title)
            tf = title.font()
            tf.setBold(True)
            title.setFont(tf)
            col.addWidget(title)
            col.addStretch(1)
            w = QWidget()
            w.setLayout(col)
            row.addWidget(w, 1)
        return container

    def _build_table(self) -> QWidget:
        box = QGroupBox("Parametre")
        outer = QVBoxLayout(box)
        props = self._properties
        table = QTableWidget(len(ROWS), len(props) + 1, self)
        headers = ["Parameter"] + [p.title for p in props]
        table.setHorizontalHeaderLabels(headers)
        table.verticalHeader().setVisible(False)
        table.verticalHeader().setDefaultSectionSize(TABLE_ROW_HEIGHT)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        table.setAlternatingRowColors(True)
        table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        for r, (label, getter, direction) in enumerate(ROWS):
            table.setItem(r, 0, QTableWidgetItem(label))
            values = [getter(p) for p in props]
            numeric_values = [v for v in values if isinstance(v, (int, float))]
            best = worst = None
            if direction and len(numeric_values) > 1:
                if direction == Better:
                    best = max(numeric_values)
                    worst = min(numeric_values)
                elif direction == BetterLower:
                    best = min(numeric_values)
                    worst = max(numeric_values)

            for c, v in enumerate(values, start=1):
                display = self._format_value(label, v)
                item = QTableWidgetItem(display)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                if direction and isinstance(v, (int, float)) and best is not None:
                    if v == best and v != worst:
                        item.setBackground(BEST_COLOR)
                        item.setForeground(QColor("#ffffff"))
                    elif v == worst and v != best:
                        item.setBackground(WORST_COLOR)
                        item.setForeground(QColor("#ffffff"))
                table.setItem(r, c, item)

        for r in range(table.rowCount()):
            table.setRowHeight(r, TABLE_ROW_HEIGHT)

        header_h = table.horizontalHeader().sizeHint().height() + 4
        total = header_h + len(ROWS) * TABLE_ROW_HEIGHT + 4
        table.setMinimumHeight(total)
        table.setFixedHeight(total)
        outer.addWidget(table)
        return box

    def _format_value(self, label: str, value) -> str:
        if value is None:
            return "—"
        if label == "Cena":
            return _fmt_price(value)
        if label == "Cena / m²":
            return f"{value:,.0f} PLN/m²".replace(",", " ")
        if label == "Index":
            return f"{value:.1f}"
        if label == "Plocha (m²)":
            return f"{value:g}"
        if label == "Vzdialenosť (km)":
            return f"{value:g}"
        if label in ("MHD (m)", "Vlak (m)", "Regionálny bus (m)", "Supermarket (m)",
                     "Štátna škôlka (m)", "Súkromná škôlka (m)", "Nemocnica (m)"):
            return f"{value} m"
        if label in ("Obývačka (m²)", "Kuchyňa (m²)", "Najväčšia kúpeľňa (m²)",
                     "Hlavná spálňa (m²)", "Plocha pozemku (m²)"):
            return f"{value:g} m²"
        if label == "Samostatné WC":
            return f"{value}×" if value else "0"
        return str(value)

    def _build_scoring_table(self) -> QWidget:
        box = QGroupBox("Bodovanie — prečo má nehnuteľnosť takéto skóre")
        layout = QVBoxLayout(box)
        props = self._properties
        cfg = self._scoring_config

        if not cfg:
            layout.addWidget(QLabel("Scoring config nedostupný."))
            return box

        rule_keys = list(cfg.keys())
        n_cols = 2 + 2 * len(props)
        table = QTableWidget(len(rule_keys) + 1, n_cols, self)

        headers = ["Pravidlo", "Max"]
        for p in props:
            headers.append(f"{p.title}\n(hodnota)")
            headers.append(f"{p.title}\n(body)")
        table.setHorizontalHeaderLabels(headers)
        table.verticalHeader().setVisible(False)
        table.verticalHeader().setDefaultSectionSize(TABLE_ROW_HEIGHT + 6)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        table.setAlternatingRowColors(True)
        table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        totals = [0.0 for _ in props]

        for r, key in enumerate(rule_keys):
            rule = cfg[key]
            label = rule.get("label", key)
            max_p = rule_max_points(rule)

            table.setItem(r, 0, QTableWidgetItem(label))
            max_item = QTableWidgetItem(f"{max_p:.1f}")
            max_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            table.setItem(r, 1, max_item)

            points_per_prop: list[float | None] = []
            for c, p in enumerate(props):
                val_desc = describe_rule_input(p, key, rule)
                info = (p.index_breakdown or {}).get(key)
                pts = float(info["points"]) if info else 0.0
                points_per_prop.append(pts)
                totals[c] += pts

                col_val = 2 + 2 * c
                col_pts = col_val + 1

                v_item = QTableWidgetItem(val_desc)
                v_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                table.setItem(r, col_val, v_item)

                frac = pts / max_p if max_p > 0 else 0
                p_item = QTableWidgetItem(f"{pts:.1f} / {max_p:.0f}")
                p_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                if pts < 0:
                    p_item.setBackground(QColor("#f5c2c2"))
                elif max_p > 0:
                    if frac >= 0.9:
                        p_item.setBackground(QColor("#d4edda"))
                    elif frac >= 0.5:
                        p_item.setBackground(QColor("#fff4cd"))
                    elif pts > 0:
                        p_item.setBackground(QColor("#fde2e2"))
                    else:
                        p_item.setBackground(QColor("#f0f0f0"))
                table.setItem(r, col_pts, p_item)

            if len(points_per_prop) > 1 and max_p > 0:
                numeric = [v for v in points_per_prop if v is not None]
                best = max(numeric)
                worst = min(numeric)
                for c, pts in enumerate(points_per_prop):
                    if pts is None:
                        continue
                    col_pts = 2 + 2 * c + 1
                    item = table.item(r, col_pts)
                    if pts == best and pts != worst:
                        item.setForeground(QColor("#0a5a1b"))
                        f = item.font()
                        f.setBold(True)
                        item.setFont(f)
                    elif pts == worst and pts != best:
                        item.setForeground(QColor("#8a1f1f"))

        total_row = len(rule_keys)
        total_label = QTableWidgetItem("CELKOVÝ INDEX")
        tf = total_label.font()
        tf.setBold(True)
        total_label.setFont(tf)
        table.setItem(total_row, 0, total_label)
        table.setItem(total_row, 1, QTableWidgetItem(""))
        for c, p in enumerate(props):
            col_val = 2 + 2 * c
            col_pts = col_val + 1
            table.setItem(total_row, col_val, QTableWidgetItem(""))
            score = p.index_score if p.index_score is not None else totals[c]
            item = QTableWidgetItem(f"{score:.1f}")
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            f = item.font()
            f.setBold(True)
            f.setPointSize(f.pointSize() + 1)
            item.setFont(f)
            table.setItem(total_row, col_pts, item)

        row_h = TABLE_ROW_HEIGHT + 6
        header_h = table.horizontalHeader().sizeHint().height() + 8
        total = header_h + (len(rule_keys) + 1) * row_h + 4
        table.setFixedHeight(total)
        layout.addWidget(table)

        legend = QLabel(
            "<span style='color:#0a5a1b;'><b>zelené = najlepší</b></span>  ·  "
            "<span style='color:#8a1f1f;'>červené = najhorší</span>  ·  "
            "Pozadie bunky: <span style='background:#d4edda;'>≥90 %</span> "
            "<span style='background:#fff4cd;'>≥50 %</span> "
            "<span style='background:#fde2e2;'>&lt;50 %</span> "
            "<span style='background:#f0f0f0;'>0</span>"
        )
        legend.setTextFormat(Qt.TextFormat.RichText)
        layout.addWidget(legend)
        return box

    def _build_breakdown(self) -> QWidget:
        box = QGroupBox("Krátky súhrn bodov")
        outer = QHBoxLayout(box)
        for p in self._properties:
            col = QVBoxLayout()
            title = QLabel(
                f"{p.title} · index {p.index_score:.1f}"
                if p.index_score is not None
                else p.title
            )
            f = title.font()
            f.setBold(True)
            title.setFont(f)
            col.addWidget(title)
            breakdown = p.index_breakdown or {}
            for key, info in breakdown.items():
                col.addWidget(QLabel(f"{info.get('label', key)}: {info['points']:.1f} b"))
            col.addStretch(1)
            w = QWidget()
            w.setLayout(col)
            outer.addWidget(w, 1)
        return box
