"""TDD tests for the session processing pipeline orchestrator.

RED phase: `verbamind.backend.ai_pipeline.process_service.ProcessService`
does not exist yet, so all imports fail until the GREEN phase.

The ProcessService ties the full AI pipeline together:
    transcribe -> speaker label -> SpeechToNonverbalInformation -> merge -> BIRP
"""

import json
from unittest.mock import MagicMock

import pytest

from verbamind.backend.ai_pipeline.process_service import (
    DEFAULT_NONVERBAL_CONFIDENCE,
    DEFAULT_SESSION_ID,
    ProcessService,
)


def _mock_segments():
    return [
        {"text": "Saya merasa cemas.", "start": 0.0, "end": 2.0, "channel": 0},
        {"text": "Mari coba teknik grounding.", "start": 2.5, "end": 5.0, "channel": 1},
    ]


def _mock_ser_frames():
    return [
        {"frame": 0, "timestamp": 0.0, "loudness_category": "High", "pitch_category": "No Significant Change"},
        {"frame": 1, "timestamp": 0.025, "loudness_category": "No Significant Change", "pitch_category": "Unvoiced"},
    ]


def _make_service():
    """Build a ProcessService with mocked dependencies and return both."""
    transcriber = MagicMock()
    ser = MagicMock()
    merger = MagicMock()
    labeler = MagicMock()
    birp = MagicMock()

    svc = ProcessService(
        transcribe_service=transcriber,
        nonverbal_service=ser,
        merge_service=merger,
        speaker_labeler=labeler,
        birp_generator=birp,
    )
    return svc, (transcriber, ser, merger, labeler, birp)


