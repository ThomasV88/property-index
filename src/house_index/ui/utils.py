from __future__ import annotations

from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QWidget


def fit_to_screen(widget: QWidget, margin: int = 50) -> None:
    """Obmedzí veľkosť widgetu tak aby sa zmestil na obrazovku s margin-om okolo."""
    screen = widget.screen() if widget.screen() else QGuiApplication.primaryScreen()
    if screen is None:
        return
    available = screen.availableGeometry()

    max_w = max(400, available.width() - 2 * margin)
    max_h = max(400, available.height() - 2 * margin)

    new_w = min(widget.width(), max_w)
    new_h = min(widget.height(), max_h)
    if (new_w, new_h) != (widget.width(), widget.height()):
        widget.resize(new_w, new_h)

    widget.setMaximumSize(max_w, max_h)

    x = available.left() + (available.width() - widget.width()) // 2
    y = available.top() + margin
    if widget.height() < available.height() - 2 * margin:
        y = available.top() + (available.height() - widget.height()) // 2
    widget.move(x, y)
