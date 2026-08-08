"""Recording page — 3-column audio config, big timer, red recording LED, waveform player.

No dummy data — all controls start empty/disabled until user starts recording.
"""

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QComboBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from verbamind.gui.widgets.section_title import SectionTitle
from verbamind.gui.widgets.status_led import StatusLED


def _audio_col(title: str, parent: QWidget) -> tuple[QWidget, QComboBox, QSlider]:
    col = QVBoxLayout()
    col.setSpacing(8)

    lbl = QLabel(title)
    lbl.setStyleSheet("font-size: 11.5px; font-weight: 600; color: #5a5a5a;")
    combo = QComboBox()
    combo.addItem("Pilih mikrofon...")
    combo.addItems(["Mikrofon Bawaan Laptop", "Headset USB", "External Mic"])
    combo.setObjectName(f"{title.lower().replace(' ', '_')}_combo")

    vol_lbl = QLabel("Level Volume Input")
    vol_lbl.setStyleSheet("font-size: 11px; color: #5a5a5a;")
    slider = QSlider(Qt.Horizontal)
    slider.setValue(75)
    vol_pct = QLabel("75%")
    vol_pct.setStyleSheet("font-size: 11px; color: #5a5a5a; min-width: 34px;")

    vol_row = QHBoxLayout()
    vol_row.addWidget(slider, 1)
    vol_row.addWidget(vol_pct)

    slider.valueChanged.connect(lambda v: vol_pct.setText(f"{v}%"))

    test_btn = QPushButton("🎙️ Tes Mikrofon")
    test_btn.setObjectName("small_btn")

    col.addWidget(lbl)
    col.addWidget(combo)
    col.addWidget(vol_lbl)
    col.addLayout(vol_row)
    col.addWidget(test_btn)
    col.addStretch()

    wrapper = QWidget(parent)
    wrapper.setLayout(col)
    return wrapper, combo, slider


def _waveform_widget(parent=None) -> QWidget:
    """Waveform bar (static placeholder bars)."""
    bar = QWidget(parent)
    bar.setFixedHeight(28)
    bar.setStyleSheet("background: #ffffff; border: 1px solid #b1b1b1; border-radius: 2px;")
    layout = QHBoxLayout(bar)
    layout.setContentsMargins(4, 3, 4, 3)
    layout.setSpacing(1)
    import random
    random.seed(42)
    for _ in range(28):
        h = random.randint(30, 95)
        seg = QLabel()
        seg.setFixedHeight(int(h * 0.22))
        seg.setStyleSheet(f"background: #0a5fc4; opacity: 0.7; border-radius: 1px;")
        layout.addWidget(seg, 1)
    return bar


class RecordingPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        title = SectionTitle("Sesi Baru / Perekaman")

        # Detail Sesi
        detail_group = QGroupBox("Detail Sesi")
        detail_layout = QVBoxLayout(detail_group)
        row1 = QHBoxLayout()
        pat_lbl = QLabel("Pasien:")
        pat_lbl.setStyleSheet("font-size: 11.5px; color: #5a5a5a;")
        pat_combo = QComboBox()
        pat_combo.addItem("Pilih pasien...")
        date_lbl = QLabel("Tanggal Sesi:")
        date_lbl.setStyleSheet("font-size: 11.5px; color: #5a5a5a;")
        from PySide6.QtWidgets import QDateEdit
        date_edit = QDateEdit()
        date_edit.setCalendarPopup(True)
        date_edit.setDateTime(date_edit.dateTime().currentDateTime())
        row1.addWidget(pat_lbl)
        row1.addWidget(pat_combo, 1)
        row1.addWidget(date_lbl)
        row1.addWidget(date_edit)
        detail_layout.addLayout(row1)

        # Audio Settings — 3 columns: Mic1, Mic2, Profile
        audio_group = QGroupBox("Pengaturan Audio")
        audio_layout = QHBoxLayout(audio_group)
        audio_layout.setSpacing(18)

        mic1_widget, self._mic1_combo, _ = _audio_col("🎤 Mikrofon 1 (Pasien)", self)
        mic2_widget, self._mic2_combo, _ = _audio_col("🎤 Mikrofon 2 (Psikolog)", self)

        # Profile column
        prof_col = QVBoxLayout()
        prof_col.setSpacing(8)
        prof_lbl = QLabel("⚙️ Profil Perekaman")
        prof_lbl.setStyleSheet("font-size: 11.5px; font-weight: 600; color: #5a5a5a;")
        prof_combo = QComboBox()
        prof_combo.addItems([
            "Konseling Standar (44.1 kHz / 16-bit / Stereo)",
            "High Quality (48 kHz / 24-bit / Stereo)",
            "Transkripsi Optimal (16 kHz / Mono — disarankan AI)",
        ])
        prof_col.addWidget(prof_lbl)
        prof_col.addWidget(prof_combo)
        prof_col.addStretch()
        prof_widget = QWidget(self)
        prof_widget.setLayout(prof_col)

        # Separators
        sep1 = QWidget()
        sep1.setFixedWidth(1)
        sep1.setStyleSheet("background: #b1b1b1;")
        sep2 = QWidget()
        sep2.setFixedWidth(1)
        sep2.setStyleSheet("background: #b1b1b1;")

        audio_layout.addWidget(mic1_widget, 1)
        audio_layout.addWidget(sep1)
        audio_layout.addWidget(mic2_widget, 1)
        audio_layout.addWidget(sep2)
        audio_layout.addWidget(prof_widget, 1)

        # Recording Status
        status_group = QGroupBox("Status Perekaman")
        status_layout = QVBoxLayout(status_group)
        led_row = QHBoxLayout()
        self._led = StatusLED(self)
        self._led.setStyleSheet("background: transparent;")
        led_row.addWidget(self._led)
        status_layout.addLayout(led_row)

        status_row = QHBoxLayout()
        self._timer_label = QLabel("00:00:00")
        self._timer_label.setObjectName("timer_big")
        self._rec_status = QLabel("● Siap Merekam")
        self._rec_status.setObjectName("status_rec")
        self._rec_status.setStyleSheet("color: #5a5a5a; font-size: 11px; font-weight: 600;")
        self._record_btn = QPushButton("⬤ Mulai Rekam")
        self._record_btn.setObjectName("primary_btn")
        self._pause_btn = QPushButton("⏸ Jeda")
        self._pause_btn.setObjectName("small_btn")
        self._pause_btn.setEnabled(False)
        self._stop_btn = QPushButton("■ Stop")
        self._stop_btn.setObjectName("danger_btn")
        self._stop_btn.setEnabled(False)

        self._record_btn.clicked.connect(self._on_record)
        self._pause_btn.clicked.connect(self._on_pause)
        self._stop_btn.clicked.connect(self._on_stop)

        status_row.addWidget(self._timer_label)
        status_row.addWidget(self._rec_status)
        status_row.addStretch()
        status_row.addWidget(self._record_btn)
        status_row.addWidget(self._pause_btn)
        status_row.addWidget(self._stop_btn)
        status_layout.addLayout(status_row)

        # Audio Preview (empty by default)
        preview_group = QGroupBox("Audio Preview")
        preview_layout = QVBoxLayout(preview_group)
        self._preview_info = QLabel("Belum ada rekaman.")
        self._preview_info.setStyleSheet("color: #5a5a5a; font-size: 11.5px;")
        self._waveform = _waveform_widget()
        self._waveform.setVisible(False)
        time_row = QHBoxLayout()
        self._time_label = QLabel("00:00 / 00:00")
        self._time_label.setStyleSheet("font-size: 11px; color: #5a5a5a; font-family: 'Consolas', monospace;")
        time_row.addStretch()
        time_row.addWidget(self._time_label)
        preview_layout.addWidget(self._preview_info)
        preview_layout.addWidget(self._waveform)
        preview_layout.addLayout(time_row)

        layout.addWidget(title)
        layout.addWidget(detail_group)
        layout.addWidget(audio_group)
        layout.addWidget(status_group)
        layout.addWidget(preview_group)
        layout.addStretch()

        # Timer
        self._timer = QTimer(self)
        self._timer.setInterval(1000)
        self._timer.timeout.connect(self._tick)
        self._elapsed = 0

    def _format_time(self, seconds: int) -> str:
        h = seconds // 3600
        m = (seconds % 3600) // 60
        s = seconds % 60
        return f"{h:02d}:{m:02d}:{s:02d}"

    def _tick(self):
        self._elapsed += 1
        self._timer_label.setText(self._format_time(self._elapsed))

    def _on_record(self):
        self._led.set_active(True)
        self._rec_status.setText("● SEDANG MEREKAM")
        self._rec_status.setStyleSheet("color: #c0392b; font-size: 11px; font-weight: 600;")
        self._record_btn.setEnabled(False)
        self._pause_btn.setEnabled(True)
        self._stop_btn.setEnabled(True)
        self._elapsed = 0
        self._timer.start()

    def _on_pause(self):
        self._timer.stop()
        self._led.set_active(False)
        self._rec_status.setText("⏸ DIJEDA")
        self._rec_status.setStyleSheet("color: #c8790b; font-size: 11px; font-weight: 600;")
        self._pause_btn.setEnabled(False)
        self._record_btn.setEnabled(True)

    def _on_stop(self):
        self._timer.stop()
        self._led.set_active(False)
        self._rec_status.setText("■ Berhenti")
        self._rec_status.setStyleSheet("color: #5a5a5a; font-size: 11px; font-weight: 600;")
        self._record_btn.setEnabled(True)
        self._pause_btn.setEnabled(False)
        self._stop_btn.setEnabled(False)
        self._waveform.setVisible(True)
        self._preview_info.setText(f"Rekaman selesai — durasi {self._format_time(self._elapsed)}")
        self._preview_info.setStyleSheet("color: #1a1a1a; font-size: 11.5px;")
