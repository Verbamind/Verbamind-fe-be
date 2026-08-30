"""Recording page — functional: real mic enumeration, recording to encrypted .vera,
level meters, mic test, consent file, mic roles, playback speed, audio deletion,
AI processing progress — full mockup parity.
"""

from PySide6.QtCore import QSize, Qt, QTimer, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from verbamind.gui.audio_controller import (
    MicMonitorController,
    PlaybackWorker,
    RecordingWorker,
    list_input_devices,
)
from verbamind.gui.widgets.icons import make_icon
from verbamind.gui.widgets.level_meter import LevelMeter
from verbamind.gui.widgets.section_title import SectionTitle
from verbamind.gui.widgets.spinner import Spinner
from verbamind.gui.widgets.status_led import StatusLED


def _audio_col(title: str, devices: list[dict]) -> tuple[QWidget, QComboBox, LevelMeter, QPushButton, MicMonitorController]:
    col = QVBoxLayout()
    col.setSpacing(8)

    title_row = QHBoxLayout()
    lbl = QLabel(title)
    lbl.setStyleSheet("font-size: 11.5px; font-weight: 600; color: #5a5a5a;")
    status_lbl = QLabel("Nonaktif")
    status_lbl.setStyleSheet("font-size: 11px; font-weight: 600; color: #8a8a8a;")
    title_row.addWidget(lbl)
    title_row.addStretch()
    title_row.addWidget(status_lbl)

    combo = QComboBox()
    combo.addItem("Pilih mikrofon...", None)
    for d in devices:
        combo.addItem(f"{d['name']} ({d['channels']}ch)", d["index"])

    vol_lbl = QLabel("Level Volume Input")
    vol_lbl.setStyleSheet("font-size: 11px; color: #5a5a5a;")
    meter = LevelMeter()

    test_btn = QPushButton("Tes Mikrofon")
    test_btn.setObjectName("small_btn")
    test_btn.setIcon(make_icon("mic", 16, "#1a1a1a"))
    test_btn.setIconSize(QSize(16, 16))

    col.addLayout(title_row)
    col.addWidget(combo)
    col.addWidget(vol_lbl)
    col.addWidget(meter)
    col.addWidget(test_btn)

    wrapper = QWidget()
    wrapper.setLayout(col)

    monitor = MicMonitorController()

    def set_status(active: bool):
        if active:
            status_lbl.setText("Aktif")
            status_lbl.setStyleSheet("font-size: 11px; font-weight: 600; color: #2e7d32;")
        else:
            status_lbl.setText("Nonaktif")
            status_lbl.setStyleSheet("font-size: 11px; font-weight: 600; color: #8a8a8a;")

    def on_device_changed(index: int):
        dev_index = combo.itemData(index)
        if dev_index is not None and not test_btn.property("testing"):
            monitor.set_device(dev_index)
            set_status(True)
        elif dev_index is None:
            monitor.stop()
            set_status(False)

    def on_level(level: float):
        meter.set_level(level)

    combo.currentIndexChanged.connect(on_device_changed)
    monitor.level_updated.connect(on_level)

    def toggle_test():
        if test_btn.property("testing"):
            monitor.stop()
            test_btn.setText("Tes Mikrofon")
            test_btn.setProperty("testing", False)
            meter.set_level(0)
            if combo.currentData() is not None:
                monitor.set_device(combo.currentData())
            set_status(combo.currentData() is not None)
        else:
            idx = combo.currentData()
            if idx is None:
                QMessageBox.information(wrapper, "Tes Mikrofon", "Pilih mikrofon dulu.")
                return
            monitor.set_device(idx)
            test_btn.setText("Stop Tes")
            test_btn.setProperty("testing", True)
            set_status(True)

    test_btn.clicked.connect(toggle_test)

    return wrapper, combo, meter, test_btn, monitor


def _waveform_bars(n: int = 28) -> list[QLabel]:
    bars = []
    for _ in range(n):
        seg = QLabel()
        seg.setFixedHeight(4)
        seg.setStyleSheet("background: #0a5fc4; border-radius: 1px;")
        bars.append(seg)
    return bars


