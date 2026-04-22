from __future__ import annotations

from typing import Callable

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)


class DynamicList(QWidget):
    """Kontajner na dynamické pridávanie a odstraňovanie riadkov."""

    def __init__(
        self,
        row_factory: Callable[[], QWidget],
        add_label: str = "+ Pridať",
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self._row_factory = row_factory
        self._rows: list[tuple[QWidget, QWidget]] = []

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        outer.addWidget(scroll, 1)

        self._inner = QWidget()
        self._inner_layout = QVBoxLayout(self._inner)
        self._inner_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        scroll.setWidget(self._inner)

        add_btn = QPushButton(add_label)
        add_btn.clicked.connect(lambda: self.add_row())
        outer.addWidget(add_btn)

    def add_row(self) -> QWidget:
        row_widget = self._row_factory()
        wrapper = QWidget()
        layout = QHBoxLayout(wrapper)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(row_widget, 1)

        remove_btn = QPushButton("×")
        remove_btn.setFixedWidth(28)
        remove_btn.clicked.connect(lambda: self._remove(wrapper))
        layout.addWidget(remove_btn)

        self._inner_layout.addWidget(wrapper)
        self._rows.append((wrapper, row_widget))
        return row_widget

    def _remove(self, wrapper: QWidget) -> None:
        for i, (w, row) in enumerate(self._rows):
            if w is wrapper:
                self._rows.pop(i)
                wrapper.deleteLater()
                return

    def clear(self) -> None:
        for wrapper, _ in self._rows:
            wrapper.deleteLater()
        self._rows = []

    def rows(self) -> list[QWidget]:
        return [row for _, row in self._rows]
