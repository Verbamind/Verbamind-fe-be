"""VerbaMind main window — menubar, toolbar, sidebar, statusbar, 6-page stacked content."""

import os

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMenuBar,
    QStackedWidget,
    QStatusBar,
    QToolBar,
    QWidget,
)

from verbamind.backend.audio.session_manager import SessionManager
from verbamind.gui.pages.activation_page import ActivationPage
from verbamind.gui.pages.birp_page import BIRPPage
from verbamind.gui.pages.dashboard_page import DashboardPage
from verbamind.gui.pages.recording_page import RecordingPage
from verbamind.gui.pages.settings_page import SettingsPage
from verbamind.gui.pages.transcript_page import TranscriptPage
from verbamind.gui.styles.theme import MAIN_STYLESHEET
from verbamind.gui.widgets.sidebar import Sidebar


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("VerbaMind AI")
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
        file_menu.addAction(QAction("New Session", self))
        file_menu.addAction(QAction("Open Recording...", self))
        file_menu.addSeparator()
        file_menu.addAction(QAction("Exit", self, triggered=self.close))

        edit_menu = menubar.addMenu("Edit")
        edit_menu.addAction(QAction("Settings", self))

        view_menu = menubar.addMenu("View")
        view_menu.addAction(QAction("Dashboard", self))
        view_menu.addAction(QAction("Recording", self))

        help_menu = menubar.addMenu("Help")
        help_menu.addAction(QAction("About VerbaMind", self))

    def _setup_toolbar(self):
        toolbar = QToolBar()
        toolbar.addAction(QAction("New Session", self))
        toolbar.addAction(QAction("New Patient", self))
        toolbar.addSeparator()
        toolbar.addAction(QAction("Refresh", self))
        toolbar.addAction(QAction("Export PDF", self))
        toolbar.addSeparator()
        toolbar.addAction(QAction("Settings", self))
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

        self._pages = [
            DashboardPage(),
            RecordingPage(),
            TranscriptPage(),
            BIRPPage(),
            SettingsPage(),
            ActivationPage(),
        ]
        for page in self._pages:
            container = QWidget()
            container.setObjectName("content_area")
            container_layout = QHBoxLayout(container)
            container_layout.setContentsMargins(0, 0, 0, 0)
            container_layout.addWidget(page)
            self._stack.addWidget(container)

        self._sidebar.navigation_changed.connect(self._on_navigate)

        layout.addWidget(self._sidebar)
        layout.addWidget(self._stack, 1)

        self._load_dashboard()

    def _setup_statusbar(self):
        sb = QStatusBar()
        self._status_label = QLabel("VerbaMind v0.1.0 — Ready")
        self._status_label.setStyleSheet("font-size: 11px; color: #5a5a5a;")
        lock_label = QLabel("AES-256")
        lock_label.setStyleSheet("font-size: 11px; color: #2e7d32; font-weight: 600;")
        sb.addWidget(self._status_label)
        sb.addPermanentWidget(lock_label)
        self.setStatusBar(sb)

    def _on_navigate(self, index: int):
        if 0 <= index < self._stack.count():
            self._stack.setCurrentIndex(index)

    def _load_dashboard(self):
        pass
