from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtWidgets import QListView

from house_index.domain.models import Property
from house_index.ui.card_delegate import CARD_HEIGHT, CARD_WIDTH, PropertyCardDelegate
from house_index.ui.property_model import PropertyListModel, PropertyRole


class CardsView(QListView):
    property_activated = Signal(Property)

    def __init__(self, photos_dir: Path, parent=None):
        super().__init__(parent)
        self._model = PropertyListModel(self)
        self.setModel(self._model)
        self._delegate = PropertyCardDelegate(photos_dir, self)
        self.setItemDelegate(self._delegate)
        self.setViewMode(QListView.ViewMode.IconMode)
        self.setResizeMode(QListView.ResizeMode.Adjust)
        self.setFlow(QListView.Flow.LeftToRight)
        self.setWrapping(True)
        self.setSpacing(6)
        self.setUniformItemSizes(True)
        self.setMovement(QListView.Movement.Static)
        self.setGridSize(QSize(CARD_WIDTH + 12, CARD_HEIGHT + 12))
        self.setSelectionMode(QListView.SelectionMode.ExtendedSelection)
        self.setStyleSheet("background-color: #fafafa;")

        self.doubleClicked.connect(self._on_double_clicked)

    def set_properties(self, items: list[Property]) -> None:
        self._model.set_items(items)

    def set_eur_rate(self, rate: float) -> None:
        self._delegate.set_eur_rate(rate)
        self.viewport().update()

    def selected_properties(self) -> list[Property]:
        return [
            idx.data(PropertyRole)
            for idx in self.selectionModel().selectedIndexes()
            if idx.data(PropertyRole) is not None
        ]

    def _on_double_clicked(self, index) -> None:
        prop = index.data(PropertyRole)
        if prop is not None:
            self.property_activated.emit(prop)
