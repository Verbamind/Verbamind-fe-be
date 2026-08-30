"""Circular loading spinner — shown only while AI processing runs."""

from PySide6.QtCore import QRectF, Qt, QTimer
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QWidget


class Spinner(QWidget):
    def __init__(
        self,
        parent=None,
        size: int = 44,
        color: str = "#0a5fc4",
        thickness: int = 4,
    ):
        super().__init__(parent)
        self._angle = 0
        self._color = QColor(color)
        self._thickness = thickness
        self.setFixedSize(size, size)
        self.setVisible(False)
        self._timer = QTimer(self)
        self._timer.setInterval(25)
        self._timer.timeout.connect(self._rotate)

    def start(self):
        self.setVisible(True)
        self._timer.start()

    def stop(self):
        self._timer.stop()
        self.setVisible(False)

    def _rotate(self):
        self._angle = (self._angle + 10) % 360
        self.update()

    def paintEvent(self, event):  # noqa: N802 — Qt override
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        pen = QPen(self._color, self._thickness)
        pen.setCapStyle(Qt.RoundCap)
        painter.setPen(pen)
        rect = QRectF(
            self._thickness / 2,
            self._thickness / 2,
            self.width() - self._thickness,
            self.height() - self._thickness,
        )
        painter.drawArc(rect, -self._angle * 16, 270 * 16)
