import librosa
import numpy as np

from verbamind.ai.ser.config import FRAME_DURATION, FRAME_OVERLAP


def frame_audio(audio, sr):
    """
    Split audio into overlapping frames.
    """

    frame_length = int(FRAME_DURATION * sr)

    hop_length = int(frame_length * (1 - FRAME_OVERLAP))

    frames = librosa.util.frame(
        audio,
        frame_length=frame_length,
        hop_length=hop_length
    )

    return frames.T


def compute_frame_loudness(frame):
    """
    Compute frame loudness using RMS.
    """

    rms = np.sqrt(np.mean(frame ** 2))

    return 20 * np.log10(rms + 1e-10)


def compute_loudness(audio, sr):

    frames = frame_audio(audio, sr)

    loudness = []

    for frame in frames:

        loudness.append(
            compute_frame_loudness(frame)
        )

    return float(np.median(loudness)), loudness
