"""TDD integration tests — GUI ↔ Backend wiring.

RED phase: all imports will fail since modules don't exist yet.
"""

import json
import tempfile
from pathlib import Path

import pytest
from PySide6.QtWidgets import QApplication


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance() or QApplication([])
    yield app


@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as td:
        yield td


class TestAPIClient:
    def test_client_created(self):
        from verbamind.gui.api_client import VerbaMindClient

        client = VerbaMindClient()
        assert client is not None

    def test_client_health(self):
        from verbamind.gui.api_client import VerbaMindClient

        client = VerbaMindClient(base_url="http://127.0.0.1:8000")
        info = client.health()
        assert "status" in info

    def test_client_default_base_url(self):
        from verbamind.gui.api_client import VerbaMindClient

        client = VerbaMindClient()
        assert "127.0.0.1" in client.base_url


class TestRecordingIntegration:
    def test_recorder_creates_vera_file(self, temp_dir):
        from verbamind.backend.audio.recorder import Recorder

        path = Path(temp_dir) / "session.vera"
        r = Recorder(mock=True)
        r.start(filepath=str(path))
        r.stop()
        assert path.exists()
        assert path.stat().st_size > 0

    def test_recording_page_wires_recorder(self, qapp, temp_dir):
        from verbamind.gui.pages.recording_page import RecordingPage
        from verbamind.backend.audio.recorder import Recorder

        page = RecordingPage()
        recorder = Recorder(mock=True)
        path = Path(temp_dir) / "wired_test.vera"
        recorder.start(filepath=str(path))
        recorder.stop()
        assert path.exists()

    def test_device_config_populates(self, qapp):
        from verbamind.gui.widgets.device_config import DeviceConfig

        config = DeviceConfig()
        assert config.patient_combo.count() >= 1
        assert config.psychologist_combo.count() >= 1


class TestDashboardIntegration:
    def test_session_create_and_list(self, temp_dir):
        from verbamind.backend.audio.session_manager import SessionManager

        mgr = SessionManager(recordings_dir=temp_dir)
        s1 = mgr.create_session(patient_id=1, psychologist_id=1)
        s2 = mgr.create_session(patient_id=2, psychologist_id=1)
        sessions = mgr.list_sessions()
        assert len(sessions) == 2
        assert any(s["session_id"] == s1["session_id"] for s in sessions)


class TestMergeIntegration:
    def test_merge_to_verbatim_for_llm(self):
        from verbamind.backend.ai_pipeline.merge_service import MergeService

        svc = MergeService()
        stt = [
            {"text": "I feel anxious", "start": 0.0, "end": 1.0, "channel": 0, "speaker": "patient"},
        ]
        merged = svc.merge(verbal=stt, non_verbal=[])
        text = svc.to_verbatim_text(merged)
        assert "Patient: I feel anxious" in text


class TestActivationIntegration:
    def test_check_activation_state(self):
        from verbamind.security.activation import deactivate, is_activated

        from verbamind.gui.activation_service import check_activation

        deactivate()
        assert not check_activation()

    def test_activate_flow(self):
        from verbamind.security.activation import activate, deactivate, is_activated

        from verbamind.gui.activation_service import check_activation

        activate("test-key-123")
        assert is_activated()
        assert check_activation()
        deactivate()
