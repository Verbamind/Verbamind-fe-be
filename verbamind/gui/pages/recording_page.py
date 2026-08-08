"""Recording page — dual column audio config, VU meter, record/playback controls."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from verbamind.gui.widgets.device_config import DeviceConfig
from verbamind.gui.widgets.status_led import StatusLED


def _led_row(label_text, parent=None):
    row = QHBoxLayout()
    row.setSpacing(8)
    led = StatusLED(parent)
    lbl = QLabel(label_text)
    lbl.setStyleSheet("font-size: 12px; color: #1a1a1a;")
    row.addWidget(led)
    row.addWidget(lbl)
    row.addStretch()
    return row, led


def _level_meter(parent=None):
    bar = QWidget(parent)
    bar.setFixedHeight(18)
    bar.setStyleSheet(
        "background: #ffffff; border: 1px solid #b1b1b1; border-radius: 2px;"
    )
    layout = QHBoxLayout(bar)
    layout.setContentsMargins(4, 3, 4, 3)
    layout.setSpacing(2)
    colors = ["#2ecc57"] * 4 + ["#c8790b"] * 3 + ["#c0392b"] * 3
    for c in colors:
        seg = QLabel()
        seg.setFixedHeight(12)
        seg.setStyleSheet(f"background: {c}; border-radius: 1px;")
        layout.addWidget(seg, 1)
    return bar


class RecordingPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        title = QLabel("Recording Session")
        title.setObjectName("section_title")

        audio_grid = QHBoxLayout()
        audio_grid.setSpacing(18)

        patient_col = QVBoxLayout()
        patient_col.setSpacing(10)
        patient_label = QLabel("Patient Microphone")
        patient_label.setStyleSheet("font-size: 11.5px; font-weight: 600; color: #5a5a5a;")
        self._patient_config = DeviceConfig(self)
        patient_combo = self._patient_config.patient_combo
        patient_combo.setObjectName("patient_combo")
        patient_row, self._patient_led = _led_row("Patient Channel")
        patient_meter = _level_meter()
        patient_vol = QSlider(Qt.Horizontal)
        patient_vol.setValue(75)
        patient_col.addWidget(patient_label)
        patient_col.addWidget(self._patient_config)
        patient_col.addLayout(patient_row)
        patient_col.addWidget(patient_meter)
        patient_col.addWidget(patient_vol)

        psych_col = QVBoxLayout()
        psych_col.setSpacing(10)
        psych_label = QLabel("Psychologist Microphone")
        psych_label.setStyleSheet("font-size: 11.5px; font-weight: 600; color: #5a5a5a;")
        self._psych_config = DeviceConfig(self)
        psych_combo = self._psych_config.patient_combo
        psych_combo.setObjectName("psychologist_combo")
        psych_row, self._psych_led = _led_row("Psychologist Channel")
        psych_meter = _level_meter()
        psych_vol = QSlider(Qt.Horizontal)
        psych_vol.setValue(60)
        psych_col.addWidget(psych_label)
        psych_col.addWidget(self._psych_config)
        psych_col.addLayout(psych_row)
        psych_col.addWidget(psych_meter)
        psych_col.addWidget(psych_vol)

        audio_grid.addLayout(patient_col, 1)
        sep = QWidget()
        sep.setFixedWidth(1)
        sep.setStyleSheet("background: #b1b1b1;")
        audio_grid.addWidget(sep)
        audio_grid.addLayout(psych_col, 1)

        audio_group = QGroupBox("Audio Configuration")
        audio_group_layout = QVBoxLayout(audio_group)
        audio_group_layout.addLayout(audio_grid)

        controls = QHBoxLayout()
        controls.setSpacing(10)
        self._record_btn = QPushButton("⬤  Record")
        self._record_btn.setObjectName("record_btn")
        self._pause_btn = QPushButton("⏸  Pause")
        self._pause_btn.setEnabled(False)
        self._stop_btn = QPushButton("⏹  Stop")
        self._stop_btn.setEnabled(False)

        self._record_btn.clicked.connect(self._on_record)
        self._pause_btn.clicked.connect(self._on_pause)
        self._stop_btn.clicked.connect(self._on_stop)

        controls.addWidget(self._record_btn)
        controls.addWidget(self._pause_btn)
        controls.addWidget(self._stop_btn)
        controls.addStretch()

        layout.addWidget(title)
        layout.addWidget(audio_group)
        layout.addLayout(controls)

        player_bar = QWidget()
        player_bar.setStyleSheet(
            "background: #ffffff; border: 1px solid #b1b1b1; border-radius: 2px;"
        )
        player_layout = QHBoxLayout(player_bar)
        player_layout.setContentsMargins(10, 8, 10, 8)
        player_layout.setSpacing(10)
        play_btn = QPushButton("▶")
        play_btn.setFixedSize(32, 32)
        play_btn.setStyleSheet(
            "QPushButton { background: qlineargradient(x1:0 y1:0, x2:0 y2:1, "
            "stop:0 #1a78d6, stop:1 #0a5fc4); color: #ffffff; border: 1px solid #08519f; "
            "border-radius: 16px; font-size: 13px; }"
            "QPushButton:hover { background: qlineargradient(x1:0 y1:0, x2:0 y2:1, "
            "stop:0 #2286e6, stop:1 #0f6ad3); }"
        )
        track = QLabel("")
        track.setFixedHeight(8)
        track.setStyleSheet("background: #e2e2e2; border-radius: 4px;")
        time_lbl = QLabel("00:00 / 00:00")
        time_lbl.setStyleSheet("font-size: 11px; color: #5a5a5a; min-width: 78px;")
        player_layout.addWidget(play_btn)
        player_layout.addWidget(track, 1)
        player_layout.addWidget(time_lbl)
        layout.addWidget(player_bar)
        layout.addStretch()

    def _on_record(self):
        self._record_btn.setEnabled(False)
        self._pause_btn.setEnabled(True)
        self._stop_btn.setEnabled(True)

    def _on_pause(self):
        self._pause_btn.setEnabled(False)
        self._record_btn.setEnabled(True)

    def _on_stop(self):
        self._record_btn.setEnabled(True)
        self._pause_btn.setEnabled(False)
        self._stop_btn.setEnabled(False)
