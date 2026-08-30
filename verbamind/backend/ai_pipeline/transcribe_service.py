"""Whisper STT transcription service — wraps Whisper model, outputs timestamped segments.

Uses lazy import so tests run without Whisper/torch installed.
Model "small" is cached locally after first download (offline afterwards).
"""

import logging
import os
import tempfile
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_whisper_model = None


def _get_whisper_model(model_name: str = "small"):
    """Load (and cache) the Whisper model once per process."""
    global _whisper_model
    if _whisper_model is None:
        import whisper

        logger.info("Memuat model Whisper '%s'...", model_name)
        _whisper_model = whisper.load_model(model_name)
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
            result = model.transcribe(
                str(tmp_path),
                language=self._language,
                word_timestamps=False,
            )
            for seg in result.get("segments", []):
                text = seg.get("text", "").strip()
                if not text:
                    continue
                segments.append({
                    "text": text,
                    "start": float(seg.get("start", 0.0)),
                    "end": float(seg.get("end", 0.0)),
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
