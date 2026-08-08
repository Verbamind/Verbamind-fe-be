"""VerbaMind main window — sidebar navigation + stacked content pages."""

from PySide6.QtWidgets import (
    QHBoxLayout,
    QMainWindow,
    QStackedWidget,
    QWidget,
)

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
        self.setWindowTitle("VerbaMind")
        self.setMinimumSize(1024, 680)
        self.setStyleSheet(MAIN_STYLESHEET)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._sidebar = Sidebar()
        self._stack = QStackedWidget()
        self._stack.setObjectName("content_stack")

        self._dashboard = DashboardPage()
        self._recording = RecordingPage()
        self._transcript = TranscriptPage()
        self._birp = BIRPPage()
        self._settings = SettingsPage()
        self._activation = ActivationPage()

        self._stack.addWidget(self._dashboard)
        self._stack.addWidget(self._recording)
        self._stack.addWidget(self._transcript)
        self._stack.addWidget(self._birp)
        self._stack.addWidget(self._settings)
        self._stack.addWidget(self._activation)

        self._sidebar.navigation_changed.connect(self._stack.setCurrentIndex)

        layout.addWidget(self._sidebar)
        layout.addWidget(self._stack, 1)
