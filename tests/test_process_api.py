"""TDD tests for POST /api/v1/process — full AI pipeline endpoint.

Whisper and Ollama are mocked; audio_io/merge/persist run real.
"""

import uuid
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from verbamind.security.token import get_token


@pytest.fixture()
def client():
    from verbamind.backend.main import app

    with TestClient(app, headers={"X-VerbaMind-Token": get_token()}) as c:
        yield c


MOCK_SEGMENTS = [
    {"text": "Saya sering cemas di malam hari.", "start": 0.0, "end": 2.5, "channel": 0},
    {"text": "Bagaimana perasaan Anda minggu ini?", "start": 3.0, "end": 5.0, "channel": 0},
]

MOCK_NONVERBAL = [
    {
        "frame": 0, "timestamp": 0.0,
        "current_loudness": -30.0, "baseline_loudness": -35.0,
        "delta_loudness": 5.0, "loudness_category": "High",
        "current_pitch": 180.0, "baseline_pitch": 175.0,
        "delta_pitch": 5.0, "pitch_category": "No Significant Change",
    },
]

MOCK_BIRP = {
    "behavior": "Pasien tampak cemas.",
    "intervention": "Psikolog melakukan validasi emosi.",
    "response": "Pasien terbuka.",
    "plan": "Lanjut eksplorasi sesi depan.",
}


def _make_wav() -> bytes:
    from verbamind.backend.ai_pipeline.audio_io import pcm_to_wav_bytes

    return pcm_to_wav_bytes(b"\x00\x01" * 16000)  # 1s of near-silence


def _write_wav_in_recordings() -> Path:
    rec = Path("recordings")
    rec.mkdir(parents=True, exist_ok=True)
    path = rec / f"_test_{uuid.uuid4().hex[:8]}.wav"
    path.write_bytes(_make_wav())
    return path


class TestProcessEndpoint:
    def test_process_missing_params(self, client):
        r = client.post("/api/v1/process", json={})
        assert r.status_code == 422

    def test_process_rejects_path_traversal(self, client):
        r = client.post(
            "/api/v1/process",
            json={"session_db_id": 1, "audio_path": "../important.txt"},
        )
        body = r.json()
        assert body["status"] == "error"
        assert "memuat audio" in body["message"].lower()

    def test_process_audio_not_found(self, client):
        r = client.post(
            "/api/v1/process",
            json={"session_db_id": 1, "audio_path": "recordings/nonexistent.wav"},
        )
        body = r.json()
        assert body["status"] == "error"
        assert "memuat audio" in body["message"].lower()

    def test_full_pipeline_persists_to_db(self, client):
        p = client.post("/api/v1/patients", json={"name": "Proc Test"}).json()
        s = client.post("/api/v1/sessions", json={"patient_id": p["id"]}).json()
        wav_file = _write_wav_in_recordings()
        try:
            def fake_transcribe(self, audio_data, *args, **kwargs):
                return MOCK_SEGMENTS

            def fake_nonverbal(self, audio_bytes, sr=22050):
                return MOCK_NONVERBAL

            with (
                patch(
                    "verbamind.backend.ai_pipeline.transcribe_service.TranscribeService.transcribe",
                    fake_transcribe,
                ),
                patch(
                    "verbamind.backend.ai_pipeline.speech_to_nonverbal_service."
                    "SpeechToNonverbalService.analyze_bytes",
                    fake_nonverbal,
                ),
                patch(
                    "verbamind.backend.ai_pipeline.birp_generator.BIRPGenerator.generate",
                    return_value=MOCK_BIRP,
                ),
            ):
                r = client.post(
                    "/api/v1/process",
                    json={
                        "session_db_id": s["id"],
                        "audio_path": str(wav_file),
                        "channels": 1,
                    },
                )
            body = r.json()
            assert body["status"] == "ok", body
            assert body["transcript_count"] == 2
            assert body["nonverbal_count"] == 1
            assert body["birp"] == MOCK_BIRP

            # Verify persistence
            det = client.get(f"/api/v1/sessions/{s['id']}").json()
            assert det["birp"]["behavior"] == "Pasien tampak cemas."
            assert det["session"]["birp_status"] == "Draft"
            assert len(det["segments"]) == 2
            patient_segs = [x for x in det["segments"] if x["speaker"] == "patient"]
            assert patient_segs[0]["emotion"] == "High"
        finally:
            wav_file.unlink(missing_ok=True)
            client.delete(f"/api/v1/patients/{p['id']}")

    def test_stt_failure_returns_error(self, client):
        p = client.post("/api/v1/patients", json={"name": "Err Test"}).json()
        s = client.post("/api/v1/sessions", json={"patient_id": p["id"]}).json()
        wav_file = _write_wav_in_recordings()
        try:
            with patch(
                "verbamind.backend.ai_pipeline.transcribe_service.TranscribeService.transcribe_channel",
                side_effect=RuntimeError("whisper down"),
            ):
                r = client.post(
                    "/api/v1/process",
                    json={"session_db_id": s["id"], "audio_path": str(wav_file)},
                )
            body = r.json()
            assert body["status"] == "error"
            assert any("STT" in e for e in body["errors"])
        finally:
            wav_file.unlink(missing_ok=True)
            client.delete(f"/api/v1/patients/{p['id']}")


class TestAuth:
    def test_requests_require_token(self):
        from verbamind.backend.main import app

        with TestClient(app) as c:  # no auth header
            r = c.get("/api/v1/health")
            assert r.status_code == 401


class TestAudioIO:
    def test_pcm_to_wav_roundtrip(self):
        from verbamind.backend.ai_pipeline.audio_io import (
            pcm_to_wav_bytes,
            wav_bytes_to_pcm,
        )

        pcm = b"\x01\x02" * 1000
        wav = pcm_to_wav_bytes(pcm, channels=1)
        out_pcm, ch, sr = wav_bytes_to_pcm(wav)
        assert out_pcm == pcm
        assert ch == 1
        assert sr == 16000

    def test_split_stereo(self):
        import struct

        from verbamind.backend.ai_pipeline.audio_io import split_stereo_pcm

        stereo = struct.pack("<4h", 1, 2, 3, 4)
        left, right = split_stereo_pcm(stereo)
        assert struct.unpack("<2h", left) == (1, 3)
        assert struct.unpack("<2h", right) == (2, 4)

    def test_split_to_channel_wavs_mono(self):
        from verbamind.backend.ai_pipeline.audio_io import split_to_channel_wavs

        wavs = split_to_channel_wavs(b"\x00\x01" * 100, channels=1)
        assert len(wavs) == 1
        assert wavs[0][:4] == b"RIFF"

    def test_split_to_channel_wavs_stereo(self):
        import struct

        from verbamind.backend.ai_pipeline.audio_io import (
            pcm_to_wav_bytes,
            split_to_channel_wavs,
        )

        stereo_pcm = struct.pack("<8h", 1, 2, 3, 4, 5, 6, 7, 8)
        wav = pcm_to_wav_bytes(stereo_pcm, channels=2)
        wavs = split_to_channel_wavs(wav)
        assert len(wavs) == 2
