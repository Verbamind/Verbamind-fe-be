"""Activation page — license key input, activation flow, status display."""

from PySide6.QtCore import Qt
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
        layout.setContentsMargins(24, 24, 24, 24)

        title = QLabel("License Activation")
        title.setObjectName("section_title")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #1a1a1a;")

        hwid_group = QGroupBox("Hardware ID")
        hwid_layout = QVBoxLayout(hwid_group)
        try:
            from verbamind.security.activation import get_hardware_id
            hwid = get_hardware_id()
        except Exception:
            hwid = "Unavailable"
        hwid_label = QLabel(hwid)
        hwid_label.setWordWrap(True)
        hwid_label.setStyleSheet("font-size: 12px; font-family: 'Consolas', monospace; color: #5a5a5a;")
        hwid_layout.addWidget(hwid_label)

        license_group = QGroupBox("License Key")
        license_layout = QVBoxLayout(license_group)
        self._license_input = QLineEdit()
        self._license_input.setPlaceholderText("Enter your license key...")
        self._license_input.setStyleSheet("font-family: 'Consolas', monospace; font-size: 14px; padding: 8px;")
        self._activate_btn = QPushButton("Activate")
        license_layout.addWidget(self._license_input)
        license_layout.addWidget(self._activate_btn)

        self._status_label = QLabel("")
        self._status_label.setObjectName("activation_status")
        self._status_label.setAlignment(Qt.AlignCenter)
        self._status_label.setStyleSheet("font-size: 13px; padding: 12px;")

        self._activate_btn.clicked.connect(self._on_activate)

        layout.addWidget(title)
        layout.addSpacing(12)
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
                self.show_status("Activation successful! VerbaMind is ready.", success=True)
                self._activate_btn.setEnabled(False)
                self._license_input.setEnabled(False)
            else:
                self.show_status("Invalid license key. Please check and try again.", success=False)
        except Exception as e:
            self.show_status(f"Activation error: {e}", success=False)

    def show_status(self, message: str, success: bool = False) -> None:
        self._status_label.setText(message)
        color = "#2ecc57" if success else "#dc3545"
        self._status_label.setStyleSheet(f"font-size: 13px; padding: 12px; color: {color}; font-weight: bold;")
