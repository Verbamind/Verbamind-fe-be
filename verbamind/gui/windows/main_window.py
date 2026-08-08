"""VerbaMind main window — menubar, toolbar, sidebar, statusbar, 5-page content.

Status bar matches ui-verbamind-a.html:
  🔒 Data tersimpan | Pengguna: dr. Psikolog | Model aktif: Qwen2.5 | v0.1.0
"""

import os

from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QStackedWidget,
    QStatusBar,
    QToolBar,
    QWidget,
)

from verbamind.backend.audio.session_manager import SessionManager
from verbamind.gui.pages.activation_page import ActivationPage
from verbamind.gui.pages.audit_log_page import AuditLogPage
from verbamind.gui.pages.birp_page import BIRPPage
from verbamind.gui.pages.dashboard_page import DashboardPage
from verbamind.gui.pages.patients_page import PatientsPage
from verbamind.gui.pages.recording_page import RecordingPage
from verbamind.gui.pages.settings_page import SettingsPage
from verbamind.gui.pages.transcript_page import TranscriptPage
from verbamind.gui.styles.theme import MAIN_STYLESHEET
from verbamind.gui.widgets.sidebar import Sidebar


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Verbamind AI")
        self.setMinimumSize(1180, 760)
        self.setStyleSheet(MAIN_STYLESHEET)

        self._session_manager = SessionManager(
            recordings_dir=os.path.join(os.getcwd(), "recordings")
        )

        self._setup_menubar()
        self._setup_toolbar()
        self._setup_body()
        self._setup_statusbar()

    def _setup_menubar(self):
        menubar = self.menuBar()
        file_menu = menubar.addMenu("File")
        file_menu.addAction(QAction("Sesi Baru", self))
        file_menu.addAction(QAction("Buka Rekaman...", self))
        file_menu.addSeparator()
        file_menu.addAction(QAction("Keluar", self, triggered=self.close))

        edit_menu = menubar.addMenu("Edit")
        edit_menu.addAction(QAction("Preferensi", self))

        view_menu = menubar.addMenu("Tampilan")
        view_menu.addAction(QAction("Dashboard", self))
        view_menu.addAction(QAction("Data Pasien", self))

        session_menu = menubar.addMenu("Sesi")
        session_menu.addAction(QAction("Mulai Rekam", self))

        help_menu = menubar.addMenu("Bantuan")
        help_menu.addAction(QAction("Tentang Verbamind", self))

    def _setup_toolbar(self):
        toolbar = QToolBar()
        toolbar.addAction(QAction("🔄 Segarkan", self))
        toolbar.addAction(QAction("📄 Ekspor PDF", self))
        toolbar.addSeparator()
        toolbar.addAction(QAction("⚙ Pengaturan", self))
        self.addToolBar(toolbar)

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

        # Additional pages (transcript, BIRP, activation) not in sidebar
        self._transcript = TranscriptPage()
        self._birp = BIRPPage()
        self._activation = ActivationPage()

        for page in [
            self._dashboard,
            self._patients,
            self._recording,
            self._audit_log,
            self._settings,
            self._transcript,
            self._birp,
            self._activation,
        ]:
            container = QWidget()
            container.setObjectName("content_area")
            container_layout = QHBoxLayout(container)
            container_layout.setContentsMargins(0, 0, 0, 0)
            container_layout.addWidget(page)
            self._stack.addWidget(container)

        self._sidebar.navigation_changed.connect(self._on_navigate)

        layout.addWidget(self._sidebar)
        layout.addWidget(self._stack, 1)

        # Load real data
        sessions = self._session_manager.list_sessions()
        self._dashboard.load_sessions(sessions)

    def _setup_statusbar(self):
        sb = QStatusBar()
        lock_label = QLabel("🔒 Data tersimpan")
        lock_label.setStyleSheet("color: #2e7d32; font-weight: 600; font-size: 11px;")
        user_label = QLabel("Pengguna: dr. Psikolog")
        user_label.setStyleSheet("color: #5a5a5a; font-size: 11px;")
        model_label = QLabel("Model aktif: Qwen2.5")
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
