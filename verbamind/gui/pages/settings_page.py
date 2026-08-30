"""Settings page — database info, audio config, license info."""

from PySide6.QtWidgets import (
    QGroupBox,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from verbamind.gui.widgets.section_title import SectionTitle


class SettingsPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        title = SectionTitle("Pengaturan")

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setSpacing(12)

        db_group = QGroupBox("Basis Data")
        db_layout = QVBoxLayout(db_group)
        db_layout.setSpacing(8)
        from verbamind.config.config import get_database_url
        db_path = QLabel(get_database_url())
        db_path.setObjectName("db_path_label")
        db_path.setWordWrap(True)
        db_path.setStyleSheet("font-size: 11.5px; font-family: 'Consolas', monospace; color: #5a5a5a;")
        db_layout.addWidget(db_path)
        content_layout.addWidget(db_group)

        license_group = QGroupBox("Lisensi")
        license_layout = QVBoxLayout(license_group)
        license_layout.setSpacing(8)
        try:
            from verbamind.security.activation import get_hardware_id
            hwid = get_hardware_id()
        except Exception:
            hwid = "Unavailable"
        hwid_label = QLabel(f"ID Perangkat: {hwid}")
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
