"""Audio playback controller — decrypts .vera files in memory for playback.

State machine: idle → loaded → playing ↔ paused → loaded.
"""

from typing import Any

from verbamind.config.config import get_config
from verbamind.security.encryptor import decrypt_bytes


def _get_pyaudio():
    import pyaudio
    return pyaudio


class Player:
    def __init__(self):
        config = get_config()["recording"]
        self._sample_rate = config["sample_rate"]
        self._channels = config["channels"]
        self._chunk = config["chunk_size"]
        self._state = "idle"
        self._filepath: str | None = None
        self._key: bytes | None = None
        self._decrypted: bytes | None = None
        self._position = 0.0

    @property
    def state(self) -> str:
        return self._state

    @property
    def position(self) -> float:
        return self._position

    def load(self, filepath: str, key: bytes) -> None:
        with open(filepath, "rb") as f:
            encrypted = f.read()
        self._decrypted = decrypt_bytes(encrypted, key)
        self._filepath = filepath
        self._key = key
        self._position = 0.0
        self._state = "loaded"

    def play(self) -> None:
        if self._state == "idle":
            raise RuntimeError("No file loaded")
        self._state = "playing"

    def pause(self) -> None:
        if self._state != "playing":
            raise RuntimeError("Not playing")
        self._state = "paused"

    def resume(self) -> None:
        if self._state != "paused":
            raise RuntimeError("Not paused")
        self._state = "playing"

    def stop(self) -> None:
        self._state = "loaded"
        self._position = 0.0

    def seek(self, position: float) -> None:
        self._position = max(0.0, position)
