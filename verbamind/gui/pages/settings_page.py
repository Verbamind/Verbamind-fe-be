"""Settings page — database info, audio config, license info."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)


class SettingsPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        title = QLabel("Settings")
        title.setObjectName("section_title")

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setSpacing(12)

        db_group = QGroupBox("Database")
        db_layout = QVBoxLayout(db_group)
        db_layout.setSpacing(8)
        from verbamind.config.config import get_database_url
        db_path = QLabel(get_database_url())
        db_path.setObjectName("db_path_label")
        db_path.setWordWrap(True)
        db_path.setStyleSheet("font-size: 11.5px; font-family: 'Consolas', monospace; color: #5a5a5a;")
        db_layout.addWidget(db_path)
        content_layout.addWidget(db_group)

        audio_group = QGroupBox("Audio")
        audio_layout = QVBoxLayout(audio_group)
        audio_layout.setSpacing(8)
        audio_row = QHBoxLayout()
        audio_row.addWidget(QLabel("Sample Rate:"))
        sr_input = QLineEdit("16000")
        sr_input.setFixedWidth(100)
        audio_row.addWidget(sr_input)
        audio_row.addStretch()
        channel_row = QHBoxLayout()
        channel_row.addWidget(QLabel("Channels:"))
        ch_input = QLineEdit("2")
        ch_input.setFixedWidth(60)
        channel_row.addWidget(ch_input)
        channel_row.addStretch()
        audio_layout.addLayout(audio_row)
        audio_layout.addLayout(channel_row)
        content_layout.addWidget(audio_group)

        license_group = QGroupBox("License")
        license_layout = QVBoxLayout(license_group)
        license_layout.setSpacing(8)
        try:
            from verbamind.security.activation import get_hardware_id
            hwid = get_hardware_id()
        except Exception:
            hwid = "Unavailable"
        hwid_label = QLabel(f"Hardware ID: {hwid}")
        hwid_label.setWordWrap(True)
        hwid_label.setStyleSheet("font-size: 11.5px; font-family: 'Consolas', monospace; color: #5a5a5a;")
        license_layout.addWidget(hwid_label)
        content_layout.addWidget(license_group)

        content_layout.addStretch()

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(content)

        layout.addWidget(title)
        layout.addWidget(scroll, 1)
