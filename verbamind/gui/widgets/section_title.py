"""SectionTitle — reusable page header with proper spacing and separator line.

Uses QFrame separator instead of border-bottom in QSS (which clips text in Qt).
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget


class SectionTitle(QWidget):
    """Page title with bold text + horizontal separator line below."""

    def __init__(self, text: str, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self._label = QLabel(text)
        self._label.setStyleSheet(
            "font-size: 15px; font-weight: 600; color: #1a1a1a; "
            "background: transparent; padding: 0; margin: 0;"
        )
        self._label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Plain)
        separator.setStyleSheet(
            "QFrame { background: #b1b1b1; border: none; max-height: 1px; }"
        )
        separator.setFixedHeight(1)

        layout.addWidget(self._label)
        layout.addWidget(separator)

    def text(self) -> str:
        return self._label.text()

    def set_text(self, text: str) -> None:
        self._label.setText(text)
