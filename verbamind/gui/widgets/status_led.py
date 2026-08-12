"""Status LED — green with glow when recording, gray when idle."""

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QWidget


class StatusLED(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._active = False
        self.setFixedSize(14, 14)

    @property
    def state(self) -> str:
        return "recording" if self._active else "idle"

    def set_active(self, active: bool) -> None:
        self._active = active
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        if self._active:
            color = QColor("#2ecc57")
            painter.setBrush(color)
            painter.setPen(QPen(QColor("#27ae60"), 1))
            painter.drawEllipse(1, 1, 11, 11)
            glow = QColor("#2ecc57")
            glow.setAlpha(60)
            painter.setBrush(glow)
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(-1, -1, 15, 15)
        else:
            color = QColor("#c9c9c9")
            painter.setBrush(color)
            painter.setPen(QPen(QColor("#999999"), 1))
            painter.drawEllipse(1, 1, 11, 11)
