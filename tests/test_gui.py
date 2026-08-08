"""Tests for GUI scaffolding — PySide6 window creation and properties."""

import sys

import pytest


@pytest.mark.skipif(
    sys.platform != "win32",
    reason="VerbaMind is Windows-only",
)
def test_mainwindow_creation():
    from PySide6.QtWidgets import QApplication

    from verbamind.main import MainWindow

    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    assert window.windowTitle() == "VerbaMind"
    assert window.minimumWidth() == 1024
    assert window.minimumHeight() == 680
    window.close()


def test_backend_imports():
    from verbamind.backend.main import app

    assert app.title == "VerbaMind Backend"
    assert app.version == "0.1.0"


def test_config_port():
    from verbamind.config.config import get_backend_port

    assert get_backend_port() == 8000
