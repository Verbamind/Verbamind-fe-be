"""E2E integration test — full VerbaMind pipeline.

Tests the complete flow: record → encrypt → decrypt → STT → SER → merge → BIRP.
Uses mocks for Whisper and Ollama (models not bundled in dev).
"""

import asyncio
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as td:
        yield td


@pytest.fixture
def sample_wav_path():
    """Path to the sine wave fixture for SER testing."""
    return str(Path(__file__).parent / "fixtures" / "audio" / "sine_300Hz.wav")


class TestFullPipelineE2E:
    """End-to-end: record → encrypt → decrypt → STT → SER → merge → BIRP."""

    def test_encrypt_decrypt_roundtrip(self, temp_dir):
        """Step 1: Audio recorded → AES-256 encrypt → .vera → decrypt."""
        from verbamind.security.encryptor import (
            decrypt_file,
            encrypt_bytes,
            encrypt_file,
            generate_aes_key,
        )

        original_audio = b"FAKE_AUDIO_DATA_FOR_TESTING" * 100
        key = generate_aes_key()

        # Encrypt
        input_path = Path(temp_dir) / "raw.wav"
        encrypted_path = Path(temp_dir) / "session.vera"
        input_path.write_bytes(original_audio)
        encrypt_file(str(input_path), str(encrypted_path), key)

        assert encrypted_path.exists()
        assert encrypted_path.read_bytes() != original_audio

        # Decrypt
        decrypted_path = Path(temp_dir) / "decrypted.wav"
        decrypt_file(str(encrypted_path), str(decrypted_path), key)
        assert decrypted_path.read_bytes() == original_audio

    def test_session_manager_lifecycle(self, temp_dir):
        """Step 2: Session creation → list → delete."""
        from verbamind.backend.audio.session_manager import SessionManager

        mgr = SessionManager(recordings_dir=temp_dir)

        # Create
        s1 = mgr.create_session(patient_id=1, psychologist_id=1)
        s2 = mgr.create_session(patient_id=2, psychologist_id=1)
        assert len(mgr.list_sessions()) == 2

        # Delete with file
        vera_path = Path(temp_dir) / s1["filepath"]
        vera_path.write_bytes(b"encrypted")
        mgr.delete_session(s1["session_id"])
        assert not vera_path.exists()
        assert len(mgr.list_sessions()) == 1

    def test_stt_to_merge_pipeline(self):
        """Step 3-4: STT (mock) → SpeakerLabeler → MergeService."""
        from verbamind.backend.ai_pipeline.merge_service import MergeService
        from verbamind.backend.ai_pipeline.speaker_labeler import SpeakerLabeler
        from verbamind.backend.ai_pipeline.transcribe_service import TranscribeService

        # STT (mock mode)
        stt = TranscribeService(mock=True)
        segments = stt.transcribe(b"fake audio")

        # Speaker labeling
        labeler = SpeakerLabeler(patient_channel=0, psychologist_channel=1)
        labeled = labeler.label(segments)

        # Merge
        merge = MergeService()
        merged = merge.merge(verbal=labeled, non_verbal=[])

        assert len(merged) > 0
        assert "speaker" in merged[0]
        assert "text" in merged[0]

    def test_ser_analysis(self, sample_wav_path):
        """Step 5: SER nonverbal cue detection on sample audio."""
        if not os.path.exists(sample_wav_path):
            pytest.skip("Audio fixture missing")

        from verbamind.backend.ai_pipeline.ser_service import SERService

        svc = SERService()
        results = svc.analyze_file(sample_wav_path)

        assert len(results) > 0
        assert results[0]["loudness_category"] in {
            "Very Low", "Low", "No Significant Change", "High", "Very High"
        }

    def test_birp_generation_with_mock_llm(self):
        """Step 6: BIRP generation with mocked LLM."""
        from verbamind.backend.ai_pipeline.birp_generator import BIRPGenerator

        mock_llm = MagicMock()
        mock_llm.generate.return_value = json.dumps({
            "behavior": "Pasien menunjukkan kecemasan.",
            "intervention": "Psikolog melakukan grounding technique.",
            "response": "Pasien merasa lebih tenang.",
            "plan": "Lanjutkan sesi minggu depan.",
        })
        mock_retriever = MagicMock()
        mock_retriever.retrieve.return_value = "Konteks referensi dummy."

        gen = BIRPGenerator(retriever=mock_retriever, llm=mock_llm)
        verbatim = {
            "id_sesi": "SES-E2E-01",
            "transkrip": [
                {"speaker": "Pasien", "teks": "Saya merasa cemas.", "emosi": "cemas"},
                {"speaker": "Psikolog", "teks": "Mari kita coba teknik grounding.", "emosi": ""},
            ],
        }
        birp = gen.generate(verbatim)

        assert birp["behavior"] == "Pasien menunjukkan kecemasan."
        assert birp["intervention"] == "Psikolog melakukan grounding technique."
        assert "cemas" in mock_llm.generate.call_args[0][0].lower()

    def test_security_activation_flow(self):
        """Step 7: License activation → validation → state check."""
        from verbamind.security.activation import (
            activate,
            deactivate,
            generate_license_key,
            get_hardware_id,
            is_activated,
            validate_license_key,
        )

        deactivate()
        assert not is_activated()

        hwid = get_hardware_id()
        key = generate_license_key(hwid, "secret-master-key")
        assert validate_license_key(key, hwid, "secret-master-key")
        assert not validate_license_key("WRONG", hwid, "secret-master-key")

        activate(key)
        assert is_activated()
        deactivate()
        assert not is_activated()

    def test_full_e2e_pipeline(self, sample_wav_path):
        """Complete pipeline: encrypt → decrypt → STT → SER → merge → BIRP."""
        # 1. Security: generate key
        from verbamind.security.encryptor import decrypt_bytes, encrypt_bytes, generate_aes_key

        key = generate_aes_key()
        original = b"RECORDING_DATA_PLACEHOLDER"
        encrypted = encrypt_bytes(original, key)
        decrypted = decrypt_bytes(encrypted, key)
        assert decrypted == original

        # 2. STT (mock)
        from verbamind.backend.ai_pipeline.transcribe_service import TranscribeService

        stt = TranscribeService(mock=True)
        segments = stt.transcribe(original)

        # 3. SER (if fixture available)
        nonverbal = []
        if os.path.exists(sample_wav_path):
            from verbamind.backend.ai_pipeline.ser_service import SERService

            ser = SERService()
            nonverbal_raw = ser.analyze_file(sample_wav_path)
            # Aggregate: take dominant category
            if nonverbal_raw:
                nonverbal = [{
                    "segment_start": 0.0,
                    "segment_end": 5.0,
                    "emotion": nonverbal_raw[0]["loudness_category"],
                    "confidence": 0.8,
                }]

        # 4. Merge
        from verbamind.backend.ai_pipeline.merge_service import MergeService

        merge = MergeService()
        merged = merge.merge(verbal=segments, non_verbal=nonverbal)

        # 5. BIRP (mock LLM)
        from verbamind.backend.ai_pipeline.birp_generator import BIRPGenerator

        mock_llm = MagicMock()
        mock_llm.generate.return_value = json.dumps({
            "behavior": "B", "intervention": "I",
            "response": "R", "plan": "P",
        })
        mock_retriever = MagicMock()
        mock_retriever.retrieve.return_value = "Context."

        gen = BIRPGenerator(retriever=mock_retriever, llm=mock_llm)
        verbatim_data = {
            "id_sesi": "E2E-FULL",
            "transkrip": [
                {"speaker": "Pasien", "teks": m["text"], "emosi": ""}
                for m in merged
            ],
        }
        birp = gen.generate(verbatim_data)

        # Verify full pipeline output
        assert all(k in birp for k in ("behavior", "intervention", "response", "plan"))
        assert len(merged) > 0
        assert decrypted == original


class TestAPIIntegration:
    """API endpoints respond correctly."""

    def test_health_check(self):
        from fastapi.testclient import TestClient

        from verbamind.backend.main import app

        client = TestClient(app)
        resp = client.get("/api/v1/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"

    def test_stt_router_exists(self):
        from verbamind.backend.api.transcribe_router import router

        assert "/api/v1/stt/transcribe" in [r.path for r in router.routes]

    def test_ser_router_exists(self):
        from verbamind.backend.api.ser_router import router

        assert "/api/v1/ser/analyze" in [r.path for r in router.routes]

    def test_birp_router_exists(self):
        from verbamind.backend.api.birp_router import router

        assert "/api/v1/birp/generate" in [r.path for r in router.routes]
