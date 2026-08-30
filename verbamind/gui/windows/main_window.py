"""VerbaMind main window — sidebar, statusbar, page content."""

import os

from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QScrollArea,
    QStackedWidget,
    QStatusBar,
    QWidget,
)

from verbamind.backend.audio.session_manager import SessionManager
from verbamind.gui.api_client import VerbaMindClient
from verbamind.gui.dialogs.verbatim_birp_dialog import VerbatimBIRPDialog
from verbamind.gui.pages.activation_page import ActivationPage
from verbamind.gui.pages.audit_log_page import AuditLogPage
from verbamind.gui.pages.dashboard_page import DashboardPage
from verbamind.gui.pages.patient_room_page import PatientRoomPage
from verbamind.gui.pages.patients_page import PatientsPage
from verbamind.gui.pages.recording_page import RecordingPage
from verbamind.gui.pages.settings_page import SettingsPage
from verbamind.gui.styles.theme import MAIN_STYLESHEET
from verbamind.gui.widgets.sidebar import Sidebar

# Stack page indexes
IDX_DASHBOARD, IDX_PATIENTS, IDX_RECORDING, IDX_AUDIT, IDX_SETTINGS = 0, 1, 2, 3, 4
IDX_ACTIVATION, IDX_ROOM = 5, 6


