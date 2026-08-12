"""Merged Verbatim engine — combines verbal (STT) and non-verbal data.

Produces enriched transcript segments with speaker labels, text, timestamps,
and nonverbal annotations. Output ready for LLM BIRP generation.
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
            best_nv = self._best_nonverbal_for_segment(seg, non_verbal)
            merged.append({
                "speaker": seg.get("speaker", "unknown"),
                "text": seg.get("text", ""),
                "start": seg.get("start", 0.0),
                "end": seg.get("end", 0.0),
                "emotion": best_nv["emotion"] if best_nv else None,
                "emotion_confidence": best_nv["confidence"] if best_nv else None,
            })
        return merged

    def _best_nonverbal_for_segment(
        self,
        segment: dict[str, Any],
        nonverbal_results: list[dict[str, Any]],
    ) -> dict[str, Any] | None:
        seg_start = segment.get("start", 0.0)
        seg_end = segment.get("end", 0.0)

        best = None
        best_conf = -1.0
        for nv in nonverbal_results:
            s_start = nv.get("segment_start", 0.0)
            s_end = nv.get("segment_end", 0.0)
            if s_end > seg_start and s_start < seg_end:
                if nv.get("confidence", 0.0) > best_conf:
                    best = nv
                    best_conf = nv.get("confidence", 0.0)
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
