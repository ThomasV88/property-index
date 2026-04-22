from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QEvent, QRect, QSize, Qt, QUrl
from PySide6.QtGui import (
    QBrush,
    QColor,
    QDesktopServices,
    QFont,
    QPainter,
    QPen,
    QPixmap,
    QPixmapCache,
)
from PySide6.QtWidgets import QStyle, QStyledItemDelegate, QStyleOptionViewItem

from house_index.domain.enums import STATUS_LABELS_SK, Status
from house_index.domain.models import Property
from house_index.ui.property_model import PropertyRole

CARD_WIDTH = 320
CARD_HEIGHT = 280
TITLE_HEIGHT = 30
PHOTO_SIZE = 110
BADGE_W = 60
BADGE_H = 34
PADDING = 10
LINK_SIZE = 28

STATUS_COLORS = {
    Status.INTERESTED: "#1d63b8",
    Status.VISITED: "#6a46b4",
    Status.REJECTED: "#666666",
    Status.RESERVED: "#b66f1f",
}


def index_color(score: float | None) -> QColor:
    if score is None:
        return QColor("#8a8a8a")
    if score >= 95:
        return QColor("#0f7a2e")
    if score >= 80:
        return QColor("#2f9d46")
    if score >= 65:
        return QColor("#c88a1d")
    if score >= 45:
        return QColor("#c26325")
    return QColor("#b8352f")


def format_price_pln(price: int | None) -> str:
    if price is None:
        return "— PLN"
    return f"{price:,} PLN".replace(",", " ")


def format_price_eur(price_pln: int | None, rate: float) -> str:
    if price_pln is None or rate <= 0:
        return "— EUR"
    eur = price_pln * rate
    return f"≈ {eur:,.0f} EUR".replace(",", " ")


def _photo_pixmap(path: Path | None, size: int) -> QPixmap | None:
    if path is None or not path.exists():
        return None
    key = f"{path}:{size}"
    cached = QPixmapCache.find(key)
    if cached:
        return cached
    pm = QPixmap(str(path))
    if pm.isNull():
        return None
    scaled = pm.scaled(size, size, Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                       Qt.TransformationMode.SmoothTransformation)
    QPixmapCache.insert(key, scaled)
    return scaled


