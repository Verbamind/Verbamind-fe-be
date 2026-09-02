import numpy as np

from verbamind.ai.speech_to_nonverbal.features.framing import frame_audio


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
