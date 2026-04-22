from __future__ import annotations

import copy
import logging
from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QProgressDialog,
    QPushButton,
    QScrollArea,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from house_index.scoring.defaults import DEFAULT_SCORING_CONFIG
from house_index.services.property_service import PropertyService
from house_index.ui.utils import fit_to_screen
from house_index.ui.widgets.rule_card import RuleCard

log = logging.getLogger(__name__)

TAB_GROUPS: list[tuple[str, list[str]]] = [
    ("Financie", ["price_pln"]),
    ("Doprava", ["distance_km", "nearest_mhd_m", "nearest_train_m", "nearest_regional_bus_m"]),
    ("Amenity", [
        "nearest_supermarket_m",
        "nearest_kindergarten_state_m",
        "nearest_kindergarten_private_m",
        "nearest_hospital_m",
    ]),
    ("Priestor", [
        "area_m2", "rooms", "plot_m2",
        "living_room_m2", "kitchen_m2", "bathroom_largest_m2", "bedroom_master_m2",
    ]),
    ("Vybavenie", [
        "garage", "parking_spot", "garden", "cellar",
        "balcony_or_terrace", "has_elevator", "multi_floor",
        "has_pantry", "separate_wc_count",
    ]),
    ("Stav & Rok", ["condition", "year_built"]),
]


