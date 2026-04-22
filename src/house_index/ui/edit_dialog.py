from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLineEdit,
    QMessageBox,
    QScrollArea,
    QSpinBox,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from house_index.domain.enums import (
    CONDITION_LABELS_SK,
    PROPERTY_TYPE_LABELS_SK,
    STATUS_LABELS_SK,
    Condition,
    PropertyType,
    Status,
)
from house_index.domain.models import Link, Property
from house_index.ui.utils import fit_to_screen
from house_index.ui.widgets.dynamic_list import DynamicList
from house_index.ui.widgets.link_row import LinkRow
from house_index.ui.widgets.photo_gallery import PhotoGallery
from house_index.ui.widgets.transit_row import TransitRow


def _combo_with_enum(enum_cls, labels) -> QComboBox:
    c = QComboBox()
    for item in enum_cls:
        c.addItem(labels[item], item.value)
    return c


def _optional_double_spin(minv: float, maxv: float, suffix: str = "", step: float = 1.0) -> QDoubleSpinBox:
    s = QDoubleSpinBox()
    s.setRange(minv, maxv)
    s.setSuffix(f" {suffix}" if suffix else "")
    s.setDecimals(1)
    s.setSingleStep(step)
    s.setSpecialValueText("—")
    s.setValue(minv)
    return s


def _optional_int_spin(minv: int, maxv: int, suffix: str = "", step: int = 1) -> QSpinBox:
    s = QSpinBox()
    s.setRange(minv, maxv)
    if suffix:
        s.setSuffix(f" {suffix}")
    s.setSingleStep(step)
    s.setSpecialValueText("—")
    s.setValue(minv)
    return s


def _scrollable(content: QWidget) -> QWidget:
    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setFrameShape(QFrame.Shape.NoFrame)
    scroll.setWidget(content)
    return scroll


