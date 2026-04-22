from __future__ import annotations

from pathlib import Path

from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QLabel,
    QMainWindow,
    QMenu,
    QMessageBox,
    QSizePolicy,
    QStatusBar,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from house_index import __app_name__
from house_index.domain.enums import STATUS_LABELS_SK, Status
from house_index.domain.models import Property
from house_index.paths import data_dir, db_path, photos_dir
from house_index.services import backup_service
from house_index.services.property_service import PropertyService
from house_index.ui.cards_view import CardsView
from house_index.ui.compare_view import CompareDialog
from house_index.ui.detail_view import PropertyDetailDialog
from house_index.ui.edit_dialog import PropertyEditDialog
from house_index.ui.settings_panel import SettingsPanel

SORT_OPTIONS: list[tuple[str, str]] = [
    ("Index (najvyšší)", "index_score DESC, id DESC"),
    ("Index (najnižší)", "index_score ASC, id DESC"),
    ("Cena (najnižšia)", "price_pln ASC NULLS LAST, id DESC"),
    ("Cena (najvyššia)", "price_pln DESC NULLS LAST, id DESC"),
    ("Plocha (najväčšia)", "area_m2 DESC NULLS LAST, id DESC"),
    ("Dátum pridania", "id DESC"),
    ("Cena / m² (najnižšia)", "(price_pln * 1.0 / NULLIF(area_m2, 0)) ASC NULLS LAST, id DESC"),
]


LIGHT_STYLESHEET = """
QMainWindow, QDialog, QWidget { background-color: #fafafa; color: #1a1a1a; }
QToolBar { background: #f0f0f0; border: 0; border-bottom: 1px solid #d0d0d0;
           padding: 4px; color: #1a1a1a; }
QToolButton { padding: 6px 10px; border-radius: 4px; color: #1a1a1a; }
QToolButton:hover { background: #e3e8ef; }
QToolButton:pressed { background: #d0d7df; }
QStatusBar { background: #f0f0f0; color: #555; border-top: 1px solid #d0d0d0; }
QTabWidget::pane { border: 1px solid #d0d0d0; background: #ffffff; top: -1px; }
QTabBar::tab { color: #1a1a1a; background: #e9ecef; padding: 7px 14px;
               border: 1px solid #d0d0d0; border-bottom: none;
               border-top-left-radius: 4px; border-top-right-radius: 4px;
               margin-right: 2px; }
QTabBar::tab:selected { background: #ffffff; color: #000000; font-weight: 600; }
QTabBar::tab:hover:!selected { background: #f2f4f7; }
QGroupBox { border: 1px solid #d0d0d0; border-radius: 6px; margin-top: 14px;
            padding-top: 10px; background: #ffffff; }
QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top left;
                   padding: 0 6px; color: #1a1a1a; font-weight: 600;
                   background: #fafafa; }
QLineEdit, QTextEdit, QPlainTextEdit, QComboBox, QSpinBox, QDoubleSpinBox {
    background: #ffffff; color: #1a1a1a; border: 1px solid #c7ccd3;
    border-radius: 4px; padding: 4px 6px; selection-background-color: #3b82f6;
    selection-color: #ffffff;
}
QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus, QComboBox:focus,
QSpinBox:focus, QDoubleSpinBox:focus { border: 1px solid #3b82f6; }
QLineEdit:disabled, QSpinBox:disabled, QDoubleSpinBox:disabled {
    background: #f0f0f0; color: #888; }
QPushButton { background: #ffffff; color: #1a1a1a; border: 1px solid #c7ccd3;
              border-radius: 4px; padding: 6px 14px; }
QPushButton:hover { background: #f0f4f9; border-color: #3b82f6; }
QPushButton:pressed { background: #e3e8ef; }
QPushButton:default { background: #3b82f6; color: #ffffff; border: 1px solid #2563eb; }
QPushButton:default:hover { background: #2563eb; }
QCheckBox { color: #1a1a1a; }
QCheckBox:disabled { color: #999; }
QLabel { color: #1a1a1a; background: transparent; }
QProgressBar { background: #f0f0f0; border: 1px solid #c7ccd3; border-radius: 4px;
               text-align: center; color: #1a1a1a; }
QProgressBar::chunk { background: #3b82f6; border-radius: 3px; }
QTableWidget, QTableView, QListView, QTreeView {
    background: #ffffff; color: #1a1a1a; border: 1px solid #d0d0d0;
    gridline-color: #e0e0e0;
    alternate-background-color: #f7f9fb;
    selection-background-color: #dbeafe; selection-color: #000000;
}
QHeaderView::section { background: #f0f0f0; color: #1a1a1a;
                       padding: 6px 8px; border: 1px solid #d0d0d0; font-weight: 600; }
QMenu { background: #ffffff; color: #1a1a1a; border: 1px solid #d0d0d0; }
QMenu::item:selected { background: #dbeafe; color: #000000; }
QScrollBar:vertical { background: #f0f0f0; width: 12px; margin: 0; }
QScrollBar::handle:vertical { background: #c7ccd3; border-radius: 6px; min-height: 20px; }
QScrollBar::handle:vertical:hover { background: #a8b0b8; }
QScrollBar:horizontal { background: #f0f0f0; height: 12px; margin: 0; }
QScrollBar::handle:horizontal { background: #c7ccd3; border-radius: 6px; min-width: 20px; }
QScrollBar::add-line, QScrollBar::sub-line { width: 0; height: 0; }
"""


