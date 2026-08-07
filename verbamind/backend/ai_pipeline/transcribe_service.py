"""Whisper STT transcription service — wraps Whisper model, outputs timestamped segments.

Uses lazy import so tests run without Whisper/torch installed.
In production, requires: openai-whisper + torch in models/whisper/.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class TranscriptionSegment:
    text: str
    start: float
    end: float
    channel: int


class TranscribeService:
    def __init__(self, model_path: str = "models/whisper/base.pt", mock: bool = True):
        self._model_path = model_path
        self._model = None
        self._mock = mock

    def _load_model(self):
        import whisper

        model_file = Path(self._model_path)
        model_name = model_file.stem if model_file.suffix else self._model_path
        self._model = whisper.load_model(model_name)

    def transcribe(self, audio_data: bytes) -> list[dict[str, Any]]:
        if not audio_data:
            return []
        if self._mock:
            return [{
                "text": "This is a mock transcription for testing.",
                "start": 0.0,
                "end": 2.5,
                "channel": 0,
            }]
        if self._model is None:
            if not Path(self._model_path).exists():
                raise FileNotFoundError(f"Model not found: {self._model_path}")
            self._load_model()

        import tempfile
        import wave

        tmp_path = None
        try:
            tmp_path = Path(tempfile.mktemp(suffix=".wav"))
            with wave.open(str(tmp_path), "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(16000)
                wf.writeframes(audio_data)

            result = self._model.transcribe(str(tmp_path), word_timestamps=True)
            segments = []
            for seg in result.get("segments", []):
                segments.append({
                    "text": seg.get("text", "").strip(),
                    "start": seg.get("start", 0.0),
                    "end": seg.get("end", 0.0),
                    "channel": 0,
                })
            return segments
        finally:
            if tmp_path and tmp_path.exists():
                tmp_path.unlink(missing_ok=True)