class PropertyEditDialog(QDialog):
    def __init__(
        self,
        photos_dir: Path,
        prop: Property | None = None,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self._photos_dir = photos_dir
        self._property = prop if prop else Property(title="")
        self.setWindowTitle("Upraviť nehnuteľnosť" if prop else "Pridať nehnuteľnosť")
        self.resize(860, 700)

        outer = QVBoxLayout(self)
        self.tabs = QTabWidget()
        outer.addWidget(self.tabs, 1)

        self._build_basic_tab()
        self._build_questionnaire_tab()
        self._build_location_tab()
        self._build_links_tab()
        self._build_photos_tab()
        self._build_notes_tab()

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        outer.addWidget(buttons)

        self.type_combo.currentIndexChanged.connect(self._on_type_changed)
        self._load_from_property()
        self._on_type_changed()

    def showEvent(self, event) -> None:  # noqa: N802
        super().showEvent(event)
        fit_to_screen(self, margin=50)

    def _build_basic_tab(self) -> None:
        content = QWidget()
        form = QFormLayout(content)

        self.title_edit = QLineEdit()
        self.type_combo = _combo_with_enum(PropertyType, PROPERTY_TYPE_LABELS_SK)
        self.multi_floor_check = QCheckBox("Viacpodlažná")
        self.primary_link_edit = QLineEdit()
        self.primary_link_edit.setPlaceholderText("https://otodom.pl/...")
        self.status_combo = _combo_with_enum(Status, STATUS_LABELS_SK)

        self.price_spin = _optional_int_spin(0, 10_000_000, "PLN", 10_000)
        self.area_spin = _optional_double_spin(0, 10_000, "m²", 1.0)
        self.plot_spin = _optional_double_spin(0, 100_000, "m²", 10.0)
        self.rooms_spin = _optional_int_spin(0, 20, "izieb")

        form.addRow("Názov*", self.title_edit)
        form.addRow("Typ", self.type_combo)
        form.addRow("", self.multi_floor_check)
        form.addRow("Hlavný odkaz", self.primary_link_edit)
        form.addRow("Status", self.status_combo)
        form.addRow("Cena", self.price_spin)
        form.addRow("Plocha (obytná)", self.area_spin)
        self._plot_label = "Plocha pozemku (iba dom)"
        form.addRow(self._plot_label, self.plot_spin)
        form.addRow("Počet izieb", self.rooms_spin)

        self.tabs.addTab(_scrollable(content), "Základ")

    def _build_questionnaire_tab(self) -> None:
        content = QWidget()
        outer = QVBoxLayout(content)

        layout_box = QGroupBox("Rozloženie")
        layout_form = QFormLayout(layout_box)
        self.floor_spin = _optional_int_spin(-2, 50, "posch.")
        self.elevator_check = QCheckBox("Výťah")
        self.balcony_check = QCheckBox("Balkón")
        self.balcony_area = _optional_double_spin(0, 200, "m²", 0.5)
        self.terrace_check = QCheckBox("Terasa")
        self.terrace_area = _optional_double_spin(0, 500, "m²", 0.5)
        self.garden_check = QCheckBox("Záhrada")
        self.garden_area = _optional_double_spin(0, 10_000, "m²", 5)
        self.cellar_check = QCheckBox("Pivnica")
        self.cellar_area = _optional_double_spin(0, 200, "m²", 0.5)

        def add_with_check(label: str, check: QCheckBox, area: QDoubleSpinBox):
            h = QHBoxLayout()
            h.addWidget(check)
            h.addWidget(area)
            w = QWidget()
            w.setLayout(h)
            layout_form.addRow(label, w)

        layout_form.addRow("Poschodie", self.floor_spin)
        layout_form.addRow("Výťah", self.elevator_check)
        add_with_check("Balkón", self.balcony_check, self.balcony_area)
        add_with_check("Terasa", self.terrace_check, self.terrace_area)
        add_with_check("Záhrada", self.garden_check, self.garden_area)
        add_with_check("Pivnica", self.cellar_check, self.cellar_area)
        outer.addWidget(layout_box)

        rooms_box = QGroupBox("Plochy miestností (voliteľné)")
        rooms_form = QFormLayout(rooms_box)
        self.living_room_area = _optional_double_spin(0, 200, "m²", 0.5)
        self.kitchen_area = _optional_double_spin(0, 100, "m²", 0.5)
        self.bathroom_area = _optional_double_spin(0, 50, "m²", 0.5)
        self.bedroom_area = _optional_double_spin(0, 100, "m²", 0.5)
        self.pantry_check = QCheckBox("Špajza")
        self.wc_count_spin = QSpinBox()
        self.wc_count_spin.setRange(0, 5)
        self.wc_count_spin.setSuffix(" WC")
        rooms_form.addRow("Obývačka", self.living_room_area)
        rooms_form.addRow("Kuchyňa", self.kitchen_area)
        rooms_form.addRow("Najväčšia kúpeľňa", self.bathroom_area)
        rooms_form.addRow("Hlavná spálňa", self.bedroom_area)
        rooms_form.addRow("Špajza", self.pantry_check)
        rooms_form.addRow("Samostatné WC", self.wc_count_spin)
        outer.addWidget(rooms_box)

        parking_box = QGroupBox("Parkovanie")
        parking_form = QFormLayout(parking_box)
        self.garage_check = QCheckBox("Garáž")
        self.garage_spots_spin = QSpinBox()
        self.garage_spots_spin.setRange(0, 20)
        self.garage_spots_spin.setSuffix(" miest")
        self.parking_spot_check = QCheckBox("Parkovacie miesto (mimo garáže)")
        self.parking_spot_count_spin = QSpinBox()
        self.parking_spot_count_spin.setRange(0, 20)
        self.parking_spot_count_spin.setSuffix(" miest")

        add_with_check_p = lambda label, check, spin: parking_form.addRow(
            label, self._hbox(check, spin)
        )
        add_with_check_p("Garáž", self.garage_check, self.garage_spots_spin)
        add_with_check_p("Parkovanie", self.parking_spot_check, self.parking_spot_count_spin)
        outer.addWidget(parking_box)

        eq_box = QGroupBox("Stav a rok")
        eq_form = QFormLayout(eq_box)
        self.year_spin = _optional_int_spin(0, 2100, "")
        self.year_spin.setMinimum(0)
        self.condition_combo = QComboBox()
        self.condition_combo.addItem("—", None)
        for c in Condition:
            self.condition_combo.addItem(CONDITION_LABELS_SK[c], c.value)

        eq_form.addRow("Rok výstavby", self.year_spin)
        eq_form.addRow("Stav", self.condition_combo)
        outer.addWidget(eq_box)

        outer.addStretch(1)
        self.tabs.addTab(_scrollable(content), "Dotazník")

    @staticmethod
    def _hbox(*widgets) -> QWidget:
        w = QWidget()
        h = QHBoxLayout(w)
        h.setContentsMargins(0, 0, 0, 0)
        for widget in widgets:
            h.addWidget(widget)
        return w

    def _build_location_tab(self) -> None:
        content = QWidget()
        outer = QVBoxLayout(content)

        form = QFormLayout()
        self.distance_spin = _optional_double_spin(0, 200, "km", 0.1)
        form.addRow("Vzdialenosť od centra Katowíc", self.distance_spin)
        outer.addLayout(form)

        amenity_box = QGroupBox("Amenity v okolí (vzdialenosť v metroch)")
        amenity_form = QFormLayout(amenity_box)
        self.supermarket_spin = _optional_int_spin(0, 50_000, "m", 50)
        self.kg_state_spin = _optional_int_spin(0, 50_000, "m", 50)
        self.kg_private_spin = _optional_int_spin(0, 50_000, "m", 50)
        self.hospital_spin = _optional_int_spin(0, 100_000, "m", 100)
        amenity_form.addRow("Najbližší supermarket", self.supermarket_spin)
        amenity_form.addRow("Najbližšia štátna škôlka", self.kg_state_spin)
        amenity_form.addRow("Najbližšia súkromná škôlka", self.kg_private_spin)
        amenity_form.addRow("Najbližšia nemocnica", self.hospital_spin)
        outer.addWidget(amenity_box)

        transit_box = QGroupBox("Dopravné zastávky (MHD / vlak / regionálny bus)")
        transit_layout = QVBoxLayout(transit_box)
        self.transit_list = DynamicList(lambda: TransitRow(), "+ Pridať zastávku")
        transit_layout.addWidget(self.transit_list)
        outer.addWidget(transit_box, 1)

        self.tabs.addTab(_scrollable(content), "Lokalita")

    def _build_links_tab(self) -> None:
        content = QWidget()
        layout = QVBoxLayout(content)
        info = QLineEdit()
        info.setReadOnly(True)
        info.setFrame(False)
        info.setText("Hlavný odkaz je v záložke Základ. Tu pridaj ďalšie (mapa, plán, fotogaléria...).")
        layout.addWidget(info)
        self.links_list = DynamicList(lambda: LinkRow(), "+ Pridať odkaz")
        layout.addWidget(self.links_list, 1)
        self.tabs.addTab(_scrollable(content), "Odkazy")

    def _build_photos_tab(self) -> None:
        content = QWidget()
        layout = QVBoxLayout(content)
        self.photo_gallery = PhotoGallery(self._photos_dir)
        layout.addWidget(self.photo_gallery)
        self.tabs.addTab(_scrollable(content), "Fotky")

    def _build_notes_tab(self) -> None:
        content = QWidget()
        layout = QVBoxLayout(content)

        self.tags_edit = QLineEdit()
        self.tags_edit.setPlaceholderText("Tagy, oddelené čiarkou (napr. centrum, nova, svetle)")

        form = QFormLayout()
        form.addRow("Tagy", self.tags_edit)
        layout.addLayout(form)

        self.notes_edit = QTextEdit()
        self.notes_edit.setPlaceholderText("Voľné poznámky k nehnuteľnosti...")
        layout.addWidget(self.notes_edit, 1)

        self.tabs.addTab(_scrollable(content), "Poznámky")

    def _on_type_changed(self) -> None:
        is_house = self.type_combo.currentData() == PropertyType.HOUSE.value
        self.plot_spin.setEnabled(is_house)
        if not is_house:
            self.plot_spin.setValue(0)

    def _load_from_property(self) -> None:
        p = self._property
        self.title_edit.setText(p.title)
        self._set_combo_by_data(self.type_combo, p.property_type.value)
        self.multi_floor_check.setChecked(p.multi_floor)
        self.primary_link_edit.setText(p.primary_link or "")
        self._set_combo_by_data(self.status_combo, p.status.value)

        self.price_spin.setValue(p.price_pln or 0)
        self.area_spin.setValue(p.area_m2 or 0)
        self.plot_spin.setValue(p.plot_m2 or 0)
        self.rooms_spin.setValue(p.rooms or 0)

        self.floor_spin.setValue(p.floor if p.floor is not None else -2)
        self.elevator_check.setChecked(p.has_elevator)
        self.balcony_check.setChecked(p.has_balcony)
        self.balcony_area.setValue(p.balcony_m2 or 0)
        self.terrace_check.setChecked(p.has_terrace)
        self.terrace_area.setValue(p.terrace_m2 or 0)
        self.garden_check.setChecked(p.has_garden)
        self.garden_area.setValue(p.garden_m2 or 0)
        self.cellar_check.setChecked(p.has_cellar)
        self.cellar_area.setValue(p.cellar_m2 or 0)

        self.garage_check.setChecked(p.has_garage)
        self.garage_spots_spin.setValue(p.garage_spots)
        self.parking_spot_check.setChecked(p.has_parking_spot)
        self.parking_spot_count_spin.setValue(p.parking_spot_count)

        self.living_room_area.setValue(p.living_room_m2 or 0)
        self.kitchen_area.setValue(p.kitchen_m2 or 0)
        self.bathroom_area.setValue(p.bathroom_largest_m2 or 0)
        self.bedroom_area.setValue(p.bedroom_master_m2 or 0)
        self.pantry_check.setChecked(p.has_pantry)
        self.wc_count_spin.setValue(p.separate_wc_count)

        self.year_spin.setValue(p.year_built or 0)
        if p.condition:
            self._set_combo_by_data(self.condition_combo, p.condition.value)

        self.distance_spin.setValue(p.distance_km or 0)
        self.supermarket_spin.setValue(p.nearest_supermarket_m or 0)
        self.kg_state_spin.setValue(p.nearest_kindergarten_state_m or 0)
        self.kg_private_spin.setValue(p.nearest_kindergarten_private_m or 0)
        self.hospital_spin.setValue(p.nearest_hospital_m or 0)
        for stop in p.transit_stops:
            row: TransitRow = self.transit_list.add_row()
            row.set_stop(stop)

        for link in p.links:
            row = self.links_list.add_row()
            row.set_link(link)

        self.photo_gallery.set_photos(p.photos)

        self.tags_edit.setText(", ".join(p.tags))
        self.notes_edit.setPlainText(p.notes or "")

    @staticmethod
    def _set_combo_by_data(combo: QComboBox, data) -> None:
        idx = combo.findData(data)
        if idx >= 0:
            combo.setCurrentIndex(idx)

    def _on_accept(self) -> None:
        title = self.title_edit.text().strip()
        if not title:
            QMessageBox.warning(self, "Chýba údaj", "Nehnuteľnosť musí mať názov.")
            return

        p = self._property
        p.title = title
        p.property_type = PropertyType(self.type_combo.currentData())
        p.multi_floor = self.multi_floor_check.isChecked()
        p.primary_link = self.primary_link_edit.text().strip() or None
        p.status = Status(self.status_combo.currentData())

        p.price_pln = self.price_spin.value() or None
        p.area_m2 = self.area_spin.value() or None
        p.plot_m2 = self.plot_spin.value() or None
        p.rooms = self.rooms_spin.value() or None

        p.floor = self.floor_spin.value() if self.floor_spin.value() != -2 else None
        p.has_elevator = self.elevator_check.isChecked()
        p.has_balcony = self.balcony_check.isChecked()
        p.balcony_m2 = self.balcony_area.value() or None
        p.has_terrace = self.terrace_check.isChecked()
        p.terrace_m2 = self.terrace_area.value() or None
        p.has_garden = self.garden_check.isChecked()
        p.garden_m2 = self.garden_area.value() or None
        p.has_cellar = self.cellar_check.isChecked()
        p.cellar_m2 = self.cellar_area.value() or None

        p.has_garage = self.garage_check.isChecked()
        p.garage_spots = self.garage_spots_spin.value() if p.has_garage else 0
        p.has_parking_spot = self.parking_spot_check.isChecked()
        p.parking_spot_count = self.parking_spot_count_spin.value() if p.has_parking_spot else 0

        p.living_room_m2 = self.living_room_area.value() or None
        p.kitchen_m2 = self.kitchen_area.value() or None
        p.bathroom_largest_m2 = self.bathroom_area.value() or None
        p.bedroom_master_m2 = self.bedroom_area.value() or None
        p.has_pantry = self.pantry_check.isChecked()
        p.separate_wc_count = self.wc_count_spin.value()

        p.year_built = self.year_spin.value() or None
        cond_data = self.condition_combo.currentData()
        p.condition = Condition(cond_data) if cond_data else None

        p.distance_km = self.distance_spin.value() or None
        p.nearest_supermarket_m = self.supermarket_spin.value() or None
        p.nearest_kindergarten_state_m = self.kg_state_spin.value() or None
        p.nearest_kindergarten_private_m = self.kg_private_spin.value() or None
        p.nearest_hospital_m = self.hospital_spin.value() or None
        p.transit_stops = [
            row.to_stop() for row in self.transit_list.rows() if isinstance(row, TransitRow)
        ]

        links: list[Link] = []
        for row in self.links_list.rows():
            if isinstance(row, LinkRow):
                link = row.to_link()
                if link is not None:
                    links.append(link)
        p.links = links

        p.photos = self.photo_gallery.photos()

        raw_tags = self.tags_edit.text().split(",")
        p.tags = [t.strip() for t in raw_tags if t.strip()]
        p.notes = self.notes_edit.toPlainText().strip() or None

        self.accept()

    def property_data(self) -> Property:
        return self._property