class ProcessWorker(QThread):
    """Background worker — full AI pipeline (Whisper + nonverbal + BIRP)."""

    finished_ok = Signal(dict)
    failed = Signal(str)

    def __init__(
        self,
        client: VerbaMindClient,
        session_db_id: int,
        audio_path: str,
        key_hex: str | None,
        channels: int,
        parent=None,
    ):
        super().__init__(parent)
        self._client = client
        self._session_db_id = session_db_id
        self._audio_path = audio_path
        self._key_hex = key_hex
        self._channels = channels

    def run(self):
        try:
            result = self._client.process_session(
                self._session_db_id,
                self._audio_path,
                key_hex=self._key_hex,
                channels=self._channels,
            )
            if result.get("status") in ("ok", "partial"):
                self.finished_ok.emit(result)
            else:
                self.failed.emit(
                    "; ".join(result.get("errors", []))
                    or result.get("message", "unknown error")
                )
        except Exception as e:
            self.failed.emit(str(e))


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("VerbaMind")
        self.resize(1280, 800)
        self.setMinimumSize(1024, 680)
        self.setStyleSheet(MAIN_STYLESHEET)

        self._session_manager = SessionManager(
            recordings_dir=os.path.join(os.getcwd(), "recordings")
        )
        self._api_client = VerbaMindClient()
        self._process_worker: ProcessWorker | None = None

        self._setup_body()
        self._setup_statusbar()

    def _setup_body(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._sidebar = Sidebar()
        self._stack = QStackedWidget()
        self._stack.setObjectName("content_stack")

        # 5 pages matching sidebar items
        self._dashboard = DashboardPage()
        self._patients = PatientsPage()
        self._recording = RecordingPage()
        self._audit_log = AuditLogPage()
        self._settings = SettingsPage()

        # Additional pages (activation) not in sidebar
        self._activation = ActivationPage()
        self._room = PatientRoomPage()

        for page in [
            self._dashboard,
            self._patients,
            self._recording,
            self._audit_log,
            self._settings,
            self._activation,
            self._room,
        ]:
            container = QWidget()
            container.setObjectName("content_area")
            container_layout = QHBoxLayout(container)
            container_layout.setContentsMargins(0, 0, 0, 0)

            scroll = QScrollArea()
            scroll.setObjectName("content_scroll")
            scroll.setWidgetResizable(True)
            scroll.setFrameShape(QScrollArea.Shape.NoFrame)
            scroll.setWidget(page)

            container_layout.addWidget(scroll)
            self._stack.addWidget(container)

        layout.addWidget(self._sidebar)
        layout.addWidget(self._stack, 1)

        # Load real data
        self._refresh_all()

        # Wiring
        self._recording.recording_finished.connect(self._on_recording_finished)
        self._recording.ai_process_requested.connect(self._on_process_ai)
        self._dashboard.new_session_requested.connect(
            lambda: self._on_navigate(IDX_RECORDING)
        )
        self._dashboard.view_session_requested.connect(self._on_view_session)
        self._patients.add_patient_requested.connect(self._on_add_patient)
        self._patients.open_patient_requested.connect(self._on_open_patient)
        self._patients.delete_patient_requested.connect(self._on_delete_patient)
        self._room.back_requested.connect(lambda: self._on_navigate(IDX_PATIENTS))
        self._room.new_session_for_patient.connect(self._on_new_session_for_patient)
        self._room.view_session_requested.connect(self._on_view_session)
        self._audit_log.filter_requested.connect(self._on_audit_filter)
        self._sidebar.navigation_changed.connect(self._on_navigate)

    def _refresh_patients(self):
        try:
            result = self._api_client.list_patients()
            patients = result.get("patients", [])
        except Exception:
            patients = []
        self._patients.load_patients(patients)
        self._recording.load_patients(patients)

    def _refresh_all(self):
        self._refresh_patients()
        try:
            result = self._api_client.dashboard_stats()
            self._dashboard.load_dashboard(
                result.get("stats", {}), result.get("recent_sessions", [])
            )
        except Exception:
            self._dashboard.load_sessions([])
        self._refresh_audit()

    def _refresh_audit(self):
        try:
            self._audit_log.load_entries(
                self._api_client.list_audit().get("entries", [])
            )
        except Exception:
            self._audit_log.load_entries([])

    def _on_audit_filter(self, action: str, date_from: str, date_to: str):
        try:
            self._audit_log.load_entries(
                self._api_client.list_audit(action, date_from, date_to).get("entries", [])
            )
        except Exception as e:
            QMessageBox.critical(self, "Gagal", f"Filter audit gagal: {e}")

    # ---- patient room ----
    def _on_open_patient(self, patient_id: int):
        try:
            detail = self._api_client.get_patient(patient_id)
            sessions = self._api_client.list_sessions(patient_id)
        except Exception as e:
            QMessageBox.critical(self, "Gagal", f"Memuat pasien gagal: {e}")
            return
        if detail.get("status") != "ok":
            return
        self._room.load_patient(
            detail["patient"], sessions.get("sessions", [])
        )
        self._on_navigate(IDX_ROOM)

    def _on_delete_patient(self, patient_id: int):
        confirm = QMessageBox.question(
            self, "Hapus Pasien", "Hapus pasien ini beserta seluruh sesinya?"
        )
        if confirm != QMessageBox.Yes:
            return
        try:
            self._api_client.delete_patient(patient_id)
            self._refresh_all()
            self.statusBar().showMessage("Pasien dihapus", 5000)
        except Exception as e:
            QMessageBox.critical(self, "Gagal", f"Hapus pasien gagal: {e}")

    def _on_new_session_for_patient(self, patient_id: int):
        self._refresh_patients()
        self._recording.preselect_patient(patient_id)
        self._on_navigate(IDX_RECORDING)

    # ---- verbatim modal ----
    def _on_view_session(self, session_id: int):
        try:
            detail = self._api_client.get_session_detail(session_id)
        except Exception as e:
            QMessageBox.critical(self, "Gagal", f"Memuat sesi gagal: {e}")
            return
        if detail.get("status") != "ok":
            return
        segments = detail.get("segments") or []
        dlg = VerbatimBIRPDialog(detail["session"], detail.get("birp"), segments, self)
        dlg.birp_saved.connect(self._on_modal_birp_saved)
        dlg.audio_deleted.connect(self._on_modal_audio_deleted)
        dlg.audio_kept.connect(self._on_modal_audio_kept)
        dlg.exec()
        self._refresh_all()

    def _on_modal_birp_saved(self, session_id: int, birp: dict):
        try:
            self._api_client.update_birp(session_id, birp)
        except Exception as e:
            QMessageBox.critical(self, "Gagal", f"Simpan BIRP gagal: {e}")

    def _on_modal_audio_deleted(self, session_id: int):
        try:
            self._api_client.delete_audio(session_id)
        except Exception as e:
            QMessageBox.critical(self, "Gagal", f"Hapus audio gagal: {e}")

    def _on_modal_audio_kept(self, session_id: int):
        try:
            self._api_client.keep_audio(session_id)
        except Exception as e:
            QMessageBox.critical(self, "Gagal", f"Simpan status audio gagal: {e}")

    # ---- AI processing from recording page ----
    def _on_process_ai(self):
        patient_id = self._recording.current_patient_id()
        source = self._recording.audio_source()
        if patient_id is None:
            QMessageBox.warning(self, "Proses AI", "Pilih pasien dulu.")
            return
        if source is None:
            QMessageBox.warning(
                self, "Proses AI", "Tidak ada audio — rekam dulu atau impor file audio."
            )
            return
        audio_path, key_hex, channels = source
        seconds = self._recording._elapsed
        consent = getattr(self._recording, "_consent_path", None)
        try:
            created = self._api_client.create_session(
                patient_id,
                duration_seconds=seconds,
                audio_file_path=audio_path,
                consent_file=consent,
            )
            session_db_id = created.get("id")
        except Exception as e:
            QMessageBox.critical(self, "Gagal", f"Buat sesi gagal: {e}")
            return

        if self._process_worker is not None and self._process_worker.isRunning():
            return
        self._recording.set_ai_state(
            "Transkripsi Whisper & analisis nonverbal + BIRP...",
            None,
        )
        self._process_worker = ProcessWorker(
            self._api_client, session_db_id, audio_path, key_hex, channels, parent=self
        )
        self._process_worker.setProperty("session_db_id", session_db_id)
        self._process_worker.finished_ok.connect(self._on_ai_ready)
        self._process_worker.failed.connect(self._on_ai_failed)
        self._process_worker.start()

    def _on_ai_ready(self, data: dict):
        self._recording.set_ai_state(
            "Selesai — BIRP siap direview", 100
        )
        self._refresh_all()
        session_db_id = self._process_worker.property("session_db_id") if self._process_worker else None
        self.statusBar().showMessage(
            f"Proses AI selesai ({data.get('transcript_count', 0)} segmen) — buka Riwayat Sesi pasien untuk review",
            8000,
        )
        if session_db_id:
            self._on_view_session(int(session_db_id))

    def _on_ai_failed(self, message: str):
        self._recording.set_ai_state(f"Gagal: {message}", 0)

    def _on_add_patient(self):
        from PySide6.QtWidgets import (
            QDialog,
            QDialogButtonBox,
            QFormLayout,
            QLineEdit,
            QMessageBox,
        )

        dlg = QDialog(self)
        dlg.setWindowTitle("Tambah Pasien")
        form = QFormLayout(dlg)
        name_edit = QLineEdit()
        age_edit = QLineEdit()
        age_edit.setPlaceholderText("opsional")
        gender_edit = QLineEdit()
        gender_edit.setPlaceholderText("P / L")
        birth_edit = QLineEdit()
        birth_edit.setPlaceholderText("YYYY-MM-DD (opsional)")
        record_edit = QLineEdit()
        record_edit.setPlaceholderText("No. Rekam Medis (opsional)")
        notes_edit = QLineEdit()
        notes_edit.setPlaceholderText("opsional")
        form.addRow("Nama*", name_edit)
        form.addRow("Usia", age_edit)
        form.addRow("Gender", gender_edit)
        form.addRow("Tanggal Lahir", birth_edit)
        form.addRow("No. Rekam Medis", record_edit)
        form.addRow("Catatan", notes_edit)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dlg.accept)
        buttons.rejected.connect(dlg.reject)
        form.addRow(buttons)
        if dlg.exec() != QDialog.Accepted or not name_edit.text().strip():
            return
        try:
            age = int(age_edit.text()) if age_edit.text().strip().isdigit() else None
            self._api_client.create_patient(
                name_edit.text().strip(), age, gender_edit.text().strip() or None,
                birth_edit.text().strip() or None, record_edit.text().strip() or None,
                notes_edit.text().strip() or None,
            )
            self._refresh_patients()
            self.statusBar().showMessage("Pasien tersimpan ke database", 5000)
        except Exception as e:
            QMessageBox.critical(self, "Gagal", f"Tambah pasien gagal: {e}\nPastikan backend berjalan.")

    def _on_recording_finished(self, filepath: str, seconds: int):
        self.statusBar().showMessage(
            f"Rekaman tersimpan (terenkripsi): {filepath} — {seconds}s", 8000
        )

    def _setup_statusbar(self):
        sb = QStatusBar()
        lock_label = QLabel("🔒 Data tersimpan")
        lock_label.setStyleSheet("color: #2e7d32; font-weight: 600; font-size: 11px;")
        user_label = QLabel("Pengguna: Psikolog")
        user_label.setStyleSheet("color: #5a5a5a; font-size: 11px;")
        model_label = QLabel("Model aktif: Qwen2.5 7B")
        model_label.setStyleSheet("color: #5a5a5a; font-size: 11px;")
        version_label = QLabel("v0.1.0")
        version_label.setStyleSheet("color: #5a5a5a; font-size: 11px;")

        sb.addWidget(lock_label)
        sb.addWidget(user_label)
        sb.addWidget(model_label)
        sb.addPermanentWidget(version_label)
        self.setStatusBar(sb)

    def _on_navigate(self, index: int):
        if 0 <= index < self._stack.count():
            self._stack.setCurrentIndex(index)
            if index == IDX_DASHBOARD:
                self._refresh_all()