class PropertyCardDelegate(QStyledItemDelegate):
    def __init__(self, photos_dir: Path, parent=None):
        super().__init__(parent)
        self.photos_dir = photos_dir
        self.eur_rate: float = 0.235

    def set_eur_rate(self, rate: float) -> None:
        self.eur_rate = rate

    def sizeHint(self, option: QStyleOptionViewItem, index) -> QSize:  # noqa: N802
        return QSize(CARD_WIDTH, CARD_HEIGHT)

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index) -> None:
        prop: Property | None = index.data(PropertyRole)
        if prop is None:
            return

        rect = option.rect.adjusted(6, 6, -6, -6)
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        is_selected = bool(option.state & QStyle.StateFlag.State_Selected)
        bg = QColor("#e8f0fb") if is_selected else QColor("#ffffff")
        border = QColor("#3b82f6") if is_selected else QColor("#d0d0d0")

        painter.setPen(QPen(border, 1))
        painter.setBrush(QBrush(bg))
        painter.drawRoundedRect(rect, 8, 8)

        title_rect = QRect(
            rect.left() + PADDING,
            rect.top() + PADDING,
            rect.width() - 2 * PADDING,
            TITLE_HEIGHT,
        )
        self._paint_title(painter, title_rect, prop.title)

        body_top = title_rect.bottom() + 6
        photo_rect = QRect(rect.left() + PADDING, body_top, PHOTO_SIZE, PHOTO_SIZE)
        self._paint_photo(painter, photo_rect, prop)

        details_x = photo_rect.right() + PADDING
        details_right = rect.right() - PADDING

        badge_rect = QRect(details_right - BADGE_W, body_top, BADGE_W, BADGE_H)
        self._paint_index_badge(painter, badge_rect, prop.index_score)

        self._paint_details(painter, prop, details_x, body_top, details_right)

        self._paint_status_pill(painter, rect, prop.status)
        self._paint_link_button(painter, rect, prop)

        painter.restore()

    def _paint_title(self, painter: QPainter, rect: QRect, title: str) -> None:
        font = QFont()
        font.setPointSize(11)
        font.setBold(True)
        painter.setFont(font)
        painter.setPen(QPen(QColor("#1a1a1a")))
        fm = painter.fontMetrics()
        elided = fm.elidedText(title, Qt.TextElideMode.ElideRight, rect.width())
        painter.drawText(
            rect,
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
            elided,
        )

    def _paint_photo(self, painter: QPainter, rect: QRect, prop: Property) -> None:
        primary = prop.primary_photo
        pm = None
        if primary is not None:
            pm = _photo_pixmap(self.photos_dir / primary.file_name, PHOTO_SIZE)
        if pm is not None:
            painter.save()
            painter.setClipRect(rect)
            painter.drawPixmap(rect.topLeft(), pm)
            painter.restore()
            painter.setPen(QPen(QColor("#d0d0d0"), 1))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRoundedRect(rect, 6, 6)
            return
        painter.setPen(QPen(QColor("#d0d0d0"), 1))
        painter.setBrush(QBrush(QColor("#f4f4f4")))
        painter.drawRoundedRect(rect, 6, 6)
        painter.setPen(QPen(QColor("#999")))
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, "bez fotky")

    def _paint_index_badge(self, painter: QPainter, rect: QRect, score: float | None) -> None:
        color = index_color(score)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(color))
        painter.drawRoundedRect(rect, 6, 6)

        painter.setPen(QPen(QColor("#ffffff")))
        font = QFont()
        font.setBold(True)
        font.setPointSize(13)
        painter.setFont(font)
        label = f"{score:.0f}" if score is not None else "—"
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, label)

    def _paint_details(
        self, painter: QPainter, prop: Property, x: int, top: int, right: int
    ) -> None:
        font = QFont()
        font.setPointSize(9)
        painter.setFont(font)

        painter.setPen(QPen(QColor("#1a1a1a")))
        painter.drawText(x, top + 14, format_price_pln(prop.price_pln))

        painter.setPen(QPen(QColor("#555555")))
        painter.drawText(x, top + 30, format_price_eur(prop.price_pln, self.eur_rate))

        painter.setPen(QPen(QColor("#444444")))
        area = f"{prop.area_m2:g} m²" if prop.area_m2 else "— m²"
        distance = (
            f"{prop.distance_km:g} km" if prop.distance_km is not None else "— km"
        )
        lines = [f"{area} · {distance}"]
        if prop.rooms:
            lines.append(f"{prop.rooms} izieb · {prop.property_type.value}")
        else:
            lines.append(prop.property_type.value)
        if prop.price_per_m2:
            ppm = f"{prop.price_per_m2:,.0f} PLN/m²".replace(",", " ")
            lines.append(ppm)

        y = top + 50
        for line in lines:
            painter.drawText(x, y, line)
            y += 16

    def _paint_status_pill(self, painter: QPainter, card_rect: QRect, status: Status) -> None:
        label = STATUS_LABELS_SK[status]
        color = QColor(STATUS_COLORS[status])
        font = QFont()
        font.setPointSize(8)
        painter.setFont(font)
        metrics = painter.fontMetrics()
        w = metrics.horizontalAdvance(label) + 18
        h = 22
        x = card_rect.left() + PADDING
        y = card_rect.bottom() - PADDING - h
        pill = QRect(x, y, w, h)

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(color))
        painter.drawRoundedRect(pill, 11, 11)

        painter.setPen(QPen(QColor("#ffffff")))
        painter.drawText(pill, Qt.AlignmentFlag.AlignCenter, label)

    def _link_rect(self, card_rect: QRect) -> QRect:
        x = card_rect.right() - PADDING - LINK_SIZE - 60
        y = card_rect.bottom() - PADDING - LINK_SIZE
        return QRect(x, y, LINK_SIZE + 60, LINK_SIZE)

    def _paint_link_button(self, painter: QPainter, card_rect: QRect, prop: Property) -> None:
        if not prop.primary_link:
            return
        btn = self._link_rect(card_rect)
        painter.setPen(QPen(QColor("#3b82f6"), 1))
        painter.setBrush(QBrush(QColor("#eaf2ff")))
        painter.drawRoundedRect(btn, 6, 6)
        font = QFont()
        font.setPointSize(9)
        font.setBold(True)
        painter.setFont(font)
        painter.setPen(QPen(QColor("#1d4ed8")))
        painter.drawText(btn, Qt.AlignmentFlag.AlignCenter, "Otvoriť ↗")

    def editorEvent(self, event, model, option, index) -> bool:  # noqa: N802
        if event.type() == QEvent.Type.MouseButtonRelease:
            prop: Property | None = index.data(PropertyRole)
            if prop and prop.primary_link:
                rect = option.rect.adjusted(6, 6, -6, -6)
                btn = self._link_rect(rect)
                if btn.contains(event.pos()):
                    QDesktopServices.openUrl(QUrl(prop.primary_link))
                    return True
        return super().editorEvent(event, model, option, index)
