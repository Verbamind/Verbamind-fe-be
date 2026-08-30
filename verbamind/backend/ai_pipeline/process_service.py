"""Session processing pipeline — orchestrates the full AI pipeline.

Flow (confirmed design):
  1. transcribe BOTH channels (patient ch0, psychologist ch1) via Whisper
  2. SpeechToNonverbalInformation analysis on PATIENT channel only
  3. merge: patient segments annotated with nonverbal cues; doctor segments plain
  4. BIRP narrative includes BOTH speakers (doctor context fills I & P fields)

Each stage is injected via constructor for testability; the ProcessService only
owns orchestration, error isolation, and data plumbing between stages.
"""

import logging
from typing import Any

from verbamind.ai.speech_to_nonverbal.config import FRAME_DURATION
from verbamind.backend.ai_pipeline.audio_io import split_to_channel_wavs

logger = logging.getLogger(__name__)

DEFAULT_SESSION_ID = "SESI-TIDAK-DIKETAHUI"
DEFAULT_NONVERBAL_CONFIDENCE = 0.8
PATIENT_CHANNEL = 0
PSYCHOLOGIST_CHANNEL = 1


class ProcessService:
    """Orchestrates STT (both channels) → SpeechToNonverbalInformation (patient)
    → merge → BIRP generation (patient + psychologist narrative)."""

    def __init__(
        self,
        transcribe_service: Any,
        nonverbal_service: Any,
        merge_service: Any,
        speaker_labeler: Any,
        birp_generator: Any,
    ):
        self._transcriber = transcribe_service
        self._nonverbal = nonverbal_service
        self._merger = merge_service
        self._labeler = speaker_labeler
        self._birp = birp_generator

    def process(
        self,
        audio_data: bytes,
        session_id: str | None = None,
        channels: int = 1,
    ) -> dict[str, Any]:
        """Run the full session processing pipeline.

        Args:
            audio_data: Decrypted audio bytes (WAV or raw PCM 16 kHz).
            session_id: Optional session identifier.
            channels: Channel count when audio_data is raw PCM.

        Returns:
            Result dict: session_id, status ("ok"|"partial"|"error"),
            transcript, nonverbal, merged, birp, errors.
        """
        if not audio_data:
            raise ValueError("audio_data is required (cannot be empty or None)")

        sid = session_id or DEFAULT_SESSION_ID
        errors: list[str] = []
        status = "ok"

        # Split into per-channel mono WAV (index 0 = patient, 1 = psychologist)
        channel_wavs = split_to_channel_wavs(audio_data, channels=channels)

        # Stage 1: transcribe every channel (fatal on failure)
        try:
            all_segments: list[dict[str, Any]] = []
            for ch_index, wav in enumerate(channel_wavs):
                segs = self._transcriber.transcribe_channel(wav, ch_index)
                all_segments.extend(segs)
        except Exception as exc:  # noqa: BLE001 - stage isolation
            logger.exception("STT transcription failed")
            return {
                "session_id": sid,
                "status": "error",
                "transcript": [],
                "nonverbal": [],
                "merged": [],
                "birp": None,
                "errors": [f"STT failed: {exc}"],
            }

        # Stage 2: speaker labeling (channel -> role)
        labeled = self._labeler.label(all_segments)

        # Stage 3: SpeechToNonverbalInformation — PATIENT channel only (non-fatal)
        nonverbal_frames: list[dict[str, Any]] = []
        try:
            patient_wav = channel_wavs[PATIENT_CHANNEL]
            nonverbal_frames = self._nonverbal.analyze_bytes(patient_wav)
        except Exception as exc:  # noqa: BLE001 - optional enrichment
            logger.warning("SpeechToNonverbalInformation failed: %s", exc)
            status = "partial"
            errors.append(f"SpeechToNonverbalInformation failed: {exc}")

        emotion_segments = self._frames_to_emotion_segments(nonverbal_frames)

        # Stage 4: merge (patient segments get nonverbal annotation; doctor plain)
        merged = self._merger.merge(verbal=labeled, non_verbal=emotion_segments)

        if not merged:
            if status == "ok":
                status = "partial"
            if not errors:
                errors.append("No speech detected in transcript")
            return {
                "session_id": sid,
                "status": status,
                "transcript": labeled,
                "nonverbal": nonverbal_frames,
                "merged": merged,
                "birp": None,
                "errors": errors,
            }

        # Stage 5: BIRP from BOTH speakers (patient + psychologist) (non-fatal)
        birp = None
        try:
            verbatim_data = self._build_verbatim_data(sid, merged)
            birp = self._birp.generate(verbatim_data=verbatim_data, session_id=sid)
        except Exception as exc:  # noqa: BLE001 - best-effort
            logger.warning("BIRP generation failed: %s", exc)
            status = "partial"
            errors.append(f"BIRP failed: {exc}")

        return {
            "session_id": sid,
            "status": status,
            "transcript": labeled,
            "nonverbal": nonverbal_frames,
            "merged": merged,
            "birp": birp,
            "errors": errors,
        }

    def _frames_to_emotion_segments(
        self,
        frames: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Convert per-frame nonverbal results into time-ranged emotion segments.

        Uses loudness category as the primary nonverbal cue. The detector emits
        no confidence score, so a fixed placeholder is assigned.
        """
        segments = []
        for frame in frames:
            start = float(frame.get("timestamp", 0.0))
            segments.append({
                "segment_start": start,
                "segment_end": start + FRAME_DURATION,
                "emotion": frame.get("loudness_category"),
                "confidence": DEFAULT_NONVERBAL_CONFIDENCE,
            })
        return segments

    def _build_verbatim_data(
        self,
        session_id: str,
        merged: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Map merged segments to the verbatim_data shape BIRPGenerator expects."""
        transkrip = [
            {
                "speaker": seg.get("speaker", "Tidak diketahui"),
                "teks": seg.get("text", ""),
                "emosi": seg.get("emotion") or "",
            }
            for seg in merged
        ]
        return {"id_sesi": session_id, "transkrip": transkrip}
