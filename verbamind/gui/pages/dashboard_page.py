"""Dashboard page — welcome screen with session overview."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QGroupBox,
    QLabel,
    QListWidget,
    QVBoxLayout,
    QWidget,
)


class DashboardPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)

        title = QLabel("Welcome to VerbaMind")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #1a1a1a;")

        subtitle = QLabel("AI-Assisted Counseling Session Documentation")
        subtitle.setStyleSheet("font-size: 14px; color: #5a5a5a; margin-bottom: 16px;")

        welcome = QLabel("Select a session from the list below or start a new recording.")
        welcome.setObjectName("welcome_label")
        welcome.setWordWrap(True)
        welcome.setStyleSheet("font-size: 13px; color: #5a5a5a;")

        sessions_group = QGroupBox("Recent Sessions")
        sessions_layout = QVBoxLayout(sessions_group)
        self._session_list = QListWidget()
        self._session_list.setObjectName("session_list")
        self._session_list.setStyleSheet("QListWidget { background: #ffffff; border: 1px solid #b1b1b1; }")
        sessions_layout.addWidget(self._session_list)

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addWidget(welcome)
        layout.addSpacing(16)
        layout.addWidget(sessions_group, 1)

    def load_sessions(self, sessions: list[dict]):
        self._session_list.clear()
        if not sessions:
            self._session_list.addItem("No sessions yet. Start a recording to begin.")
            return
        for s in sessions:
            item_text = f"Session {s['session_id']} — {s.get('created_at', '')[:10]}"
            self._session_list.addItem(item_text)
