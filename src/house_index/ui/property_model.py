from __future__ import annotations

from typing import Any

from PySide6.QtCore import QAbstractListModel, QModelIndex, Qt

from house_index.domain.models import Property

PropertyRole = Qt.ItemDataRole.UserRole + 1


class PropertyListModel(QAbstractListModel):
    def __init__(self, parent: Any = None):
        super().__init__(parent)
        self._items: list[Property] = []

    def set_items(self, items: list[Property]) -> None:
        self.beginResetModel()
        self._items = list(items)
        self.endResetModel()

    def item_at(self, row: int) -> Property | None:
        if 0 <= row < len(self._items):
            return self._items[row]
        return None

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:  # noqa: B008
        return 0 if parent.isValid() else len(self._items)

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if not index.isValid() or index.row() >= len(self._items):
            return None
        prop = self._items[index.row()]
        if role == PropertyRole:
            return prop
        if role == Qt.ItemDataRole.DisplayRole:
            return prop.title
        if role == Qt.ItemDataRole.ToolTipRole:
            return prop.primary_link or ""
        return None
