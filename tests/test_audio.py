"""TDD tests for audio module — device enumeration, recording, playback, session management.

RED phase: all imports will fail since modules don't exist yet.
"""

import os
import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as td:
        yield td


@pytest.fixture
def sample_wav_bytes():
    return b"\x00" * 1024


class TestDeviceManager:
    def test_list_input_devices(self):
        from verbamind.backend.audio.device import list_input_devices

        devices = list_input_devices()
        assert isinstance(devices, list)

    def test_device_has_required_fields(self):
        from verbamind.backend.audio.device import list_input_devices

        devices = list_input_devices()
        if devices:
            d = devices[0]
            assert "index" in d
            assert "name" in d
            assert "channels" in d

    def test_default_channel_config(self):
        from verbamind.backend.audio.device import get_channel_config

        config = get_channel_config()
        assert "patient_input" in config
        assert "psychologist_input" in config
        assert isinstance(config["patient_input"], int)
        assert isinstance(config["psychologist_input"], int)

    def test_set_channel_config(self):
        from verbamind.backend.audio.device import get_channel_config, set_channel_config

        original = get_channel_config()
        set_channel_config(patient_input=0, psychologist_input=1)
        updated = get_channel_config()
        assert updated["patient_input"] == 0
        assert updated["psychologist_input"] == 1
        set_channel_config(**original)


class TestRecorder:
    def test_initial_state_is_idle(self):
        from verbamind.backend.audio.recorder import Recorder

        r = Recorder(mock=True)
        assert r.state == "idle"

    def test_start_recording(self, temp_dir):
        from verbamind.backend.audio.recorder import Recorder

        path = Path(temp_dir) / "test.vera"
        r = Recorder(mock=True)
        r.start(filepath=str(path), duration=None)
        assert r.state == "recording"

    def test_stop_recording(self, temp_dir):
        from verbamind.backend.audio.recorder import Recorder

        path = Path(temp_dir) / "test.vera"
        r = Recorder(mock=True)
        r.start(filepath=str(path))
        r.stop()
        assert r.state == "idle"

    def test_pause_resume(self, temp_dir):
        from verbamind.backend.audio.recorder import Recorder

        path = Path(temp_dir) / "test.vera"
        r = Recorder(mock=True)
        r.start(filepath=str(path))
        r.pause()
        assert r.state == "paused"
        r.resume()
        assert r.state == "recording"

    def test_cannot_start_while_recording(self, temp_dir):
        from verbamind.backend.audio.recorder import Recorder

        path1 = Path(temp_dir) / "test1.vera"
        path2 = Path(temp_dir) / "test2.vera"
        r = Recorder(mock=True)
        r.start(filepath=str(path1))
        with pytest.raises(RuntimeError, match="already recording"):
            r.start(filepath=str(path2))

    def test_cannot_stop_when_idle(self):
        from verbamind.backend.audio.recorder import Recorder

        r = Recorder(mock=True)
        with pytest.raises(RuntimeError, match="not recording"):
            r.stop()

    def test_recording_metadata(self, temp_dir):
        from verbamind.backend.audio.recorder import Recorder

        path = Path(temp_dir) / "session_001.vera"
        r = Recorder(mock=True)
        r.start(filepath=str(path))
        info = r.info()
        assert info["filepath"] == str(path)
        assert "started_at" in info
        assert info["state"] == "recording"


class TestPlayer:
    def test_initial_state(self):
        from verbamind.backend.audio.player import Player

        p = Player()
        assert p.state == "idle"

    def test_load_and_play(self, temp_dir):
        from verbamind.backend.audio.player import Player
        from verbamind.security.encryptor import encrypt_bytes, generate_aes_key

        key = generate_aes_key()
        test_file = Path(temp_dir) / "test.vera"
        test_file.write_bytes(encrypt_bytes(b"fake audio", key))

        p = Player()
        p.load(filepath=str(test_file), key=key)
        assert p.state == "loaded"
        p.play()
        assert p.state == "playing"

    def test_pause_and_resume(self, temp_dir):
        from verbamind.backend.audio.player import Player
        from verbamind.security.encryptor import encrypt_bytes, generate_aes_key

        key = generate_aes_key()
        test_file = Path(temp_dir) / "test.vera"
        test_file.write_bytes(encrypt_bytes(b"fake audio", key))

        p = Player()
        p.load(filepath=str(test_file), key=key)
        p.play()
        p.pause()
        assert p.state == "paused"
        p.resume()
        assert p.state == "playing"

    def test_stop(self, temp_dir):
        from verbamind.backend.audio.player import Player
        from verbamind.security.encryptor import encrypt_bytes, generate_aes_key

        key = generate_aes_key()
        test_file = Path(temp_dir) / "test.vera"
        test_file.write_bytes(encrypt_bytes(b"fake audio", key))

        p = Player()
        p.load(filepath=str(test_file), key=key)
        p.play()
        p.stop()
        assert p.state == "loaded"

    def test_seek(self, temp_dir):
        from verbamind.backend.audio.player import Player
        from verbamind.security.encryptor import encrypt_bytes, generate_aes_key

        key = generate_aes_key()
        test_file = Path(temp_dir) / "test.vera"
        test_file.write_bytes(encrypt_bytes(b"fake audio", key))

        p = Player()
        p.load(filepath=str(test_file), key=key)
        p.seek(10.0)
        assert p.position == 10.0

    def test_cannot_play_without_load(self):
        from verbamind.backend.audio.player import Player

        p = Player()
        with pytest.raises(RuntimeError, match="No file loaded"):
            p.play()


class TestSessionManager:
    def test_create_session(self, temp_dir):
        from verbamind.backend.audio.session_manager import SessionManager

        mgr = SessionManager(recordings_dir=temp_dir)
        session = mgr.create_session(patient_id=1, psychologist_id=1)
        assert "session_id" in session
        assert session["filepath"].endswith(".vera")
        assert Path(temp_dir, session["filepath"]).parent.exists()

    def test_list_sessions(self, temp_dir):
        from verbamind.backend.audio.session_manager import SessionManager

        mgr = SessionManager(recordings_dir=temp_dir)
        mgr.create_session(patient_id=1, psychologist_id=1)
        mgr.create_session(patient_id=2, psychologist_id=1)
        sessions = mgr.list_sessions()
        assert len(sessions) == 2

    def test_delete_session(self, temp_dir):
        from verbamind.backend.audio.session_manager import SessionManager

        mgr = SessionManager(recordings_dir=temp_dir)
        session = mgr.create_session(patient_id=1, psychologist_id=1)
        filepath = Path(temp_dir, session["filepath"])
        filepath.write_bytes(b"fake encrypted data")
        assert filepath.exists()
        mgr.delete_session(session["session_id"])
        assert not filepath.exists()

    def test_get_session(self, temp_dir):
        from verbamind.backend.audio.session_manager import SessionManager

        mgr = SessionManager(recordings_dir=temp_dir)
        created = mgr.create_session(patient_id=1, psychologist_id=1)
        fetched = mgr.get_session(created["session_id"])
        assert fetched["patient_id"] == 1
        assert fetched["psychologist_id"] == 1
