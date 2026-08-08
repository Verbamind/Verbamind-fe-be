"""Sidebar navigation — Windows classic with dot indicators + left accent border."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QBrush, QColor, QFont, QIcon, QPainter, QPixmap
from PySide6.QtWidgets import QListWidget, QListWidgetItem


def _make_dot_icon(size=8, color="#8fa6bd"):
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setBrush(QColor(color))
    painter.setPen(Qt.NoPen)
    painter.drawEllipse(0, 0, size, size)
    painter.end()
    return QIcon(pixmap)


class Sidebar(QListWidget):
    navigation_changed = Signal(int)

    ITEMS = [
        ("Dashboard", "📊"),
        ("Recording", "🎙"),
        ("Patients", "👤"),
        ("Audit Log", "📋"),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("sidebar")
        self.setFixedWidth(190)
        self.setSpacing(0)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        icon = _make_dot_icon()

        for label, emoji in self.ITEMS:
            item = QListWidgetItem(f"  {emoji}  {label}")
            item.setIcon(icon)
            self.addItem(item)

        self.setCurrentRow(0)
        self.currentRowChanged.connect(self.navigation_changed.emit)
