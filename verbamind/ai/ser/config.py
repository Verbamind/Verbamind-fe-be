"""
Global configuration for Nonverbal Cue Detection
"""

# ===========================
# Audio
# ===========================

SAMPLE_RATE = None          # keep original sample rate

FRAME_DURATION = 0.025        # seconds (25 ms)

FRAME_OVERLAP = 0.50        # 50%

# FRAME_LENGTH = int(FRAME_DURATION*SAMPLE_RATE)
# HOP_LENGTH = int(FRAME_LENGTH * (1 - FRAME_OVERLAP))

# ===========================
# Baseline
# ===========================

INITIAL_DURATION = 2.5      # in seconds

EMA_ALPHA = 0.05

EMA_BETA = 0.05

MIN_LOUDNESS_DEVIATION = 1e-3

# ===========================
# Loudness
# ===========================

LOUDNESS_METHOD = "median"

REFERENCE_PRESSURE = 20e-6  # 20 µPa

# ===========================
# Pitch
# ===========================

PITCH_MAX = 300

PITCH_MIN = 75

PITCH_CORRELATION_THRESHOLD = 0.3

PITCH_PROMINENCE = 0.5