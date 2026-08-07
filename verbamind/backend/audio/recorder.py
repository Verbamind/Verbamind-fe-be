"""Dual-channel audio recording controller — state machine: idle → recording → paused."""

import threading
from datetime import datetime, timezone
from typing import Any

from verbamind.config.config import get_config
from verbamind.security.encryptor import encrypt_bytes, generate_aes_key


def _get_pyaudio():
    import pyaudio
    return pyaudio


class Recorder:
    def __init__(self, mock: bool = False):
        config = get_config()["recording"]
        self._sample_rate = config["sample_rate"]
        self._channels = config["channels"]
        self._chunk = config["chunk_size"]
        self._mock = mock
        self._state = "idle"
        self._filepath: str | None = None
        self._started_at: datetime | None = None
        self._frames: list[bytes] = []
        self._session_key: bytes | None = None
        self._thread: Any = None
        self._stream: Any = None
        self._audio: Any = None

    @property
    def state(self) -> str:
        return self._state

    def start(self, filepath: str, duration: float | None = None) -> None:
        if self._state != "idle":
            raise RuntimeError("already recording")
        self._filepath = filepath
        self._started_at = datetime.now(timezone.utc)
        self._session_key = generate_aes_key()
        self._frames = []
        self._state = "recording"
        if self._mock:
            return
        pyaudio = _get_pyaudio()
        self._audio = pyaudio.PyAudio()
        self._stream = self._audio.open(
            format=pyaudio.paInt16,
            channels=self._channels,
            rate=self._sample_rate,
            input=True,
            frames_per_buffer=self._chunk,
        )

    def stop(self) -> bytes:
        if self._state not in ("recording", "paused"):
            raise RuntimeError("not recording")
        if self._state == "paused" and self._stream and not self._mock:
            self._stream.start_stream()
        self._state = "idle"
        if self._stream and not self._mock:
            self._stream.stop_stream()
            self._stream.close()
            self._stream = None
        if self._audio and not self._mock:
            self._audio.terminate()
            self._audio = None
        raw = b"".join(self._frames)
        encrypted = encrypt_bytes(raw, self._session_key)
        with open(self._filepath, "wb") as f:
            f.write(encrypted)
        return self._session_key

    def pause(self) -> None:
        if self._state != "recording":
            raise RuntimeError("not recording")
        self._state = "paused"
        if self._stream and not self._mock:
            self._stream.stop_stream()

    def resume(self) -> None:
        if self._state != "paused":
            raise RuntimeError("not paused")
        self._state = "recording"
        if self._stream and not self._mock:
            self._stream.start_stream()

    def info(self) -> dict[str, Any]:
        return {
            "filepath": self._filepath,
            "started_at": self._started_at.isoformat() if self._started_at else None,
            "state": self._state,
            "frames": len(self._frames),
        }
