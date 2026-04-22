from __future__ import annotations

from PySide6.QtWidgets import QHBoxLayout, QLineEdit, QWidget

from house_index.domain.models import Link


class LinkRow(QWidget):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.label = QLineEdit()
        self.label.setPlaceholderText("Štítok (napr. Mapa, Plán bytu)")
        self.label.setMaximumWidth(200)

        self.url = QLineEdit()
        self.url.setPlaceholderText("https://...")

        layout.addWidget(self.label)
        layout.addWidget(self.url, 1)

    def set_link(self, link: Link) -> None:
        self.label.setText(link.label or "")
        self.url.setText(link.url)

    def to_link(self) -> Link | None:
        url = self.url.text().strip()
        if not url:
            return None
        return Link(url=url, label=self.label.text().strip() or None)
