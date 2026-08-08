"""Status LED widget — green when recording, gray when idle."""

from PySide6.QtCore import QSize
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import QWidget


class StatusLED(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._active = False
        self.setFixedSize(16, 16)

    @property
    def state(self) -> str:
        return "recording" if self._active else "idle"

    def set_active(self, active: bool) -> None:
        self._active = active
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        color = QColor("#2ecc57") if self._active else QColor("#c9c9c9")
        painter.setBrush(color)
        painter.setPen(QColor("#b1b1b1"))
        painter.drawEllipse(2, 2, 12, 12)
