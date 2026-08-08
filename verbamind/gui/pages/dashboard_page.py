"""Dashboard page — welcome screen with session overview."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class DashboardPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)

        title = QLabel("Welcome to VerbaMind")
        title.setObjectName("section_title")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #1a1a1a;")

        subtitle = QLabel("AI-Assisted Counseling Session Documentation")
        subtitle.setStyleSheet("font-size: 14px; color: #5a5a5a; margin-bottom: 16px;")

        welcome = QLabel("Select a session from the sidebar or start a new recording.")
        welcome.setObjectName("welcome_label")
        welcome.setWordWrap(True)
        welcome.setStyleSheet("font-size: 13px; color: #5a5a5a;")

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(20)
        layout.addWidget(welcome)
        layout.addStretch()
