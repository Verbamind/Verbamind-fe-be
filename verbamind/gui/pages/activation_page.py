"""Activation page — HWID display, license key input, activation flow."""

from PySide6.QtCore import Qt
from verbamind.gui.widgets.section_title import SectionTitle
from PySide6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class ActivationPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        title = SectionTitle("Aktivasi Lisensi")

        hwid_group = QGroupBox("Hardware ID")
        hwid_layout = QVBoxLayout(hwid_group)
        try:
            from verbamind.security.activation import get_hardware_id
            hwid = get_hardware_id()
        except Exception:
            hwid = "Unavailable"
        hwid_label = QLabel(hwid)
        hwid_label.setWordWrap(True)
        hwid_label.setStyleSheet(
            "font-size: 12px; font-family: 'Consolas', monospace; color: #5a5a5a; "
            "background: #f9f9f9; padding: 8px; border: 1px solid #b1b1b1; border-radius: 2px;"
        )
        hwid_layout.addWidget(hwid_label)

        license_group = QGroupBox("Enter License Key")
        license_layout = QVBoxLayout(license_group)
        license_layout.setSpacing(10)
        self._license_input = QLineEdit()
        self._license_input.setPlaceholderText("XXXX-XXXX-XXXX-XXXX")
        self._license_input.setStyleSheet(
            "font-family: 'Consolas', monospace; font-size: 15px; padding: 10px; "
            "letter-spacing: 3px;"
        )

        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)
        self._activate_btn = QPushButton("Activate License")
        self._activate_btn.setObjectName("primary_btn")
        btn_row.addWidget(self._activate_btn)
        btn_row.addStretch()
        license_layout.addWidget(self._license_input)
        license_layout.addLayout(btn_row)

        self._status_label = QLabel("")
        self._status_label.setObjectName("activation_status")
        self._status_label.setAlignment(Qt.AlignCenter)
        self._status_label.setWordWrap(True)
        self._status_label.setStyleSheet("font-size: 12.5px; padding: 10px;")

        self._activate_btn.clicked.connect(self._on_activate)

        layout.addWidget(title)
        layout.addWidget(hwid_group)
        layout.addWidget(license_group)
        layout.addWidget(self._status_label)
        layout.addStretch()

    def _on_activate(self):
        key = self._license_input.text().strip()
        if not key:
            self.show_status("Please enter a license key.", success=False)
            return
        try:
            from verbamind.security.activation import activate, get_hardware_id, validate_license_key
            hwid = get_hardware_id()
            if validate_license_key(key, hwid, "secret-master-key"):
                activate(key)
                self.show_status("✓ Activation successful — VerbaMind is ready.", success=True)
                self._activate_btn.setEnabled(False)
                self._license_input.setEnabled(False)
            else:
                self.show_status("✗ Invalid license key. Please check and try again.", success=False)
        except Exception as e:
            self.show_status(f"Activation error: {e}", success=False)

    def show_status(self, message: str, success: bool = False) -> None:
        self._status_label.setText(message)
        color = "#2e7d32" if success else "#c0392b"
        bg = "#e8f5e9" if success else "#fce4e4"
        self._status_label.setStyleSheet(
            f"font-size: 12.5px; padding: 10px; color: {color}; "
            f"background: {bg}; border-radius: 2px; font-weight: 600;"
        )