class TestProcessServiceUnit:
    """Unit tests — orchestration logic in isolation with mocked dependencies."""

    def test_process_happy_path_returns_ok(self):
        svc, (transcriber, ser, merger, labeler, birp) = _make_service()

        transcriber.transcribe.return_value = _mock_segments()
        labeler.label.return_value = [
            {**s, "speaker": "patient" if s["channel"] == 0 else "psychologist"}
            for s in _mock_segments()
        ]
        ser.analyze_bytes.return_value = _mock_ser_frames()
        merger.merge.return_value = [
            {"speaker": "patient", "text": "Saya merasa cemas.", "start": 0.0, "end": 2.0, "emotion": "High", "emotion_confidence": DEFAULT_NONVERBAL_CONFIDENCE},
        ]
        birp.generate.return_value = {
            "behavior": "B", "intervention": "I", "response": "R", "plan": "P",
        }

        result = svc.process(b"fake-audio", session_id="SES-1")

        assert result["status"] == "ok"
        assert result["session_id"] == "SES-1"
        assert result["transcript"] == labeler.label.return_value
        assert result["merged"] == merger.merge.return_value
        assert result["birp"]["behavior"] == "B"
        assert result["errors"] == []

    def test_process_default_session_id(self):
        svc, _ = _make_service()

        result = svc.process(b"fake-audio")

        assert result["session_id"] == DEFAULT_SESSION_ID

    def test_process_empty_audio_raises_value_error(self):
        svc, _ = _make_service()

        with pytest.raises(ValueError):
            svc.process(b"")

    def test_process_none_audio_raises_value_error(self):
        svc, _ = _make_service()

        with pytest.raises(ValueError):
            svc.process(None)

    def test_process_ser_failure_is_partial(self):
        svc, (transcriber, ser, merger, labeler, birp) = _make_service()

        transcriber.transcribe.return_value = _mock_segments()
        labeler.label.return_value = _mock_segments()
        ser.analyze_bytes.side_effect = RuntimeError("librosa missing")
        merger.merge.return_value = _mock_segments()
        birp.generate.return_value = {"behavior": "B", "intervention": "I", "response": "R", "plan": "P"}

        result = svc.process(b"fake-audio", session_id="SES-2")

        assert result["status"] == "partial"
        assert result["nonverbal"] == []
        assert any("SpeechToNonverbalInformation" in e for e in result["errors"])
        # BIRP still generated from verbal-only merge
        assert result["birp"] is not None

    def test_process_birp_failure_is_partial(self):
        svc, (transcriber, ser, merger, labeler, birp) = _make_service()

        transcriber.transcribe.return_value = _mock_segments()
        labeler.label.return_value = _mock_segments()
        ser.analyze_bytes.return_value = []
        merger.merge.return_value = _mock_segments()
        birp.generate.side_effect = RuntimeError("Ollama down")

        result = svc.process(b"fake-audio", session_id="SES-3")

        assert result["status"] == "partial"
        assert result["birp"] is None
        assert any("BIRP" in e for e in result["errors"])
        # Transcript + merge still available
        assert result["merged"] == _mock_segments()

    def test_process_transcribe_failure_returns_error(self):
        svc, (transcriber, _, _, _, _) = _make_service()

        transcriber.transcribe_channel.side_effect = FileNotFoundError("model not found")

        result = svc.process(b"fake-audio", session_id="SES-4")

        assert result["status"] == "error"
        assert result["transcript"] == []
        assert result["birp"] is None
        assert any("STT" in e for e in result["errors"])

    def test_process_empty_transcript_is_partial(self):
        svc, (transcriber, ser, merger, labeler, birp) = _make_service()

        transcriber.transcribe.return_value = []
        labeler.label.return_value = []
        ser.analyze_bytes.return_value = []
        merger.merge.return_value = []

        result = svc.process(b"fake-audio", session_id="SES-5")

        assert result["status"] == "partial"
        assert result["merged"] == []
        assert result["birp"] is None

    def test_process_converts_ser_frames_to_emotion_segments(self):
        svc, (transcriber, ser, merger, labeler, birp) = _make_service()

        transcriber.transcribe.return_value = _mock_segments()
        labeler.label.return_value = _mock_segments()
        ser.analyze_bytes.return_value = _mock_ser_frames()
        merger.merge.return_value = []
        birp.generate.return_value = {"behavior": "B", "intervention": "I", "response": "R", "plan": "P"}

        svc.process(b"fake-audio", session_id="SES-6")

        # The merger should receive emotion segments converted from SpeechToNonverbalInformation frames
        nonverbal_arg = merger.merge.call_args.kwargs["non_verbal"]
        assert len(nonverbal_arg) == 2
        assert nonverbal_arg[0]["emotion"] == "High"
        assert nonverbal_arg[0]["segment_start"] == 0.0
        assert nonverbal_arg[0]["segment_end"] > nonverbal_arg[0]["segment_start"]
        assert nonverbal_arg[0]["confidence"] == DEFAULT_NONVERBAL_CONFIDENCE

    def test_process_builds_verbatim_data_for_birp(self):
        svc, (transcriber, ser, merger, labeler, birp) = _make_service()

        transcriber.transcribe.return_value = _mock_segments()
        labeler.label.return_value = _mock_segments()
        ser.analyze_bytes.return_value = []
        merger.merge.return_value = [
            {"speaker": "patient", "text": "Saya merasa cemas.", "start": 0.0, "end": 2.0, "emotion": None, "emotion_confidence": None},
        ]
        birp.generate.return_value = {"behavior": "B", "intervention": "I", "response": "R", "plan": "P"}

        svc.process(b"fake-audio", session_id="SES-7")

        verbatim = birp.generate.call_args.kwargs["verbatim_data"]
        assert verbatim["id_sesi"] == "SES-7"
        assert verbatim["transkrip"][0]["teks"] == "Saya merasa cemas."
        assert verbatim["transkrip"][0]["speaker"] == "patient"
        assert verbatim["transkrip"][0]["emosi"] == ""  # None -> empty string

    def test_process_emotion_none_maps_to_empty_string(self):
        svc, (transcriber, ser, merger, labeler, birp) = _make_service()

        transcriber.transcribe.return_value = _mock_segments()
        labeler.label.return_value = _mock_segments()
        ser.analyze_bytes.return_value = []
        merger.merge.return_value = [
            {"speaker": "patient", "text": "x", "start": 0.0, "end": 1.0, "emotion": "High", "emotion_confidence": 0.8},
        ]
        birp.generate.return_value = {"behavior": "B", "intervention": "I", "response": "R", "plan": "P"}

        svc.process(b"fake-audio", session_id="SES-8")

        verbatim = birp.generate.call_args.kwargs["verbatim_data"]
        assert verbatim["transkrip"][0]["emosi"] == "High"


class TestProcessServiceIntegration:
    """Integration — real pipeline services with mocked LLM/retriever only."""

    def test_process_with_real_services(self):
        from verbamind.backend.ai_pipeline.birp_generator import BIRPGenerator
        from verbamind.backend.ai_pipeline.merge_service import MergeService
        from verbamind.backend.ai_pipeline.speaker_labeler import SpeakerLabeler
        from verbamind.backend.ai_pipeline.transcribe_service import TranscribeService

        mock_llm = MagicMock()
        mock_llm.generate.return_value = json.dumps({
            "behavior": "B", "intervention": "I", "response": "R", "plan": "P",
        })
        mock_retriever = MagicMock()
        mock_retriever.retrieve.return_value = "Konteks dummy."

        svc = ProcessService(
            transcribe_service=TranscribeService(mock=True),
            nonverbal_service=MagicMock(analyze_bytes=MagicMock(return_value=[])),
            merge_service=MergeService(),
            speaker_labeler=SpeakerLabeler(patient_channel=0, psychologist_channel=1),
            birp_generator=BIRPGenerator(retriever=mock_retriever, llm=mock_llm),
        )

        result = svc.process(b"fake-audio", session_id="SES-INT-1")

        assert result["status"] == "ok"
        assert len(result["merged"]) > 0
        assert result["merged"][0]["speaker"] in {"patient", "psychologist"}
        assert set(result["birp"]) == {"behavior", "intervention", "response", "plan"}
