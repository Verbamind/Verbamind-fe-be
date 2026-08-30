from verbamind.ai.speech_to_nonverbal.config import (
    EMA_ALPHA,
    EMA_BETA,
    MIN_LOUDNESS_DEVIATION,
)
from verbamind.ai.speech_to_nonverbal.models.baseline import LoudnessBaseline


def update_baseline(
    baseline: LoudnessBaseline,
    current_loudness: float
):
    """
    Update adaptive loudness baseline using EMA.
    """

    delta = current_loudness - baseline.baseline

    new_baseline = (
        EMA_ALPHA * current_loudness +
        (1 - EMA_ALPHA) * baseline.baseline
    )

    new_deviation = (
        EMA_BETA * abs(delta) +
        (1 - EMA_BETA) * baseline.deviation
    )

    new_deviation = max(
        new_deviation,
        MIN_LOUDNESS_DEVIATION
    )

    updated = LoudnessBaseline(
        baseline=float(new_baseline),
        deviation=float(new_deviation)
    )

    return updated
