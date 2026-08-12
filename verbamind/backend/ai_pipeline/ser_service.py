"""SER Service — wraps Verbamind_SpeechToNonverbalInformation pipeline.

Loads audio file → extracts loudness + pitch features → runs adaptive baseline +
fuzzy inference → returns per-frame nonverbal results ready for DB persistence.
"""

import logging
from typing import Any

import librosa
import numpy as np

from verbamind.ai.ser.config import FRAME_DURATION, FRAME_OVERLAP, INITIAL_DURATION
from verbamind.ai.ser.features.loudness import compute_loudness
from verbamind.ai.ser.features.pitch import compute_pitch
from verbamind.ai.ser.pipeline.detector import NonverbalChangeDetector

logger = logging.getLogger(__name__)


class SERService:
    """Analyze audio for nonverbal cues (loudness + pitch changes per frame)."""

    def analyze_file(self, audio_path: str) -> list[dict[str, Any]]:
        """Load WAV file and run full nonverbal detection pipeline.

        Args:
            audio_path: Path to .wav audio file.

        Returns:
            List of dicts with keys: frame, timestamp, current_loudness,
            baseline_loudness, delta_loudness, loudness_category,
            current_pitch, baseline_pitch, delta_pitch, pitch_category.
        """
        audio, sr = librosa.load(audio_path, sr=None)
        return self._run_pipeline(audio, sr)

    def analyze_bytes(self, audio_bytes: bytes, sr: int = 22050) -> list[dict[str, Any]]:
        """Analyze audio from in-memory bytes (e.g., decrypted .vera content).

        Args:
            audio_bytes: Raw audio bytes (WAV format).
            sr: Sample rate (default 22050).

        Returns:
            Same as analyze_file().
        """
        import io
        audio, sr = librosa.load(io.BytesIO(audio_bytes), sr=None)
        return self._run_pipeline(audio, sr)

    def _run_pipeline(self, audio: np.ndarray, sr: int) -> list[dict[str, Any]]:
        # Feature extraction
        _, frame_loudness = compute_loudness(audio, sr)
        _, frame_pitch = compute_pitch(audio, sr)

        # Handle edge case: pitch all NaN (silent/unvoiced audio)
        if isinstance(frame_pitch, float) and np.isnan(frame_pitch):
            frame_pitch = [np.nan] * len(frame_loudness)

        # Calculate initial frames
        frame_length = int(FRAME_DURATION * sr)
        hop_length = int(frame_length * (1 - FRAME_OVERLAP))
        initial_samples = int(INITIAL_DURATION * sr)
        num_initial = max(1, min(
            ((initial_samples - frame_length) // hop_length) + 1,
            len(frame_loudness),
        ))

        # Run detector
        detector = NonverbalChangeDetector(initial_duration_frames=num_initial)
        loudness_df, pitch_df = detector.detect(frame_loudness, frame_pitch)

        # Merge into result dicts with timestamps
        results = []
        for i in range(len(loudness_df)):
            l_row = loudness_df.iloc[i]
            p_row = pitch_df.iloc[i]
            frame_idx = int(l_row["Frame"])
            timestamp = frame_idx * hop_length / sr

            results.append({
                "frame": frame_idx,
                "timestamp": timestamp,
                "current_loudness": float(l_row["Current_Loudness"]),
                "baseline_loudness": float(l_row["Baseline_Loudness"]),
                "delta_loudness": float(l_row["Delta_Loudness"]),
                "loudness_category": str(l_row["Loudness_Category"]),
                "current_pitch": None if np.isnan(p_row["Current_Pitch"]) else float(p_row["Current_Pitch"]),
                "baseline_pitch": None if np.isnan(p_row["Baseline_Pitch"]) else float(p_row["Baseline_Pitch"]),
                "delta_pitch": None if np.isnan(p_row["Delta_Pitch"]) else float(p_row["Delta_Pitch"]),
                "pitch_category": str(p_row["Pitch_Category"]),
            })

        logger.info(f"SER analysis complete: {len(results)} frames")
        return results
