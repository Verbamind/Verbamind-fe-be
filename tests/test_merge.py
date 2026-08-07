"""TDD tests for merged verbatim engine — merges verbal (STT) + non-verbal (SER) data.

RED phase: all imports will fail since modules don't exist yet.
"""

import pytest


class TestMergeService:
    def test_merge_verbal_only(self):
        from verbamind.backend.ai_pipeline.merge_service import MergeService

        svc = MergeService()
        stt_segments = [
            {"text": "Hello", "start": 0.0, "end": 1.0, "channel": 0, "speaker": "patient"},
            {"text": "Hi there", "start": 1.5, "end": 3.0, "channel": 1, "speaker": "psychologist"},
        ]
        merged = svc.merge(verbal=stt_segments, non_verbal=[])
        assert len(merged) == 2
        assert merged[0]["speaker"] == "patient"
        assert merged[0]["text"] == "Hello"
        assert merged[0]["emotion"] is None

    def test_merge_with_ser_data(self):
        from verbamind.backend.ai_pipeline.merge_service import MergeService

        svc = MergeService()
        stt = [
            {"text": "I feel anxious", "start": 0.0, "end": 2.0, "channel": 0, "speaker": "patient"},
        ]
        ser = [
            {"emotion": "anxious", "confidence": 0.85, "segment_start": 0.0, "segment_end": 2.0},
        ]
        merged = svc.merge(verbal=stt, non_verbal=ser)
        assert merged[0]["emotion"] == "anxious"
        assert merged[0]["emotion_confidence"] == 0.85

    def test_merge_overlapping_ser_takes_most_confident(self):
        from verbamind.backend.ai_pipeline.merge_service import MergeService

        svc = MergeService()
        stt = [
            {"text": "Long reply", "start": 0.0, "end": 5.0, "channel": 0, "speaker": "patient"},
        ]
        ser = [
            {"emotion": "sad", "confidence": 0.6, "segment_start": 0.0, "segment_end": 5.0},
            {"emotion": "anxious", "confidence": 0.9, "segment_start": 0.0, "segment_end": 5.0},
        ]
        merged = svc.merge(verbal=stt, non_verbal=ser)
        assert merged[0]["emotion"] == "anxious"

    def test_merge_partial_overlap(self):
        from verbamind.backend.ai_pipeline.merge_service import MergeService

        svc = MergeService()
        stt = [
            {"text": "Segment A", "start": 0.0, "end": 2.0, "channel": 0, "speaker": "patient"},
            {"text": "Segment B", "start": 2.0, "end": 4.0, "channel": 0, "speaker": "patient"},
        ]
        ser = [
            {"emotion": "calm", "confidence": 0.8, "segment_start": 1.5, "segment_end": 3.0},
        ]
        merged = svc.merge(verbal=stt, non_verbal=ser)
        assert merged[0]["emotion"] == "calm"
        assert merged[1]["emotion"] == "calm"

    def test_merge_output_has_all_required_fields(self):
        from verbamind.backend.ai_pipeline.merge_service import MergeService

        svc = MergeService()
        stt = [
            {"text": "Test", "start": 0.0, "end": 1.0, "channel": 0, "speaker": "patient"},
        ]
        merged = svc.merge(verbal=stt, non_verbal=[])
        fields = {"speaker", "text", "start", "end", "emotion", "emotion_confidence"}
        assert fields.issubset(set(merged[0].keys()))

    def test_merge_empty_input(self):
        from verbamind.backend.ai_pipeline.merge_service import MergeService

        svc = MergeService()
        assert svc.merge(verbal=[], non_verbal=[]) == []

    def test_merge_segments_ordered_by_start_time(self):
        from verbamind.backend.ai_pipeline.merge_service import MergeService

        svc = MergeService()
        stt = [
            {"text": "B", "start": 2.0, "end": 3.0, "channel": 0, "speaker": "patient"},
            {"text": "A", "start": 0.0, "end": 1.0, "channel": 0, "speaker": "patient"},
        ]
        merged = svc.merge(verbal=stt, non_verbal=[])
        assert merged[0]["start"] == 0.0
        assert merged[1]["start"] == 2.0

    def test_to_verbatim_text(self):
        from verbamind.backend.ai_pipeline.merge_service import MergeService

        svc = MergeService()
        stt = [
            {"text": "Hello", "start": 0.0, "end": 1.0, "channel": 0, "speaker": "patient"},
            {"text": "Hi there", "start": 1.5, "end": 3.0, "channel": 1, "speaker": "psychologist"},
        ]
        merged = svc.merge(verbal=stt, non_verbal=[])
        text = svc.to_verbatim_text(merged)
        assert "Patient: Hello" in text
        assert "Psychologist: Hi there" in text

    def test_to_verbatim_text_includes_emotions(self):
        from verbamind.backend.ai_pipeline.merge_service import MergeService

        svc = MergeService()
        stt = [
            {"text": "I'm scared", "start": 0.0, "end": 1.0, "channel": 0, "speaker": "patient"},
        ]
        ser = [
            {"emotion": "fearful", "confidence": 0.95, "segment_start": 0.0, "segment_end": 1.0},
        ]
        merged = svc.merge(verbal=stt, non_verbal=ser)
        text = svc.to_verbatim_text(merged)
        assert "fearful" in text
