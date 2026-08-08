"""Recording page — dual-channel config, record/stop/pause, status LED."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from verbamind.gui.widgets.device_config import DeviceConfig
from verbamind.gui.widgets.status_led import StatusLED


class RecordingPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)

        title = QLabel("Recording Session")
        title.setObjectName("section_title")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #1a1a1a;")

        self._status_led = StatusLED()
        self._status_label = QLabel("Ready")
        self._status_label.setStyleSheet("font-size: 13px; color: #5a5a5a;")
        status_layout = QHBoxLayout()
        status_layout.addWidget(self._status_led)
        status_layout.addWidget(self._status_label)
        status_layout.addStretch()

        device_group = QGroupBox("Audio Configuration")
        self._device_config = DeviceConfig()
        device_layout = QVBoxLayout(device_group)
        device_layout.addWidget(self._device_config)

        controls_layout = QHBoxLayout()
        self._record_btn = QPushButton("⬤ Record")
        self._record_btn.setObjectName("record_btn")
        self._pause_btn = QPushButton("Pause")
        self._stop_btn = QPushButton("Stop")
        self._pause_btn.setEnabled(False)
        self._stop_btn.setEnabled(False)

        self._record_btn.clicked.connect(self._on_record)
        self._pause_btn.clicked.connect(self._on_pause)
        self._stop_btn.clicked.connect(self._on_stop)

        controls_layout.addWidget(self._record_btn)
        controls_layout.addWidget(self._pause_btn)
        controls_layout.addWidget(self._stop_btn)
        controls_layout.addStretch()

        layout.addWidget(title)
        layout.addSpacing(8)
        layout.addLayout(status_layout)
        layout.addSpacing(16)
        layout.addWidget(device_group)
        layout.addSpacing(16)
        layout.addLayout(controls_layout)
        layout.addStretch()

    def _on_record(self):
        self._status_led.set_active(True)
        self._status_label.setText("Recording...")
        self._record_btn.setEnabled(False)
        self._pause_btn.setEnabled(True)
        self._stop_btn.setEnabled(True)

    def _on_pause(self):
        self._status_led.set_active(False)
        self._status_label.setText("Paused")
        self._pause_btn.setEnabled(False)
        self._record_btn.setEnabled(True)

    def _on_stop(self):
        self._status_led.set_active(False)
        self._status_label.setText("Ready")
        self._record_btn.setEnabled(True)
        self._pause_btn.setEnabled(False)
        self._stop_btn.setEnabled(False)
