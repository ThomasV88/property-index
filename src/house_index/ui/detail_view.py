from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QDesktopServices, QPixmap
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)
from PySide6.QtCore import QUrl

from house_index.domain.enums import (
    CONDITION_LABELS_SK,
    PROPERTY_TYPE_LABELS_SK,
    PropertyType,
    STATUS_LABELS_SK,
    TRANSIT_LABELS_SK,
)
from house_index.domain.models import Property
from house_index.services.property_service import PropertyService
from house_index.ui.card_delegate import STATUS_COLORS, index_color
from house_index.ui.utils import fit_to_screen


def _parking_summary(p: Property) -> str:
    parts = []
    if p.has_garage:
        parts.append(f"Garáž ×{p.garage_spots}" if p.garage_spots else "Garáž")
    if p.has_parking_spot:
        parts.append(
            f"Parkovacie miesto ×{p.parking_spot_count}" if p.parking_spot_count else "Parkovacie miesto"
        )
    return " + ".join(parts) if parts else "—"

MAX_PREVIEW_PHOTO = 300


def _dt(value, suffix: str = "", fmt: str = "{}") -> str:
    if value is None:
        return "—"
    return fmt.format(value) + (f" {suffix}" if suffix else "")


def _yes_no(value: bool) -> str:
    return "áno" if value else "nie"


