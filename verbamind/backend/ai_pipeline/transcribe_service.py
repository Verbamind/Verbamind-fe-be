"""Whisper STT transcription service — wraps faster-whisper (CTranslate2).

Uses lazy import so tests run without the model installed.
Model "small" is downloaded once to the local cache (offline afterwards).
faster-whisper runs on CTranslate2 (no PyTorch), keeping the backend small.
"""

import logging
import os
import tempfile
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_whisper_model = None


def _get_whisper_model(model_name: str = "small"):
    """Load (and cache) the faster-whisper model once per process."""
    global _whisper_model
    if _whisper_model is None:
        from faster_whisper import WhisperModel

        logger.info("Memuat model Whisper '%s'...", model_name)
        _whisper_model = WhisperModel(
            model_name, device="cpu", compute_type="int8"
        )
    return _whisper_model


class TranscribeService:
    def __init__(
        self,
        model_path: str = "small",
        mock: bool = True,
        language: str = "id",
    ):
        self._model_path = model_path
        self._model = None
        self._mock = mock
        self._language = language

    def transcribe(self, audio_data: bytes) -> list[dict[str, Any]]:
        """Transcribe WAV bytes -> segments [{text, start, end, channel: 0}]."""
        if not audio_data:
            return []
        if self._mock:
            return [{
                "text": "This is a mock transcription for testing.",
                "start": 0.0,
                "end": 2.5,
                "channel": 0,
            }]

        model = _get_whisper_model(self._model_path)
        segments: list[dict[str, Any]] = []

        fd, name = tempfile.mkstemp(suffix=".wav")
        os.close(fd)
        tmp_path = Path(name)
        try:
            tmp_path.write_bytes(audio_data)
            gen, _info = model.transcribe(
                str(tmp_path),
                language=self._language,
                word_timestamps=False,
            )
            for seg in gen:
                text = seg.text.strip()
                if not text:
                    continue
                segments.append({
                    "text": text,
                    "start": float(seg.start),
                    "end": float(seg.end),
                    "channel": 0,
                })
        finally:
            tmp_path.unlink(missing_ok=True)

        return segments

    def transcribe_channel(
        self, audio_data: bytes, channel: int
    ) -> list[dict[str, Any]]:
        """Transcribe one channel's mono WAV bytes, tagging segments with channel."""
        segments = self.transcribe(audio_data)
        return [{**seg, "channel": channel} for seg in segments]
