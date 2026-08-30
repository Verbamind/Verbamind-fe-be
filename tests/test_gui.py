"""Tests for GUI scaffolding — verifies imports and window creation."""

import pytest
from PySide6.QtWidgets import QApplication


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance() or QApplication([])
    yield app


class TestMainWindow:
    def test_mainwindow_creation(self, qapp):
        from verbamind.gui.windows.main_window import MainWindow

        window = MainWindow()
        assert "erbamind" in window.windowTitle().lower()
        assert window.minimumWidth() == 1024
        assert window.minimumHeight() == 680
        window.close()


class TestBackendImports:
    def test_backend_imports(self):
        from verbamind.backend.main import app

        assert app.title == "VerbaMind Backend"
        assert app.version == "0.1.0"

    def test_config_port(self):
        from verbamind.config.config import get_backend_port

        assert get_backend_port() == 8000
