import numpy as np
import skfuzzy as fuzz

class ChangeFuzzyInference:

    def __init__(self):

        self.x = np.arange(-5, 5.01, 0.01)

        self.very_low = fuzz.trapmf(
            self.x,
            [-5, -5, -3, -2]
        )

        self.low = fuzz.trimf(
            self.x,
            [-3, -2, -1]
        )

        self.no_change = fuzz.trapmf(
            self.x,
            [-2, -1, 1, 2]
        )

        self.high = fuzz.trimf(
            self.x,
            [1, 2, 3]
        )

        self.very_high = fuzz.trapmf(
            self.x,
            [2, 3, 5, 5]
        )

    def infer(self, delta, deviation):

        normalized = delta / deviation

        very_low_degree = fuzz.interp_membership(
            self.x,
            self.very_low,
            normalized
        )

        low_degree = fuzz.interp_membership(
            self.x,
            self.low,
            normalized
        )

        no_change_degree = fuzz.interp_membership(
            self.x,
            self.no_change,
            normalized
        )

        high_degree = fuzz.interp_membership(
            self.x,
            self.high,
            normalized
        )

        very_high_degree = fuzz.interp_membership(
            self.x,
            self.very_high,
            normalized
        )

        memberships = {
            "Very Low": very_low_degree,
            "Low": low_degree,
            "No Significant Change": no_change_degree,
            "High": high_degree,
            "Very High": very_high_degree
        }

        return max(
            memberships,
            key=memberships.get
        )