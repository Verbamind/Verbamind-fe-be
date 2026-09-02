import numpy as np
from scipy.signal import find_peaks

from verbamind.ai.speech_to_nonverbal.config import (
    PITCH_CORRELATION_THRESHOLD,
    PITCH_MAX,
    PITCH_MIN,
    PITCH_PROMINENCE,
)
from verbamind.ai.speech_to_nonverbal.features.framing import frame_audio


def compute_autocorrelation(frame):
    """
    Calculate autocorrelation of the frame
    """

    frame = frame - np.mean(frame)

    corr = np.correlate(
        frame,
        frame,
        mode="full"
    )

    corr = corr[len(corr)//2:]

    max_corr = np.max(np.abs(corr))
    if max_corr == 0:
        return np.zeros_like(corr)
    corr /= max_corr

    return corr

def compute_frame_pitch(frame, sr):
    """
    Estimate fundamental frequency (F0)
    using Normalized Autocorrelation Function (NACF).

    Returns
    -------
    float
        Fundamental frequency (Hz)
        or np.nan for unvoiced frames.
    """
    min_lag = int(sr / PITCH_MAX)
    max_lag = int(sr / PITCH_MIN)

    corr = compute_autocorrelation(frame)

    search_area = corr[min_lag:max_lag]

    peaks, properties = find_peaks(search_area, prominence=PITCH_PROMINENCE)

    if len(peaks) == 0:
        return np.nan

    best_peak = peaks[
        np.argmax(properties["prominences"])
    ]
    peak_value = search_area[best_peak]

    if peak_value < PITCH_CORRELATION_THRESHOLD:
        return np.nan

    lag = best_peak + min_lag

    f0 = sr / lag

    return f0

def compute_pitch(audio, sr):

    frames = frame_audio(audio, sr)

    pitch = []

    for frame in frames:

        pitch.append(
            compute_frame_pitch(frame, sr)
        )

    pitch = np.asarray(pitch)

    if np.all(np.isnan(pitch)):
        return np.nan, pitch.tolist()

    return float(np.nanmedian(pitch)), pitch.tolist()
