"""Speaker labeler — maps audio channel index to speaker role (patient/psychologist).

Dual-channel recording: channel 0 = patient, channel 1 = psychologist.
"""

from typing import Any


class SpeakerLabeler:
    def __init__(self, patient_channel: int = 0, psychologist_channel: int = 1):
        self._mapping = {
            patient_channel: "patient",
            psychologist_channel: "psychologist",
        }

    def label(self, segments: list[dict[str, Any]]) -> list[dict[str, Any]]:
        labeled = []
        for seg in segments:
            labeled_seg = dict(seg)
            labeled_seg["speaker"] = self._mapping.get(
                seg.get("channel", -1), "unknown"
            )
            labeled.append(labeled_seg)
        return labeled