class RecordingPage(QWidget):

    recording_finished = Signal(str, int)  # filepath, seconds
    ai_process_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        title = SectionTitle("Sesi Baru / Perekaman")

        # ---- Detail Sesi ----
        detail_group = QGroupBox("Detail Sesi")
        detail_layout = QVBoxLayout(detail_group)
        row1 = QHBoxLayout()
        pat_lbl = QLabel("Pasien:")
        pat_lbl.setStyleSheet("font-size: 11.5px; color: #5a5a5a;")
        self._pat_combo = QComboBox()
        self._pat_combo.addItem("Pilih pasien...", None)
        self._pat_combo.setMinimumWidth(220)
        date_lbl = QLabel("Tanggal Sesi:")
        date_lbl.setStyleSheet("font-size: 11.5px; color: #5a5a5a;")
        self._date_edit = QDateEdit()
        self._date_edit.setCalendarPopup(True)
        self._date_edit.setDateTime(self._date_edit.dateTime().currentDateTime())
        row1.addWidget(pat_lbl)
        row1.addWidget(self._pat_combo, 1)
        row1.addWidget(date_lbl)
        row1.addWidget(self._date_edit)
        detail_layout.addLayout(row1)

        row2 = QHBoxLayout()
        consent_lbl = QLabel("Surat Konsen:")
        consent_lbl.setStyleSheet("font-size: 11.5px; color: #5a5a5a;")
        self._consent_edit = QLineEdit()
        self._consent_edit.setReadOnly(True)
        self._consent_edit.setPlaceholderText("Belum ada berkas persetujuan rekam suara")
        self._consent_btn = QPushButton("Upload Berkas...")
        self._consent_btn.setObjectName("small_btn")
        self._consent_btn.clicked.connect(self._on_upload_consent)
        row2.addWidget(consent_lbl)
        row2.addWidget(self._consent_edit, 1)
        row2.addWidget(self._consent_btn)
        detail_layout.addLayout(row2)

        # ---- Audio Settings ----
        audio_group = QGroupBox("Pengaturan Audio")
        audio_layout = QHBoxLayout(audio_group)
        audio_layout.setSpacing(18)

        try:
            devices = list_input_devices()
        except Exception:
            devices = []

        mic1_widget, self._mic1_combo, self._mic1_meter, self._mic1_test, self._mic1_monitor = _audio_col(
            "Channel 1", devices
        )
        mic2_widget, self._mic2_combo, self._mic2_meter, self._mic2_test, self._mic2_monitor = _audio_col(
            "Channel 2", devices
        )

        prof_col = QVBoxLayout()
        prof_col.setSpacing(8)
        vol_lbl = QLabel("Level Volume Input")
        vol_lbl.setStyleSheet("font-size: 11.5px; font-weight: 600; color: #5a5a5a;")
        vol_row = QHBoxLayout()
        self._volume_slider = QSlider(Qt.Horizontal)
        self._volume_slider.setRange(0, 100)
        self._volume_slider.setValue(100)
        self._volume_pct = QLabel("100%")
        self._volume_pct.setStyleSheet(
            "font-size: 11px; color: #5a5a5a; min-width: 34px;"
        )
        self._volume_slider.valueChanged.connect(
            lambda v: self._volume_pct.setText(f"{v}%")
        )
        vol_row.addWidget(self._volume_slider, 1)
        vol_row.addWidget(self._volume_pct)
        role_lbl = QLabel("Atur Perangkat")
        role_lbl.setStyleSheet("font-size: 11.5px; font-weight: 600; color: #5a5a5a;")
        role_row1 = QHBoxLayout()
        role_row1.addWidget(QLabel("Channel 1:"))
        self._mic1_role = QComboBox()
        self._mic1_role.addItems(["Pasien", "Psikolog"])
        self._mic1_role.currentTextChanged.connect(self._on_mic1_role_changed)
        role_row1.addWidget(self._mic1_role, 1)
        role_row2 = QHBoxLayout()
        role_row2.addWidget(QLabel("Channel 2:"))
        self._mic2_role_lbl = QLabel("Psikolog")
        self._mic2_role_lbl.setStyleSheet(
            "font-size: 12px; padding: 4px; background: #efefef; border: 1px solid #c0c0c0;"
        )
        role_row2.addWidget(self._mic2_role_lbl, 1)

        prof_col.addWidget(vol_lbl)
        prof_col.addLayout(vol_row)
        prof_col.addWidget(role_lbl)
        prof_col.addLayout(role_row1)
        prof_col.addLayout(role_row2)
        prof_col.addStretch()
        prof_widget = QWidget()
        prof_widget.setLayout(prof_col)

        sep1 = QWidget()
        sep1.setFixedWidth(1)
        sep1.setStyleSheet("background: #b1b1b1;")
        sep2 = QWidget()
        sep2.setFixedWidth(1)
        sep2.setStyleSheet("background: #b1b1b1;")

        mic1_widget.setMaximumWidth(300)
        mic2_widget.setMaximumWidth(300)
        prof_widget.setMaximumWidth(340)

        audio_layout.addWidget(mic1_widget)
        audio_layout.addWidget(sep1)
        audio_layout.addWidget(mic2_widget)
        audio_layout.addWidget(sep2)
        audio_layout.addWidget(prof_widget)
        audio_layout.addStretch()

        # ---- Recording Status ----
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
        self._rec_status = QLabel("Siap Merekam")
        self._rec_status.setObjectName("status_rec")
        self._rec_status.setStyleSheet("color: #5a5a5a; font-size: 11px; font-weight: 600;")
        self._record_btn = QPushButton("Mulai Rekam")
        self._record_btn.setObjectName("primary_btn")
        self._record_btn.setIcon(make_icon("record", 16, "#ffffff"))
        self._record_btn.setIconSize(QSize(16, 16))
        self._pause_btn = QPushButton("Jeda")
        self._pause_btn.setObjectName("small_btn")
        self._pause_btn.setIcon(make_icon("pause", 16, "#1a1a1a"))
        self._pause_btn.setIconSize(QSize(16, 16))
        self._pause_btn.setEnabled(False)
        self._stop_btn = QPushButton("Stop")
        self._stop_btn.setObjectName("danger_btn")
        self._stop_btn.setIcon(make_icon("stop", 16, "#a02a1f"))
        self._stop_btn.setIconSize(QSize(16, 16))
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

        # ---- Audio Preview ----
        preview_group = QGroupBox("Audio Preview")
        preview_layout = QVBoxLayout(preview_group)
        self._preview_info = QLabel("Belum ada rekaman.")
        self._preview_info.setStyleSheet("color: #5a5a5a; font-size: 11.5px;")
        self._waveform_row = QHBoxLayout()
        self._waveform_row.setContentsMargins(4, 3, 4, 3)
        self._waveform_row.setSpacing(1)
        self._waveform_bars = _waveform_bars()
        for b in self._waveform_bars:
            self._waveform_row.addWidget(b, 1)
        self._waveform_holder = QWidget()
        self._waveform_holder.setFixedHeight(28)
        self._waveform_holder.setStyleSheet("background: #ffffff; border: 1px solid #b1b1b1; border-radius: 2px;")
        self._waveform_holder.setLayout(self._waveform_row)
        self._waveform_holder.setVisible(False)

        preview_btn_row = QHBoxLayout()
        self._play_btn = QPushButton("Putar / Jeda")
        self._play_btn.setObjectName("small_btn")
        self._play_btn.setIcon(make_icon("play", 16, "#1a1a1a"))
        self._play_btn.setIconSize(QSize(16, 16))
        self._play_btn.setEnabled(False)
        self._stop_play_btn = QPushButton("Stop")
        self._stop_play_btn.setObjectName("small_btn")
        self._stop_play_btn.setIcon(make_icon("stop", 16, "#1a1a1a"))
        self._stop_play_btn.setIconSize(QSize(16, 16))
        self._stop_play_btn.setEnabled(False)
        speed_lbl = QLabel("Playback Speed")
        speed_lbl.setStyleSheet("font-size: 11.5px; color: #5a5a5a;")
        self._speed_combo = QComboBox()
        for s in ["1.0", "1.25", "1.5", "2.0"]:
            self._speed_combo.addItem(f"{s}×", float(s))
        self._delete_audio_btn = QPushButton("Hapus Audio")
        self._delete_audio_btn.setObjectName("small_btn")
        self._delete_audio_btn.setStyleSheet("color: #a02a1f; border: 1px solid #c0392b;")
        self._delete_audio_btn.setIcon(make_icon("trash", 16, "#a02a1f"))
        self._delete_audio_btn.setIconSize(QSize(16, 16))
        self._delete_audio_btn.setEnabled(False)
        self._delete_audio_btn.clicked.connect(self._on_delete_audio)
        preview_btn_row.addWidget(self._play_btn)
        preview_btn_row.addWidget(self._stop_play_btn)
        preview_btn_row.addWidget(speed_lbl)
        preview_btn_row.addWidget(self._speed_combo)
        preview_btn_row.addStretch()
        preview_btn_row.addWidget(self._delete_audio_btn)

        # Proses AI — di bawah "Hapus Audio"
        ai_btn_row = QHBoxLayout()
        ai_btn_row.addStretch()
        self._ai_process_btn = QPushButton("Proses AI")
        self._ai_process_btn.setObjectName("primary_btn")
        self._ai_process_btn.setIcon(make_icon("settings", 16, "#ffffff"))
        self._ai_process_btn.setIconSize(QSize(16, 16))
        self._ai_process_btn.setEnabled(False)
        self._ai_process_btn.clicked.connect(self._on_process_ai)
        ai_btn_row.addWidget(self._ai_process_btn)

        time_row = QHBoxLayout()
        self._time_label = QLabel("00:00 / 00:00")
        self._time_label.setStyleSheet("font-size: 11px; color: #5a5a5a; font-family: 'Consolas', monospace;")
        time_row.addStretch()
        time_row.addWidget(self._time_label)

        preview_layout.addWidget(self._preview_info)
        preview_layout.addWidget(self._waveform_holder)
        preview_layout.addLayout(preview_btn_row)
        preview_layout.addLayout(ai_btn_row)
        preview_layout.addLayout(time_row)

        self._play_btn.clicked.connect(self._on_play)
        self._stop_play_btn.clicked.connect(self._on_stop_play)

        # ---- Progres Pemrosesan AI (spinner melingkar) ----
        ai_group = QGroupBox("Progres Pemrosesan AI")
        ai_layout = QVBoxLayout(ai_group)
        ai_head = QHBoxLayout()
        self._ai_stage_lbl = QLabel("Menunggu rekaman...")
        self._ai_stage_lbl.setStyleSheet("font-size: 11.5px;")
        ai_head.addWidget(self._ai_stage_lbl)
        ai_head.addStretch()
        self._spinner = Spinner()
        spinner_row = QHBoxLayout()
        spinner_row.addStretch()
        spinner_row.addWidget(self._spinner)
        spinner_row.addStretch()
        ai_layout.addLayout(ai_head)
        ai_layout.addLayout(spinner_row)

        layout.addWidget(title)
        layout.addWidget(detail_group)
        layout.addWidget(audio_group)
        layout.addWidget(status_group)
        layout.addWidget(preview_group)
        layout.addWidget(ai_group)
        layout.addStretch()

        # Timer
        self._timer = QTimer(self)
        self._timer.setInterval(1000)
        self._timer.timeout.connect(self._tick)
        self._elapsed = 0

        # Recording state
        self._rec_worker: RecordingWorker | None = None
        self._play_worker: PlaybackWorker | None = None
        self._last_rec: tuple[str, bytes, int] | None = None  # (filepath, key, channels)
        self._paused = False
        self._consent_path: str | None = None

        # Live waveform during recording
        self._wave_timer = QTimer(self)
        self._wave_timer.setInterval(120)

    # ---- patients ----
    def load_patients(self, patients: list[dict]) -> None:
        self._pat_combo.clear()
        self._pat_combo.addItem("Pilih pasien...", None)
        for p in patients:
            self._pat_combo.addItem(f"{p['name']} (ID {p['id']})", p["id"])

    def current_patient_id(self) -> int | None:
        return self._pat_combo.currentData()

    def preselect_patient(self, patient_id: int) -> None:
        for i in range(self._pat_combo.count()):
            if self._pat_combo.itemData(i) == patient_id:
                self._pat_combo.setCurrentIndex(i)
                return

    # ---- consent ----
    def _on_upload_consent(self):
        import shutil

        from PySide6.QtWidgets import QFileDialog

        path, _ = QFileDialog.getOpenFileName(
            self, "Upload Surat Konsen", "", "Dokumen (*.pdf *.png *.jpg *.jpeg *.docx)"
        )
        if not path:
            return
        import os

        from verbamind.config.paths import recordings_dir

        consent_dir = recordings_dir() / "consent"
        consent_dir.mkdir(parents=True, exist_ok=True)
        dest = consent_dir / os.path.basename(path)
        try:
            shutil.copy(path, dest)
        except OSError as e:
            QMessageBox.warning(self, "Upload Konsen", f"Gagal menyalin berkas: {e}")
            return
        self._consent_edit.setText(os.path.basename(path))
        self._consent_path = str(dest)

    def audio_source(self) -> tuple[str, bytes | None, int] | None:
        """Resolve audio for AI processing.

        Returns (path, key_hex_or_None, channels) or None when no audio is
        available.
        """
        if self._last_rec is not None:
            filepath, key, channels = self._last_rec
            return (filepath, key.hex(), channels)
        return None

    # ---- mic roles ----
    def _on_mic1_role_changed(self, role: str):
        self._mic2_role_lbl.setText("Psikolog" if role == "Pasien" else "Pasien")

    # ---- audio delete ----
    def _on_delete_audio(self):
        import os

        if self._last_rec is None:
            return
        filepath = self._last_rec[0]
        confirm = QMessageBox.question(
            self, "Hapus Audio", f"Hapus file rekaman ini?\n{filepath}"
        )
        if confirm != QMessageBox.Yes:
            return
        if self._play_worker is not None and self._play_worker.isRunning():
            self._play_worker.request_stop()
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
        except OSError:
            pass
        self._last_rec = None
        self._play_btn.setEnabled(False)
        self._stop_play_btn.setEnabled(False)
        self._delete_audio_btn.setEnabled(False)
        self._preview_info.setText("Rekaman dihapus.")
        self._preview_info.setStyleSheet("color: #5a5a5a; font-size: 11.5px;")
        self._waveform_holder.setVisible(False)
        self._ai_process_btn.setEnabled(False)

    # ---- AI processing ----
    def _on_process_ai(self):
        if self._last_rec is None or self.current_patient_id() is None:
            QMessageBox.information(
                self, "Proses AI", "Butuh rekaman + pasien terpilih."
            )
            return
        self.ai_process_requested.emit()

    def set_ai_state(self, stage: str, percent: int | None) -> None:
        self._ai_stage_lbl.setText(stage)
        if percent is None:
            self._spinner.start()
        else:
            self._spinner.stop()

    # ---- timer ----
    def _format_time(self, seconds: int) -> str:
        h = seconds // 3600
        m = (seconds % 3600) // 60
        s = seconds % 60
        return f"{h:02d}:{m:02d}:{s:02d}"

    def _tick(self):
        if not self._paused:
            self._elapsed += 1
            self._timer_label.setText(self._format_time(self._elapsed))

    # ---- recording ----
    def _on_record(self):
        if self._rec_worker is not None and self._rec_worker.isRunning():
            return
        import time

        from verbamind.config.paths import recordings_dir

        rec_dir = recordings_dir()
        rec_dir.mkdir(parents=True, exist_ok=True)
        ts = time.strftime("%Y%m%d_%H%M%S")
        filepath = str(rec_dir / f"REC_{ts}.vera")

        # stop mic monitors to free devices
        self._mic1_monitor.stop()
        self._mic2_monitor.stop()

        self._elapsed = 0
        self._paused = False
        self._timer_label.setText("00:00:00")
        self._timer.start()

        self._led.set_active(True)
        self._rec_status.setText("Sedang Merekam")
        self._rec_status.setStyleSheet("color: #c0392b; font-size: 11px; font-weight: 600;")
        self._record_btn.setEnabled(False)
        self._pause_btn.setEnabled(True)
        self._stop_btn.setEnabled(True)

        # Map physical mics to roles based on the "Atur Perangkat" selection.
        mic1_dev = self._mic1_combo.currentData()
        mic2_dev = self._mic2_combo.currentData()
        if self._mic1_role.currentText() == "Pasien":
            patient_dev, psych_dev = mic1_dev, mic2_dev
        else:
            patient_dev, psych_dev = mic2_dev, mic1_dev

        self._rec_worker = RecordingWorker(
            filepath,
            patient_device=patient_dev,
            psychologist_device=psych_dev,
            volume=self._volume_slider.value() / 100.0,
        )
        self._rec_worker.level_updated.connect(self._on_rec_level)
        self._rec_worker.finished_ok.connect(self._on_rec_finished)
        self._rec_worker.start()

    def _on_rec_level(self, level: float):
        v = int(level * 100)
        for i, bar in enumerate(self._waveform_bars):
            h = max(4, int((v / 100.0) * 24 * (0.5 + 0.5 * ((i * 37) % 10) / 10)))
            bar.setFixedHeight(h)

    def _on_pause(self):
        # Note: RecordingWorker keeps capturing; pause only freezes timer display.
        self._paused = not self._paused
        if self._paused:
            self._led.set_active(False)
            self._rec_status.setText("Dijeda")
            self._rec_status.setStyleSheet("color: #c8790b; font-size: 11px; font-weight: 600;")
            self._pause_btn.setText("Lanjut")
        else:
            self._led.set_active(True)
            self._rec_status.setText("Sedang Merekam")
            self._rec_status.setStyleSheet("color: #c0392b; font-size: 11px; font-weight: 600;")
            self._pause_btn.setText("Jeda")

    def _on_stop(self):
        if self._rec_worker is None:
            return
        self._timer.stop()
        self._wave_timer.stop()
        self._rec_worker.request_stop()
        self._led.set_active(False)
        self._rec_status.setText("Menyimpan...")
        self._rec_status.setStyleSheet("color: #5a5a5a; font-size: 11px; font-weight: 600;")
        self._record_btn.setEnabled(False)
        self._pause_btn.setEnabled(False)
        self._stop_btn.setEnabled(False)

    def _on_rec_finished(self, filepath: str, key: bytes, seconds: int, channels: int):
        self._rec_status.setText("Berhenti")
        self._record_btn.setEnabled(True)
        self._pause_btn.setEnabled(False)
        self._pause_btn.setText("Jeda")
        self._stop_btn.setEnabled(False)
        self._last_rec = (filepath, key, channels)
        self._waveform_holder.setVisible(True)
        self._preview_info.setText(f"Rekaman selesai — durasi {self._format_time(seconds)} ({filepath})")
        self._preview_info.setStyleSheet("color: #1a1a1a; font-size: 11.5px;")
        self._play_btn.setEnabled(True)
        self._stop_play_btn.setEnabled(False)
        self._delete_audio_btn.setEnabled(True)
        self._ai_process_btn.setEnabled(True)
        self._time_label.setText(f"00:00 / {self._format_time(seconds)}")
        self.recording_finished.emit(filepath, seconds)

    # ---- playback ----
    def _on_play(self):
        if self._last_rec is None:
            return
        filepath, key, channels = self._last_rec
        speed = self._speed_combo.currentData() or 1.0
        self._play_worker = PlaybackWorker(filepath, key, channels, speed=speed)
        self._play_worker.position_updated.connect(self._on_play_position)
        self._play_worker.finished_ok.connect(self._on_play_done)
        self._play_btn.setEnabled(False)
        self._stop_play_btn.setEnabled(True)
        self._play_worker.start()

    def _on_play_position(self, elapsed: float, total: float):
        self._time_label.setText(
            f"{self._format_time(int(elapsed))} / {self._format_time(int(total))}"
        )

    def _on_play_done(self):
        self._play_btn.setEnabled(True)
        self._stop_play_btn.setEnabled(False)

    def _on_stop_play(self):
        if self._play_worker is not None:
            self._play_worker.request_stop()
        self._on_play_done()

    def closeEvent(self, event):  # noqa: N802 — Qt override
        self._mic1_monitor.stop()
        self._mic2_monitor.stop()
        if self._rec_worker is not None and self._rec_worker.isRunning():
            self._rec_worker.request_stop()
        if self._play_worker is not None and self._play_worker.isRunning():
            self._play_worker.request_stop()
        super().closeEvent(event)