class SettingsPanel(QDialog):
    def __init__(self, service: PropertyService, parent: QWidget | None = None):
        super().__init__(parent)
        self._service = service
        self._cards: list[RuleCard] = []
        self._saving = False

        self.setWindowTitle("Nastavenia bodovania")
        self.resize(960, 820)

        outer = QVBoxLayout(self)

        intro = QLabel(
            "Uprav pásma, body a kľúče pre jednotlivé pravidlá indexu. "
            "Po uložení sa index prepočíta pre všetky nehnuteľnosti."
        )
        intro.setWordWrap(True)
        outer.addWidget(intro)

        self._tabs = QTabWidget()
        outer.addWidget(self._tabs, 1)

        self._populate(copy.deepcopy(service.scoring_config))
        self._add_general_tab()

        bottom = QHBoxLayout()
        self._reset_btn = QPushButton("Obnoviť defaulty")
        self._reset_btn.clicked.connect(self._on_reset_defaults)
        bottom.addWidget(self._reset_btn)
        bottom.addStretch(1)

        self._buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        self._save_btn = self._buttons.button(QDialogButtonBox.StandardButton.Save)
        self._save_btn.setText("Uložiť a prepočítať")
        self._save_btn.clicked.connect(self._on_save)
        self._buttons.rejected.connect(self.reject)
        bottom.addWidget(self._buttons)
        outer.addLayout(bottom)

    def showEvent(self, event) -> None:  # noqa: N802
        super().showEvent(event)
        fit_to_screen(self, margin=50)

    def _populate(self, config: dict[str, dict[str, Any]]) -> None:
        self._cards = []
        while self._tabs.count() > 0:
            self._tabs.removeTab(0)

        seen: set[str] = set()
        for tab_name, keys in TAB_GROUPS:
            tab = self._build_rules_tab([(k, config[k]) for k in keys if k in config])
            self._tabs.addTab(tab, tab_name)
            seen.update(keys)

        leftover = [(k, r) for k, r in config.items() if k not in seen]
        if leftover:
            tab = self._build_rules_tab(leftover)
            self._tabs.addTab(tab, "Ostatné")

    def _build_rules_tab(self, rules: list[tuple[str, dict[str, Any]]]) -> QWidget:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        inner = QWidget()
        layout = QVBoxLayout(inner)
        for key, rule in rules:
            card = RuleCard(key, rule)
            self._cards.append(card)
            layout.addWidget(card)
        layout.addStretch(1)
        scroll.setWidget(inner)
        return scroll

    def _add_general_tab(self) -> None:
        tab = QWidget()
        layout = QVBoxLayout(tab)

        header = QLabel(
            "<b>Obecné nastavenia</b><br>"
            "Kurz PLN → EUR ovplyvňuje iba zobrazenie ceny v kartách a detaile. "
            "Neukladá sa do scoring configu a neprepočítava skóre."
        )
        header.setWordWrap(True)
        layout.addWidget(header)

        form = QFormLayout()
        self._eur_rate_spin = QDoubleSpinBox()
        self._eur_rate_spin.setRange(0.0001, 10.0)
        self._eur_rate_spin.setDecimals(4)
        self._eur_rate_spin.setSingleStep(0.001)
        self._eur_rate_spin.setValue(self._service.get_eur_rate())
        self._eur_rate_spin.setMinimumWidth(160)
        form.addRow("Kurz PLN → EUR", self._eur_rate_spin)

        hint = QLabel(
            "Aprilová hodnota 2026: ~ <b>0.235</b> (1 PLN ≈ 0.235 EUR / "
            "1 EUR ≈ 4.25 PLN). Aktualizuj podľa potreby."
        )
        hint.setWordWrap(True)
        form.addRow(hint)

        layout.addLayout(form)
        layout.addStretch(1)
        self._tabs.addTab(tab, "Obecné")

    def _on_reset_defaults(self) -> None:
        answer = QMessageBox.question(
            self,
            "Obnoviť defaulty",
            "Naozaj obnoviť predvolené hodnoty? Všetky tvoje úpravy budú stratené "
            "(ale uložia sa až po Save).",
        )
        if answer == QMessageBox.StandardButton.Yes:
            self._populate(copy.deepcopy(DEFAULT_SCORING_CONFIG))
            self._add_general_tab()

    def _collect_config(self) -> dict[str, dict[str, Any]]:
        return {card.key: card.to_rule() for card in self._cards}

    def _set_saving(self, saving: bool) -> None:
        self._saving = saving
        self._save_btn.setEnabled(not saving)
        self._reset_btn.setEnabled(not saving)
        cancel = self._buttons.button(QDialogButtonBox.StandardButton.Cancel)
        if cancel is not None:
            cancel.setEnabled(not saving)
        self._save_btn.setText("Ukladám…" if saving else "Uložiť a prepočítať")

    def _on_save(self) -> None:
        if self._saving:
            log.info("Save klik ignorovaný — ukladanie už prebieha")
            return
        self._set_saving(True)
        QApplication.processEvents()
        log.info("Ukladám scoring_config + EUR rate")

        try:
            config = self._collect_config()
            log.debug("Zozbieraný config s %d pravidlami", len(config))
            self._service.save_config(config)
            self._service.set_eur_rate(self._eur_rate_spin.value())
            log.info("Config + EUR rate uložené")
        except Exception as exc:  # noqa: BLE001
            log.exception("save_config failed")
            self._set_saving(False)
            QMessageBox.critical(self, "Chyba", f"Ukladanie zlyhalo: {exc}")
            return

        self._run_recompute_sync()

    def _run_recompute_sync(self) -> None:
        log.info("Spúšťam recompute_all (sync)")
        progress = QProgressDialog("Prepočítavam indexy…", "", 0, 0, self)
        progress.setWindowTitle("Prepočítavam")
        progress.setCancelButton(None)
        progress.setMinimumDuration(0)
        progress.setWindowModality(Qt.WindowModality.ApplicationModal)
        progress.setAutoClose(False)
        progress.setAutoReset(False)
        progress.show()
        QApplication.processEvents()

        def on_progress(done: int, total: int) -> None:
            if progress.maximum() != total:
                progress.setMaximum(total)
            progress.setValue(done)
            QApplication.processEvents()

        try:
            count = self._service.recompute_all(on_progress)
            log.info("Recompute dokončený: %d nehnuteľností", count)
        except Exception as exc:  # noqa: BLE001
            log.exception("recompute_all failed")
            progress.close()
            self._set_saving(False)
            QMessageBox.critical(self, "Chyba", f"Prepočet zlyhal: {exc}")
            return

        progress.close()
        self._set_saving(False)
        QMessageBox.information(
            self, "Hotovo", f"Prepočítaných {count} nehnuteľností."
        )
        self.accept()
