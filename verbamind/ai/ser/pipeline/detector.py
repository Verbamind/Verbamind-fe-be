import numpy as np
import pandas as pd

from verbamind.ai.ser.baseline.initialization import initialize_baseline
from verbamind.ai.ser.baseline.adaptive import update_baseline
from verbamind.ai.ser.fuzzy.inference import ChangeFuzzyInference

class NonverbalChangeDetector:

    def __init__(self, initial_duration_frames):
        self.initial_duration_frames = initial_duration_frames
        self.fuzzy_engine = ChangeFuzzyInference()

    def detect(
        self,
        loudness_values,
        pitch_values
    ):
        """
        Detect loudness and pitch changes
        using adaptive baseline and fuzzy inference.
        """

        loudness_values = np.asarray(loudness_values)
        pitch_values = np.asarray(pitch_values)

        loudness_baseline = initialize_baseline(
            loudness_values[
                :self.initial_duration_frames
            ]
        )

        pitch_baseline = initialize_baseline(
            pitch_values[
                :self.initial_duration_frames
            ]
        )

        loudness_results = []
        pitch_results = []

        for i in range(
            self.initial_duration_frames,
            len(loudness_values)
        ):

            current_loudness = loudness_values[i]

            delta_loudness = (
                current_loudness
                - loudness_baseline.baseline
            )

            current_loudness_deviation = (
                loudness_baseline.deviation
            )

            if (
                abs(delta_loudness)
                <= current_loudness_deviation
            ):

                loudness_category = (
                    "No Significant Change"
                )

            else:

                loudness_category = (
                    self.fuzzy_engine.infer(
                        delta_loudness,
                        current_loudness_deviation
                    )
                )

            loudness_results.append([
                i,
                current_loudness,
                loudness_baseline.baseline,
                delta_loudness,
                current_loudness_deviation,
                loudness_category
            ])

            current_pitch = pitch_values[i]

            if np.isnan(current_pitch):

                pitch_results.append([
                    i,
                    np.nan,
                    pitch_baseline.baseline,
                    np.nan,
                    pitch_baseline.deviation,
                    "Unvoiced"
                ])

            else:

                delta_pitch = (
                    current_pitch
                    - pitch_baseline.baseline
                )

                current_pitch_deviation = (
                    pitch_baseline.deviation
                )

                if (
                    abs(delta_pitch)
                    <= current_pitch_deviation
                ):

                    pitch_category = (
                        "No Significant Change"
                    )

                else:

                    pitch_category = (
                        self.fuzzy_engine.infer(
                            delta_pitch,
                            current_pitch_deviation
                        )
                    )

                pitch_results.append([
                    i,
                    current_pitch,
                    pitch_baseline.baseline,
                    delta_pitch,
                    current_pitch_deviation,
                    pitch_category
                ])

            loudness_baseline = update_baseline(
                loudness_baseline,
                current_loudness
            )

            if not np.isnan(current_pitch):

                pitch_baseline = update_baseline(
                    pitch_baseline,
                    current_pitch
                )

        loudness_df = pd.DataFrame(
            loudness_results,
            columns=[
                "Frame",
                "Current_Loudness",
                "Baseline_Loudness",
                "Delta_Loudness",
                "Baseline_Loudness_Deviation",
                "Loudness_Category"
            ]
        )

        pitch_df = pd.DataFrame(
            pitch_results,
            columns=[
                "Frame",
                "Current_Pitch",
                "Baseline_Pitch",
                "Delta_Pitch",
                "Baseline_Pitch_Deviation",
                "Pitch_Category"
            ]
        )

        return loudness_df, pitch_df
