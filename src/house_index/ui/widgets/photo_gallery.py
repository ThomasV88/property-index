from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from house_index.domain.models import Photo
from house_index.services import photo_service

THUMB_SIZE = 140


class PhotoGallery(QWidget):
    def __init__(self, photos_dir: Path, parent: QWidget | None = None):
        super().__init__(parent)
        self.photos_dir = photos_dir
        self._photos: list[Photo] = []

        layout = QVBoxLayout(self)

        self.list_widget = QListWidget()
        self.list_widget.setViewMode(QListWidget.ViewMode.IconMode)
        self.list_widget.setIconSize(QSize(THUMB_SIZE, THUMB_SIZE))
        self.list_widget.setResizeMode(QListWidget.ResizeMode.Adjust)
        self.list_widget.setMovement(QListWidget.Movement.Static)
        self.list_widget.setSpacing(8)
        self.list_widget.setGridSize(QSize(THUMB_SIZE + 20, THUMB_SIZE + 36))
        layout.addWidget(self.list_widget, 1)

        buttons = QHBoxLayout()
        self.add_btn = QPushButton("+ Pridať fotku")
        self.add_btn.clicked.connect(self._on_add)
        self.primary_btn = QPushButton("Nastaviť ako hlavnú")
        self.primary_btn.clicked.connect(self._on_set_primary)
        self.remove_btn = QPushButton("Odstrániť")
        self.remove_btn.clicked.connect(self._on_remove)
        buttons.addWidget(self.add_btn)
        buttons.addWidget(self.primary_btn)
        buttons.addWidget(self.remove_btn)
        buttons.addStretch(1)
        layout.addLayout(buttons)

    def set_photos(self, photos: list[Photo]) -> None:
        self._photos = [Photo(**p.__dict__) for p in photos]
        self._refresh()

    def photos(self) -> list[Photo]:
        return list(self._photos)

    def _refresh(self) -> None:
        self.list_widget.clear()
        for idx, photo in enumerate(self._photos):
            path = self.photos_dir / photo.file_name
            pm = QPixmap(str(path))
            if not pm.isNull():
                pm = pm.scaled(
                    THUMB_SIZE, THUMB_SIZE,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            label = "★ hlavná" if photo.is_primary else f"fotka {idx + 1}"
            item = QListWidgetItem(pm, label)
            item.setData(Qt.ItemDataRole.UserRole, idx)
            self.list_widget.addItem(item)

    def _selected_index(self) -> int | None:
        items = self.list_widget.selectedItems()
        if not items:
            return None
        return items[0].data(Qt.ItemDataRole.UserRole)

    def _on_add(self) -> None:
        files, _ = QFileDialog.getOpenFileNames(
            self, "Vyber fotky", "",
            "Obrázky (*.jpg *.jpeg *.png *.webp *.bmp)",
        )
        for f in files:
            try:
                name = photo_service.import_photo(Path(f), self.photos_dir)
            except photo_service.PhotoImportError as exc:
                QMessageBox.warning(self, "Chyba", str(exc))
                continue
            is_primary = not any(p.is_primary for p in self._photos)
            self._photos.append(
                Photo(file_name=name, is_primary=is_primary, sort_order=len(self._photos))
            )
        self._refresh()

    def _on_set_primary(self) -> None:
        idx = self._selected_index()
        if idx is None:
            return
        for i, p in enumerate(self._photos):
            p.is_primary = i == idx
        self._refresh()

    def _on_remove(self) -> None:
        idx = self._selected_index()
        if idx is None:
            return
        photo = self._photos.pop(idx)
        photo_service.delete_photo_file(photo.file_name, self.photos_dir)
        if photo.is_primary and self._photos:
            self._photos[0].is_primary = True
        self._refresh()
