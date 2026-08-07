"""Merged Verbatim engine — combines verbal (STT) and non-verbal (SER) data.

Produces enriched transcript segments with speaker labels, text, timestamps,
and emotional annotations. Output ready for LLM BIRP generation.
"""

from typing import Any


class MergeService:
    def merge(
        self,
        verbal: list[dict[str, Any]],
        non_verbal: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        sorted_verbal = sorted(verbal, key=lambda s: s.get("start", 0.0))
        merged = []
        for seg in sorted_verbal:
            best_emotion = self._best_emotion_for_segment(seg, non_verbal)
            merged.append({
                "speaker": seg.get("speaker", "unknown"),
                "text": seg.get("text", ""),
                "start": seg.get("start", 0.0),
                "end": seg.get("end", 0.0),
                "emotion": best_emotion["emotion"] if best_emotion else None,
                "emotion_confidence": best_emotion["confidence"] if best_emotion else None,
            })
        return merged

    def _best_emotion_for_segment(
        self,
        segment: dict[str, Any],
        ser_results: list[dict[str, Any]],
    ) -> dict[str, Any] | None:
        seg_start = segment.get("start", 0.0)
        seg_end = segment.get("end", 0.0)
        seg_mid = (seg_start + seg_end) / 2

        best = None
        best_conf = -1.0
        for ser in ser_results:
            s_start = ser.get("segment_start", 0.0)
            s_end = ser.get("segment_end", 0.0)
            if s_end > seg_start and s_start < seg_end:
                if ser.get("confidence", 0.0) > best_conf:
                    best = ser
                    best_conf = ser.get("confidence", 0.0)
        return best if best else None

    def to_verbatim_text(self, merged: list[dict[str, Any]]) -> str:
        lines = []
        for seg in merged:
            speaker = seg["speaker"].capitalize()
            text = seg["text"]
            emotion = seg.get("emotion")
            line = f"{speaker}: {text}"
            if emotion:
                line += f" [{emotion}]"
            lines.append(line)
        return "\n".join(lines)