class PropertyDetailDialog(QDialog):
    edit_requested = None

    def __init__(
        self,
        prop: Property,
        photos_dir: Path,
        parent: QWidget | None = None,
        service: PropertyService | None = None,
    ):
        super().__init__(parent)
        self._property = prop
        self._photos_dir = photos_dir
        self._service = service
        self.setWindowTitle(prop.title)
        self.resize(900, 720)
        self._edit_requested = False

        outer = QVBoxLayout(self)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        outer.addWidget(scroll, 1)

        content = QWidget()
        scroll.setWidget(content)
        content_layout = QVBoxLayout(content)

        content_layout.addWidget(self._build_header())
        content_layout.addWidget(self._build_photos_row())
        content_layout.addWidget(self._build_params_grid())
        content_layout.addWidget(self._build_breakdown_panel())
        content_layout.addWidget(self._build_links_panel())
        content_layout.addWidget(self._build_transit_panel())
        content_layout.addWidget(self._build_tags_panel())
        content_layout.addWidget(self._build_notes_panel())
        content_layout.addStretch(1)

        buttons = QDialogButtonBox()
        edit_btn = QPushButton("Upraviť")
        edit_btn.clicked.connect(self._on_edit)
        buttons.addButton(edit_btn, QDialogButtonBox.ButtonRole.ActionRole)
        close_btn = buttons.addButton(QDialogButtonBox.StandardButton.Close)
        close_btn.clicked.connect(self.reject)
        outer.addWidget(buttons)

    def showEvent(self, event) -> None:  # noqa: N802
        super().showEvent(event)
        fit_to_screen(self, margin=50)

    def edit_requested_flag(self) -> bool:
        return self._edit_requested

    def _on_edit(self) -> None:
        self._edit_requested = True
        self.accept()

    def _build_header(self) -> QWidget:
        box = QWidget()
        layout = QHBoxLayout(box)

        title = QLabel(self._property.title)
        f = title.font()
        f.setPointSize(18)
        f.setBold(True)
        title.setFont(f)
        layout.addWidget(title, 1)

        score = self._property.index_score
        badge = QLabel(f"{score:.1f}" if score is not None else "—")
        badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        badge.setMinimumSize(90, 60)
        color = index_color(score).name()
        badge_font = badge.font()
        badge_font.setPointSize(22)
        badge_font.setBold(True)
        badge.setFont(badge_font)
        badge.setStyleSheet(
            f"background-color: {color}; color: #fff; border-radius: 8px; padding: 4px 8px;"
        )
        layout.addWidget(badge)

        status_color = STATUS_COLORS[self._property.status]
        status = QLabel(STATUS_LABELS_SK[self._property.status])
        status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        status.setStyleSheet(
            f"background-color: {status_color}; color: #ffffff; border-radius: 10px; "
            "padding: 6px 14px;"
        )
        status.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Preferred)
        layout.addWidget(status)

        return box

    def _build_photos_row(self) -> QWidget:
        box = QGroupBox("Fotky")
        layout = QHBoxLayout(box)
        layout.setAlignment(Qt.AlignmentFlag.AlignLeft)

        if not self._property.photos:
            layout.addWidget(QLabel("Žiadne fotky."))
            return box

        for photo in self._property.photos[:6]:
            path = self._photos_dir / photo.file_name
            pm = QPixmap(str(path))
            if pm.isNull():
                continue
            scaled = pm.scaled(
                MAX_PREVIEW_PHOTO, MAX_PREVIEW_PHOTO,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            lbl = QLabel()
            lbl.setPixmap(scaled)
            if photo.is_primary:
                lbl.setStyleSheet("border: 2px solid #f0a030; border-radius: 4px;")
            layout.addWidget(lbl)
        return box

    def _build_params_grid(self) -> QWidget:
        p = self._property
        box = QGroupBox("Parametre")
        grid = QGridLayout(box)
        grid.setHorizontalSpacing(24)

        eur_rate = self._service.get_eur_rate() if self._service else 0.235
        renov_cost = self._service.renovation_cost_estimate(p) if self._service else 0.0
        eff_price = self._service.effective_price(p) if self._service else None

        price_pln_text = f"{p.price_pln:,}".replace(",", " ") if p.price_pln else None
        price_eur_text = (
            f"{p.price_pln * eur_rate:,.0f}".replace(",", " ") if p.price_pln and eur_rate else None
        )
        eff_text = None
        if p.price_pln and renov_cost > 0:
            eff_text = (
                f"{eff_price:,.0f}".replace(",", " ")
                + f" PLN (+{renov_cost:,.0f} renov.)".replace(",", " ")
            )

        rows: list[tuple[str, str]] = [
            ("Typ", PROPERTY_TYPE_LABELS_SK[p.property_type] + (" · viacpodlažné" if p.multi_floor else "")),
            ("Cena", _dt(price_pln_text, "PLN")),
            ("Cena (EUR)", _dt(price_eur_text, "EUR")),
        ]
        if eff_text is not None:
            rows.append(("Efektívna cena (skórovaná)", eff_text))
        rows += [
            ("Plocha", _dt(p.area_m2, "m²")),
            ("Cena / m²", _dt(f"{p.price_per_m2:,.0f}".replace(",", " ") if p.price_per_m2 else None, "PLN/m²")),
            ("Vzdialenosť od centra", _dt(p.distance_km, "km")),
            ("Počet izieb", _dt(p.rooms, "izieb")),
            ("Poschodie", _dt(p.floor)),
            ("Výťah", _yes_no(p.has_elevator)),
            ("Balkón", _yes_no(p.has_balcony) + (f" ({p.balcony_m2:g} m²)" if p.has_balcony and p.balcony_m2 else "")),
            ("Terasa", _yes_no(p.has_terrace) + (f" ({p.terrace_m2:g} m²)" if p.has_terrace and p.terrace_m2 else "")),
            ("Záhrada", _yes_no(p.has_garden) + (f" ({p.garden_m2:g} m²)" if p.has_garden and p.garden_m2 else "")),
            ("Pivnica", _yes_no(p.has_cellar) + (f" ({p.cellar_m2:g} m²)" if p.has_cellar and p.cellar_m2 else "")),
            ("Parkovanie", _parking_summary(p)),
            ("Plocha pozemku", _dt(p.plot_m2, "m²") if p.property_type is PropertyType.HOUSE else "— (len dom)"),
            ("Rok výstavby", _dt(p.year_built)),
            ("Stav", CONDITION_LABELS_SK[p.condition] if p.condition else "—"),
            ("Supermarket", _dt(p.nearest_supermarket_m, "m")),
            ("Škôlka (štátna)", _dt(p.nearest_kindergarten_state_m, "m")),
            ("Škôlka (súkromná)", _dt(p.nearest_kindergarten_private_m, "m")),
            ("Nemocnica", _dt(p.nearest_hospital_m, "m")),
        ]

        for i, (label, value) in enumerate(rows):
            r, c = i // 2, (i % 2) * 2
            lbl = QLabel(label)
            lbl.setStyleSheet("color: #555; font-weight: 600;")
            grid.addWidget(lbl, r, c)
            v = QLabel(value)
            v.setStyleSheet("color: #1a1a1a;")
            grid.addWidget(v, r, c + 1)

        return box

    def _build_breakdown_panel(self) -> QWidget:
        box = QGroupBox(f"Rozklad indexu (celkom {self._property.index_score:.2f})"
                        if self._property.index_score is not None
                        else "Rozklad indexu")
        layout = QVBoxLayout(box)
        breakdown = self._property.index_breakdown or {}
        if not breakdown:
            layout.addWidget(QLabel("Index ešte nebol vypočítaný."))
            return box

        max_points = max((v["points"] for v in breakdown.values()), default=1) or 1
        for key, info in breakdown.items():
            row = QHBoxLayout()
            label = QLabel(info.get("label", key))
            label.setMinimumWidth(220)
            row.addWidget(label)

            bar = QProgressBar()
            bar.setRange(0, int(max_points * 100) or 100)
            bar.setValue(int(info["points"] * 100))
            bar.setFormat(f"{info['points']:.1f} b")
            bar.setTextVisible(True)
            row.addWidget(bar, 1)

            container = QWidget()
            container.setLayout(row)
            layout.addWidget(container)
        return box

    def _build_links_panel(self) -> QWidget:
        box = QGroupBox("Odkazy")
        layout = QVBoxLayout(box)
        items: list[tuple[str, str]] = []
        if self._property.primary_link:
            items.append(("Hlavný odkaz", self._property.primary_link))
        for link in self._property.links:
            items.append((link.label or "Odkaz", link.url))

        if not items:
            layout.addWidget(QLabel("Žiadne odkazy."))
            return box

        for label, url in items:
            row = QHBoxLayout()
            row.addWidget(QLabel(f"{label}:"))
            link_label = QLabel(f'<a href="{url}">{url}</a>')
            link_label.setOpenExternalLinks(True)
            link_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
            row.addWidget(link_label, 1)
            container = QWidget()
            container.setLayout(row)
            layout.addWidget(container)
        return box

    def _build_transit_panel(self) -> QWidget:
        box = QGroupBox("MHD v okolí")
        layout = QVBoxLayout(box)
        if not self._property.transit_stops:
            layout.addWidget(QLabel("Žiadne zastávky zadané."))
            return box
        for stop in self._property.transit_stops:
            text = f"{TRANSIT_LABELS_SK[stop.kind]}: {stop.distance_m} m"
            if stop.name:
                text += f" · {stop.name}"
            layout.addWidget(QLabel(text))
        return box

    def _build_tags_panel(self) -> QWidget:
        box = QGroupBox("Tagy")
        layout = QHBoxLayout(box)
        if not self._property.tags:
            layout.addWidget(QLabel("Žiadne."))
            return box
        for tag in self._property.tags:
            chip = QLabel(f"#{tag}")
            chip.setStyleSheet(
                "background-color: #dbeafe; color: #1e3a8a; "
                "border-radius: 8px; padding: 4px 10px;"
            )
            layout.addWidget(chip)
        layout.addStretch(1)
        return box

    def _build_notes_panel(self) -> QWidget:
        box = QGroupBox("Poznámky")
        layout = QVBoxLayout(box)
        if self._property.notes:
            note = QLabel(self._property.notes)
            note.setWordWrap(True)
            layout.addWidget(note)
        else:
            layout.addWidget(QLabel("—"))
        return box
