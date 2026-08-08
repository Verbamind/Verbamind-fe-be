"""Settings page — database info, audio config, license info."""

from PySide6.QtWidgets import (
    QGroupBox,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)


class SettingsPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)

        title = QLabel("Settings")
        title.setObjectName("section_title")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #1a1a1a;")

        content = QWidget()
        content_layout = QVBoxLayout(content)

        db_group = QGroupBox("Database")
        db_layout = QVBoxLayout(db_group)
        from verbamind.config.config import get_database_url

        db_path = QLabel(get_database_url())
        db_path.setObjectName("db_path_label")
        db_path.setWordWrap(True)
        db_path.setStyleSheet("font-size: 12px; color: #5a5a5a;")
        db_layout.addWidget(db_path)
        content_layout.addWidget(db_group)

        audio_group = QGroupBox("Audio")
        audio_layout = QVBoxLayout(audio_group)
        audio_info = QLabel("Dual-channel recording configured via Recording page.")
        audio_info.setWordWrap(True)
        audio_layout.addWidget(audio_info)
        content_layout.addWidget(audio_group)

        content_layout.addStretch()

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(content)
        scroll.setStyleSheet("QScrollArea { border: none; background: #f0f0f0; }")

        layout.addWidget(title)
        layout.addSpacing(8)
        layout.addWidget(scroll, 1)
