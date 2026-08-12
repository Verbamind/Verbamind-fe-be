"""TDD tests for SER (nonverbal cue detection) service.

Tests the SERService that wraps the Verbamind_SpeechToNonverbalInformation
pipeline and produces per-frame NonverbalResult-ready dicts.
"""

import os
from pathlib import Path

import pytest

FIXTURES = Path(__file__).parent / "fixtures" / "audio"


class TestSERService:
    def test_service_created(self):
        from verbamind.backend.ai_pipeline.ser_service import SERService

        svc = SERService()
        assert svc is not None

    def test_analyze_sine_wave(self):
        """Sine wave should produce many frames with loudness categories."""
        from verbamind.backend.ai_pipeline.ser_service import SERService

        wav_path = str(FIXTURES / "sine_300Hz.wav")
        if not os.path.exists(wav_path):
            pytest.skip("sine fixture missing")

        svc = SERService()
        results = svc.analyze_file(wav_path)

        assert isinstance(results, list)
        assert len(results) > 0

        first = results[0]
        assert "frame" in first
        assert "timestamp" in first
        assert "current_loudness" in first
        assert "baseline_loudness" in first
        assert "delta_loudness" in first
        assert "loudness_category" in first
        assert "current_pitch" in first
        assert "baseline_pitch" in first
        assert "delta_pitch" in first
        assert "pitch_category" in first

    def test_analyze_categories_valid(self):
        """All loudness/pitch categories must be from the known set."""
        from verbamind.backend.ai_pipeline.ser_service import SERService

        wav_path = str(FIXTURES / "sine_300Hz.wav")
        if not os.path.exists(wav_path):
            pytest.skip("sine fixture missing")

        svc = SERService()
        results = svc.analyze_file(wav_path)

        valid = {
            "Very Low", "Low", "No Significant Change",
            "High", "Very High", "Unvoiced",
        }
        for r in results:
            assert r["loudness_category"] in valid, f"Invalid loudness: {r['loudness_category']}"
            assert r["pitch_category"] in valid, f"Invalid pitch: {r['pitch_category']}"

    def test_timestamps_monotonic(self):
        """Frame timestamps should be monotonically increasing."""
        from verbamind.backend.ai_pipeline.ser_service import SERService

        wav_path = str(FIXTURES / "sine_300Hz.wav")
        if not os.path.exists(wav_path):
            pytest.skip("sine fixture missing")

        svc = SERService()
        results = svc.analyze_file(wav_path)

        timestamps = [r["timestamp"] for r in results]
        for i in range(1, len(timestamps)):
            assert timestamps[i] >= timestamps[i - 1], "Timestamps not monotonic"

    def test_frame_indices_sequential(self):
        """Frame indices should be sequential integers."""
        from verbamind.backend.ai_pipeline.ser_service import SERService

        wav_path = str(FIXTURES / "sine_300Hz.wav")
        if not os.path.exists(wav_path):
            pytest.skip("sine fixture missing")

        svc = SERService()
        results = svc.analyze_file(wav_path)

        frames = [r["frame"] for r in results]
        for i in range(1, len(frames)):
            assert frames[i] == frames[i - 1] + 1, f"Frame gap at {i}"


class TestSEREndpoint:
    def test_router_registered(self):
        from verbamind.backend.api.ser_router import router

        routes = [r.path for r in router.routes]
        assert "/api/v1/ser/analyze" in routes
