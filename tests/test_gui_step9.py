"""TDD tests for Step 9 GUI — main window, sidebar, dashboard, recording page.

RED phase: all imports will fail since modules don't exist yet.
"""

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance() or QApplication([])
    yield app


class TestTheme:
    def test_theme_colors_dict(self):
        from verbamind.gui.styles.theme import COLORS

        assert COLORS["win_bg"] == "#f0f0f0"
        assert COLORS["accent"] == "#0a5fc4"
        assert COLORS["led_on"] == "#2ecc57"

    def test_main_stylesheet_is_string(self):
        from verbamind.gui.styles.theme import MAIN_STYLESHEET

        assert isinstance(MAIN_STYLESHEET, str)
        assert "QMainWindow" in MAIN_STYLESHEET


class TestSidebar:
    def test_sidebar_items(self, qapp):
        from verbamind.gui.widgets.sidebar import Sidebar

        sidebar = Sidebar()
        items = [sidebar.item(i).text() for i in range(sidebar.count())]
        assert any("Dashboard" in t for t in items)
        assert any("Recording" in t for t in items)

    def test_sidebar_emits_signal(self, qapp):
        from verbamind.gui.widgets.sidebar import Sidebar

        sidebar = Sidebar()
        signals_received = []

        def on_navigate(index):
            signals_received.append(index)

        sidebar.navigation_changed.connect(on_navigate)
        sidebar.setCurrentRow(2)
        assert len(signals_received) == 1


class TestStatusLED:
    def test_led_default_off(self, qapp):
        from verbamind.gui.widgets.status_led import StatusLED

        led = StatusLED()
        assert led.state == "idle"

    def test_led_set_active(self, qapp):
        from verbamind.gui.widgets.status_led import StatusLED

        led = StatusLED()
        led.set_active(True)
        assert led.state == "recording"


class TestMainWindow:
    def test_window_title(self, qapp):
        from verbamind.gui.windows.main_window import MainWindow

        window = MainWindow()
        assert "VerbaMind" in window.windowTitle()

    def test_window_has_menubar(self, qapp):
        from verbamind.gui.windows.main_window import MainWindow

        window = MainWindow()
        assert window.menuBar() is not None

    def test_window_has_statusbar(self, qapp):
        from verbamind.gui.windows.main_window import MainWindow

        window = MainWindow()
        assert window.statusBar() is not None

    def test_window_has_sidebar(self, qapp):
        from verbamind.gui.windows.main_window import MainWindow
        from PySide6.QtWidgets import QListWidget

        window = MainWindow()
        sidebar = window.findChild(QListWidget, "sidebar")
        assert sidebar is not None
        assert sidebar.count() == 4


class TestDashboardPage:
    def test_dashboard_created(self, qapp):
        from verbamind.gui.pages.dashboard_page import DashboardPage

        page = DashboardPage()
        assert page is not None

    def test_dashboard_has_table(self, qapp):
        from verbamind.gui.pages.dashboard_page import DashboardPage
        from PySide6.QtWidgets import QTableWidget

        page = DashboardPage()
        tables = page.findChildren(QTableWidget)
        assert len(tables) >= 1


class TestRecordingPage:
    def test_recording_page_created(self, qapp):
        from verbamind.gui.pages.recording_page import RecordingPage

        page = RecordingPage()
        assert page is not None

    def test_recording_has_record_button(self, qapp):
        from verbamind.gui.pages.recording_page import RecordingPage
        from PySide6.QtWidgets import QPushButton

        page = RecordingPage()
        buttons = page.findChildren(QPushButton)
        texts = [b.text() for b in buttons]
        assert any("Record" in t for t in texts)
