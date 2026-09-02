"""Overlapping audio framing (numpy) — replaces librosa.util.frame."""

import numpy as np
from numpy.lib.stride_tricks import sliding_window_view

from verbamind.ai.speech_to_nonverbal.config import FRAME_DURATION, FRAME_OVERLAP


def frame_audio(audio, sr):
    """Split audio into overlapping frames (rows = frames)."""
    frame_length = int(FRAME_DURATION * sr)
    hop_length = int(frame_length * (1 - FRAME_OVERLAP))

    audio = np.asarray(audio)
    if len(audio) < frame_length:
        return np.empty((0, frame_length))

    n_frames = 1 + (len(audio) - frame_length) // hop_length
    return sliding_window_view(audio, frame_length)[::hop_length][:n_frames]
