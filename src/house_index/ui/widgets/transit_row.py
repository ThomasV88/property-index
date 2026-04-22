from __future__ import annotations

from PySide6.QtWidgets import QComboBox, QHBoxLayout, QLineEdit, QSpinBox, QWidget

from house_index.domain.enums import TRANSIT_LABELS_SK, TransitKind
from house_index.domain.models import TransitStop


class TransitRow(QWidget):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.kind = QComboBox()
        for k in TransitKind:
            self.kind.addItem(TRANSIT_LABELS_SK[k], k.value)

        self.distance = QSpinBox()
        self.distance.setRange(0, 20000)
        self.distance.setSuffix(" m")
        self.distance.setSingleStep(50)

        self.name = QLineEdit()
        self.name.setPlaceholderText("Názov zastávky (voliteľné)")

        layout.addWidget(self.kind)
        layout.addWidget(self.distance)
        layout.addWidget(self.name, 1)

    def set_stop(self, stop: TransitStop) -> None:
        idx = self.kind.findData(stop.kind.value)
        if idx >= 0:
            self.kind.setCurrentIndex(idx)
        self.distance.setValue(stop.distance_m)
        self.name.setText(stop.name or "")

    def to_stop(self) -> TransitStop:
        return TransitStop(
            kind=TransitKind(self.kind.currentData()),
            distance_m=self.distance.value(),
            name=self.name.text().strip() or None,
        )
