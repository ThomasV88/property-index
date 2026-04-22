from __future__ import annotations

from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QDoubleSpinBox,
    QHBoxLayout,
    QHeaderView,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

MIN_VISIBLE_ROWS = 10
ROW_HEIGHT = 28


def format_number(v: float) -> str:
    if v == int(v):
        return f"{int(v):,}".replace(",", " ")
    return f"{v:.2f}"


def _set_min_height(table: QTableWidget) -> None:
    header_h = table.horizontalHeader().sizeHint().height() + 2
    table.setMinimumHeight(header_h + MIN_VISIBLE_ROWS * ROW_HEIGHT)


class BandsTable(QWidget):
    def __init__(self, bands: list[list[float]], parent: QWidget | None = None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.table = QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels(["Hranica", "Násobič (0–1)"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(
            QAbstractItemView.EditTrigger.DoubleClicked
            | QAbstractItemView.EditTrigger.EditKeyPressed
            | QAbstractItemView.EditTrigger.AnyKeyPressed
        )
        for t, m in bands:
            self._append_row(float(t), float(m))
        _set_min_height(self.table)
        layout.addWidget(self.table)

        row = QHBoxLayout()
        add_btn = QPushButton("+ Pridať pásmo")
        add_btn.clicked.connect(lambda: self._append_row(0.0, 0.5))
        remove_btn = QPushButton("− Odstrániť vybraté")
        remove_btn.clicked.connect(self._remove_selected)
        row.addWidget(add_btn)
        row.addWidget(remove_btn)
        row.addStretch(1)
        layout.addLayout(row)

    def _append_row(self, threshold: float, mult: float) -> None:
        r = self.table.rowCount()
        self.table.insertRow(r)
        self.table.setRowHeight(r, ROW_HEIGHT)
        self.table.setItem(r, 0, QTableWidgetItem(format_number(threshold)))
        self.table.setItem(r, 1, QTableWidgetItem(format_number(mult)))

    def _remove_selected(self) -> None:
        rows = sorted({i.row() for i in self.table.selectedIndexes()}, reverse=True)
        for r in rows:
            self.table.removeRow(r)

    def bands(self) -> list[list[float]]:
        out: list[list[float]] = []
        for r in range(self.table.rowCount()):
            t_item = self.table.item(r, 0)
            m_item = self.table.item(r, 1)
            if t_item is None or m_item is None:
                continue
            try:
                t = float(t_item.text().replace(" ", "").replace(",", "."))
                m = float(m_item.text().replace(" ", "").replace(",", "."))
            except ValueError:
                continue
            out.append([t, m])
        out.sort(key=lambda row: row[0])
        return out


class EnumPointsTable(QWidget):
    def __init__(self, points_map: dict[str, float], parent: QWidget | None = None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.table = QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels(["Kľúč", "Body"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        for key, pts in points_map.items():
            self._append_row(str(key), float(pts))
        _set_min_height(self.table)
        layout.addWidget(self.table)

        row = QHBoxLayout()
        add_btn = QPushButton("+ Pridať kľúč")
        add_btn.clicked.connect(lambda: self._append_row("", 0.0))
        remove_btn = QPushButton("− Odstrániť vybraté")
        remove_btn.clicked.connect(self._remove_selected)
        row.addWidget(add_btn)
        row.addWidget(remove_btn)
        row.addStretch(1)
        layout.addLayout(row)

    def _append_row(self, key: str, pts: float) -> None:
        r = self.table.rowCount()
        self.table.insertRow(r)
        self.table.setRowHeight(r, ROW_HEIGHT)
        self.table.setItem(r, 0, QTableWidgetItem(key))
        self.table.setItem(r, 1, QTableWidgetItem(format_number(pts)))

    def _remove_selected(self) -> None:
        rows = sorted({i.row() for i in self.table.selectedIndexes()}, reverse=True)
        for r in rows:
            self.table.removeRow(r)

    def points(self) -> dict[str, float]:
        out: dict[str, float] = {}
        for r in range(self.table.rowCount()):
            k = self.table.item(r, 0)
            v = self.table.item(r, 1)
            if k is None or v is None:
                continue
            key = k.text().strip()
            if not key:
                continue
            try:
                pts = float(v.text().replace(" ", "").replace(",", "."))
            except ValueError:
                continue
            out[key] = pts
        return out


class RenovationCostTable(QWidget):
    """Editor pre renovation_cost_per_m2: map {condition_key: PLN/m²}."""

    def __init__(self, cost_map: dict[str, Any], parent: QWidget | None = None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.table = QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels(["Stav", "Odhad renovácie (PLN/m²)"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        rows = max(len(cost_map), 3)
        self.table.setMinimumHeight(
            self.table.horizontalHeader().sizeHint().height() + 2 + rows * ROW_HEIGHT
        )
        for key, cost in cost_map.items():
            self._append_row(str(key), float(cost))
        layout.addWidget(self.table)

        row = QHBoxLayout()
        add_btn = QPushButton("+ Pridať stav")
        add_btn.clicked.connect(lambda: self._append_row("", 0.0))
        remove_btn = QPushButton("− Odstrániť vybraté")
        remove_btn.clicked.connect(self._remove_selected)
        row.addWidget(add_btn)
        row.addWidget(remove_btn)
        row.addStretch(1)
        layout.addLayout(row)

    def _append_row(self, key: str, cost: float) -> None:
        r = self.table.rowCount()
        self.table.insertRow(r)
        self.table.setRowHeight(r, ROW_HEIGHT)
        self.table.setItem(r, 0, QTableWidgetItem(key))
        self.table.setItem(r, 1, QTableWidgetItem(format_number(cost)))

    def _remove_selected(self) -> None:
        rows = sorted({i.row() for i in self.table.selectedIndexes()}, reverse=True)
        for r in rows:
            self.table.removeRow(r)

    def cost_map(self) -> dict[str, float]:
        out: dict[str, float] = {}
        for r in range(self.table.rowCount()):
            k = self.table.item(r, 0)
            v = self.table.item(r, 1)
            if k is None or v is None:
                continue
            key = k.text().strip()
            if not key:
                continue
            try:
                cost = float(v.text().replace(" ", "").replace(",", "."))
            except ValueError:
                continue
            out[key] = cost
        return out


def make_double_spin(
    value: float,
    minv: float = 0,
    maxv: float = 10_000_000,
    step: float = 1.0,
    decimals: int = 2,
) -> QDoubleSpinBox:
    s = QDoubleSpinBox()
    s.setRange(minv, maxv)
    s.setSingleStep(step)
    s.setDecimals(decimals)
    s.setGroupSeparatorShown(True)
    s.setValue(value)
    s.setButtonSymbols(QDoubleSpinBox.ButtonSymbols.UpDownArrows)
    s.setMinimumWidth(140)
    return s
