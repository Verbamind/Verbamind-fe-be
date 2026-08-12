import numpy as np

from verbamind.ai.ser.models.baseline import LoudnessBaseline


def initialize_baseline(loudness_values):
    """
    Initialize loudness baseline from the first
    INITIAL_DURATION of patient utterances.

    Parameters
    ----------
    loudness_values : list[float]

    Returns
    -------
    LoudnessBaseline
    """

    values = np.asarray(loudness_values, dtype=float)

    if len(values) == 0:
        raise ValueError("No loudness values provided.")

    baseline = np.nanmedian(values)

    deviation = np.nanmedian(np.abs(values - baseline))

    return LoudnessBaseline(
        baseline=float(baseline),
        deviation=float(deviation)
    )
