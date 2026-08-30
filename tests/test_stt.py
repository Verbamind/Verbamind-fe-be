"""TDD tests for STT module — Whisper transcription + speaker labeling.

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


class TestTranscribeService:
    def test_transcribe_returns_segments(self):
        from verbamind.backend.ai_pipeline.transcribe_service import TranscribeService

        svc = TranscribeService(model_path="models/whisper/base.pt")
        segments = svc.transcribe(b"fake audio data")
        assert isinstance(segments, list)

    def test_each_segment_has_required_fields(self):
        from verbamind.backend.ai_pipeline.transcribe_service import TranscribeService

        svc = TranscribeService(model_path="models/whisper/base.pt")
        segments = svc.transcribe(b"fake audio data")
        if segments:
            seg = segments[0]
            assert "text" in seg
            assert "start" in seg
            assert "end" in seg
            assert "channel" in seg

    def test_transcribe_empty_audio(self):
        from verbamind.backend.ai_pipeline.transcribe_service import TranscribeService

        svc = TranscribeService(model_path="models/whisper/base.pt")
        segments = svc.transcribe(b"")
        assert segments == []

    def test_invalid_whisper_model_raises_clear_error(self):
        from verbamind.backend.ai_pipeline.transcribe_service import TranscribeService

        svc = TranscribeService(model_path="nonexistent-model", mock=False)
        with pytest.raises(RuntimeError):
            svc.transcribe(b"RIFF\xf0\x3f\x00\x00WAVEfmt ")


class TestSpeakerLabeler:
    def test_label_two_channel_segments(self):
        from verbamind.backend.ai_pipeline.speaker_labeler import SpeakerLabeler

        labeler = SpeakerLabeler(patient_channel=0, psychologist_channel=1)
        segments = [
            {"text": "Hello", "start": 0.0, "end": 1.0, "channel": 0},
            {"text": "Hi there", "start": 1.0, "end": 2.5, "channel": 1},
            {"text": "How are you", "start": 2.5, "end": 4.0, "channel": 0},
        ]
        labeled = labeler.label(segments)
        assert labeled[0]["speaker"] == "patient"
        assert labeled[1]["speaker"] == "psychologist"
        assert labeled[2]["speaker"] == "patient"

    def test_label_preserves_all_original_fields(self):
        from verbamind.backend.ai_pipeline.speaker_labeler import SpeakerLabeler

        labeler = SpeakerLabeler(patient_channel=0, psychologist_channel=1)
        segments = [
            {"text": "Test", "start": 0.0, "end": 1.0, "channel": 0},
        ]
        labeled = labeler.label(segments)
        assert labeled[0]["text"] == "Test"
        assert labeled[0]["start"] == 0.0
        assert labeled[0]["end"] == 1.0

    def test_unknown_channel_labeled_as_unknown(self):
        from verbamind.backend.ai_pipeline.speaker_labeler import SpeakerLabeler

        labeler = SpeakerLabeler(patient_channel=0, psychologist_channel=1)
        segments = [
            {"text": "???", "start": 0.0, "end": 1.0, "channel": 99},
        ]
        labeled = labeler.label(segments)
        assert labeled[0]["speaker"] == "unknown"

    def test_label_empty_segments(self):
        from verbamind.backend.ai_pipeline.speaker_labeler import SpeakerLabeler

        labeler = SpeakerLabeler(patient_channel=0, psychologist_channel=1)
        assert labeler.label([]) == []


class TestSTTAPI:
    def test_transcribe_endpoint_returns_501(self):
        """Verify the transcribe router exists and registers the endpoint."""
        from verbamind.backend.api.transcribe_router import router

        routes = [r.path for r in router.routes]
        assert "/api/v1/stt/transcribe" in routes
