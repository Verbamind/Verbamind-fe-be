"""TDD tests for GUI — settings and activation pages."""

import pytest
from PySide6.QtWidgets import QApplication


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance() or QApplication([])
    yield app


class TestSettingsPage:
    def test_page_created(self, qapp):
        from verbamind.gui.pages.settings_page import SettingsPage

        page = SettingsPage()
        assert page is not None

    def test_settings_has_microphone_section(self, qapp):
        from verbamind.gui.pages.settings_page import SettingsPage
        from PySide6.QtWidgets import QGroupBox

        page = SettingsPage()
        groups = page.findChildren(QGroupBox)
        titles = [g.title() for g in groups]
        assert any("audio" in t.lower() or "microphone" in t.lower() for t in titles)

    def test_settings_has_database_info(self, qapp):
        from verbamind.gui.pages.settings_page import SettingsPage
        from PySide6.QtWidgets import QLabel

        page = SettingsPage()
        labels = page.findChildren(QLabel, "db_path_label")
        assert len(labels) >= 1


class TestActivationPage:
    def test_page_created(self, qapp):
        from verbamind.gui.pages.activation_page import ActivationPage

        page = ActivationPage()
        assert page is not None

    def test_activation_has_license_input(self, qapp):
        from verbamind.gui.pages.activation_page import ActivationPage
        from PySide6.QtWidgets import QLineEdit

        page = ActivationPage()
        inputs = page.findChildren(QLineEdit)
        assert len(inputs) >= 1

    def test_activation_has_activate_button(self, qapp):
        from verbamind.gui.pages.activation_page import ActivationPage
        from PySide6.QtWidgets import QPushButton

        page = ActivationPage()
        buttons = page.findChildren(QPushButton)
        texts = [b.text() for b in buttons]
        assert any("activat" in t.lower() for t in texts)

    def test_activation_shows_status(self, qapp):
        from verbamind.gui.pages.activation_page import ActivationPage
        from PySide6.QtWidgets import QLabel

        page = ActivationPage()
        page.show_status("Activation successful", success=True)
        labels = page.findChildren(QLabel, "activation_status")
        assert len(labels) >= 1
