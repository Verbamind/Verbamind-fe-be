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
        assert "Dashboard" in items
        assert "Recording" in items

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
        assert window.windowTitle() == "VerbaMind"

    def test_window_has_sidebar(self, qapp):
        from verbamind.gui.windows.main_window import MainWindow
        from PySide6.QtWidgets import QListWidget

        window = MainWindow()
        sidebar = window.findChild(QListWidget, "sidebar")
        assert sidebar is not None

    def test_window_has_stacked_widget(self, qapp):
        from verbamind.gui.windows.main_window import MainWindow

        window = MainWindow()
        from PySide6.QtWidgets import QStackedWidget

        stacked = window.findChild(QStackedWidget, "content_stack")
        assert stacked is not None

    def test_navigation_switches_page(self, qapp):
        from verbamind.gui.windows.main_window import MainWindow
        from PySide6.QtWidgets import QListWidget, QStackedWidget

        window = MainWindow()
        stacked = window.findChild(QStackedWidget, "content_stack")
        initial = stacked.currentIndex()
        sidebar = window.findChild(QListWidget, "sidebar")
        sidebar.setCurrentRow(1)
        assert stacked.currentIndex() != initial


class TestDashboardPage:
    def test_dashboard_created(self, qapp):
        from verbamind.gui.pages.dashboard_page import DashboardPage

        page = DashboardPage()
        assert page is not None

    def test_dashboard_has_welcome_label(self, qapp):
        from verbamind.gui.pages.dashboard_page import DashboardPage
        from PySide6.QtWidgets import QLabel

        page = DashboardPage()
        labels = page.findChildren(QLabel, "welcome_label")
        assert len(labels) >= 1


class TestRecordingPage:
    def test_recording_page_created(self, qapp):
        from verbamind.gui.pages.recording_page import RecordingPage

        page = RecordingPage()
        assert page is not None

    def test_recording_has_record_button(self, qapp):
        from verbamind.gui.pages.recording_page import RecordingPage
        from PySide6.QtWidgets import QPushButton

        page = RecordingPage()
        btn = page.findChild(QPushButton, "record_btn")
        assert btn is not None

    def test_device_config_combos(self, qapp):
        from verbamind.gui.widgets.device_config import DeviceConfig
        from PySide6.QtWidgets import QComboBox

        config = DeviceConfig()
        combos = config.findChildren(QComboBox, "patient_combo")
        assert len(combos) >= 1