class MainWindow(QMainWindow):
    def __init__(self, service: PropertyService) -> None:
        super().__init__()
        self._service = service

        self.setWindowTitle(__app_name__)
        self.resize(1280, 840)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)

        self._build_toolbar()

        self.cards_view = CardsView(photos_dir(), self)
        self.cards_view.property_activated.connect(self._on_view_detail)
        layout.addWidget(self.cards_view, 1)

        self.status_label = QLabel("")
        status = QStatusBar()
        status.addPermanentWidget(self.status_label)
        self.setStatusBar(status)

        self._apply_light_palette()
        self.reload()

    def _build_toolbar(self) -> None:
        toolbar = QToolBar("Hlavný panel")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        add_action = QAction("Pridať", self)
        add_action.triggered.connect(self._on_add_property)
        toolbar.addAction(add_action)

        edit_action = QAction("Upraviť", self)
        edit_action.triggered.connect(self._on_edit_selected)
        toolbar.addAction(edit_action)

        delete_action = QAction("Zmazať", self)
        delete_action.triggered.connect(self._on_delete_selected)
        toolbar.addAction(delete_action)

        toolbar.addSeparator()

        compare_action = QAction("Porovnať", self)
        compare_action.setToolTip("Označ 2–3 nehnuteľnosti (Ctrl + klik)")
        compare_action.triggered.connect(self._on_compare_selected)
        toolbar.addAction(compare_action)

        settings_action = QAction("Nastavenia", self)
        settings_action.triggered.connect(self._on_settings)
        toolbar.addAction(settings_action)

        toolbar.addSeparator()

        backup_action = QAction("Záloha ▾", self)
        backup_menu = QMenu(self)
        export_act = backup_menu.addAction("Exportovať ZIP...")
        export_act.triggered.connect(self._on_export_backup)
        restore_act = backup_menu.addAction("Obnoviť zo ZIP...")
        restore_act.triggered.connect(self._on_restore_backup)
        backup_action.setMenu(backup_menu)
        backup_action.triggered.connect(lambda: backup_menu.popup(self.cursor().pos()))
        toolbar.addAction(backup_action)

        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        toolbar.addWidget(spacer)

        toolbar.addWidget(QLabel("Status: "))
        self.status_filter = QComboBox()
        self.status_filter.addItem("Všetky", None)
        for s in Status:
            self.status_filter.addItem(STATUS_LABELS_SK[s], s.value)
        self.status_filter.currentIndexChanged.connect(lambda _: self.reload())
        toolbar.addWidget(self.status_filter)

        toolbar.addWidget(QLabel("  Radiť: "))
        self.sort_combo = QComboBox()
        for label, order in SORT_OPTIONS:
            self.sort_combo.addItem(label, order)
        self.sort_combo.currentIndexChanged.connect(lambda _: self.reload())
        toolbar.addWidget(self.sort_combo)

    def _apply_light_palette(self) -> None:
        self.setStyleSheet(LIGHT_STYLESHEET)

    def reload(self) -> None:
        status_value = self.status_filter.currentData() if hasattr(self, "status_filter") else None
        status = Status(status_value) if status_value else None
        order = self.sort_combo.currentData() if hasattr(self, "sort_combo") else None
        items = self._service.list_all(status=status, order_by=order)
        self.cards_view.set_eur_rate(self._service.get_eur_rate())
        self.cards_view.set_properties(items)
        self.status_label.setText(f"Nehnuteľností: {len(items)}")

    def _on_add_property(self) -> None:
        dlg = PropertyEditDialog(photos_dir=photos_dir(), parent=self)
        if dlg.exec():
            self._service.save(dlg.property_data())
            self.reload()

    def _on_edit_selected(self) -> None:
        selected = self.cards_view.selected_properties()
        if len(selected) != 1:
            QMessageBox.information(
                self, "Upraviť", "Vyber presne jednu nehnuteľnosť na úpravu."
            )
            return
        self._on_edit_property(selected[0])

    def _on_edit_property(self, prop: Property) -> None:
        full = self._service.get(prop.id)
        if full is None:
            return
        dlg = PropertyEditDialog(photos_dir=photos_dir(), prop=full, parent=self)
        if dlg.exec():
            self._service.save(dlg.property_data())
            self.reload()

    def _on_view_detail(self, prop: Property) -> None:
        full = self._service.get(prop.id)
        if full is None:
            return
        dlg = PropertyDetailDialog(full, photos_dir(), self, service=self._service)
        dlg.exec()
        if dlg.edit_requested_flag():
            self._on_edit_property(full)

    def _on_settings(self) -> None:
        dlg = SettingsPanel(self._service, self)
        if dlg.exec():
            self.reload()

    def _on_export_backup(self) -> None:
        default = str(Path.home() / "house-index-backup.zip")
        path, _ = QFileDialog.getSaveFileName(
            self, "Exportovať zálohu", default, "ZIP archívy (*.zip)"
        )
        if not path:
            return
        try:
            count = backup_service.create_backup(Path(path), db_path(), photos_dir())
        except backup_service.BackupError as exc:
            QMessageBox.critical(self, "Chyba", str(exc))
            return
        QMessageBox.information(
            self, "Záloha", f"Záloha uložená ({count} fotiek):\n{path}"
        )

    def _on_restore_backup(self) -> None:
        confirm = QMessageBox.warning(
            self,
            "Obnoviť zálohu",
            "Obnovenie prepíše aktuálnu databázu a fotky. Aktuálna DB sa uloží ako "
            ".bak. Pokračovať?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return

        path, _ = QFileDialog.getOpenFileName(
            self, "Obnoviť zo zálohy", str(Path.home()), "ZIP archívy (*.zip)"
        )
        if not path:
            return

        try:
            _, count = backup_service.restore_backup(Path(path), db_path(), photos_dir())
        except backup_service.BackupError as exc:
            QMessageBox.critical(self, "Chyba", str(exc))
            return

        QMessageBox.information(
            self, "Obnovenie",
            f"Obnovené: {count} fotiek. Aplikáciu reštartuj ak nevidíš zmeny."
        )
        self._service = PropertyService(db_path())
        self.reload()

    def _on_compare_selected(self) -> None:
        selected = self.cards_view.selected_properties()
        if len(selected) < 2 or len(selected) > 3:
            QMessageBox.information(
                self, "Porovnať",
                "Vyber 2 alebo 3 nehnuteľnosti na porovnanie (Ctrl + klik).",
            )
            return
        full = [self._service.get(p.id) for p in selected]
        full = [p for p in full if p is not None]
        if len(full) < 2:
            return
        dlg = CompareDialog(full, photos_dir(), self, scoring_config=self._service.scoring_config)
        dlg.exec()

    def _on_delete_selected(self) -> None:
        selected = self.cards_view.selected_properties()
        if not selected:
            return
        msg = (
            f"Naozaj zmazať {len(selected)} nehnuteľností?"
            if len(selected) > 1
            else f"Naozaj zmazať '{selected[0].title}'?"
        )
        answer = QMessageBox.question(self, "Zmazať", msg)
        if answer != QMessageBox.StandardButton.Yes:
            return
        for prop in selected:
            if prop.id is not None:
                self._service.delete(prop.id)
        self.reload()
