"""Transcript viewer page — scrollable segments with speaker labels and emotions."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QGroupBox,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)


class TranscriptPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)

        title = QLabel("Transcript")
        title.setObjectName("section_title")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #1a1a1a;")

        self._segments_layout = QVBoxLayout()
        self._segments_container = QWidget()
        self._segments_container.setLayout(self._segments_layout)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self._segments_container)
        scroll.setStyleSheet("QScrollArea { border: none; background: #ffffff; }")

        self._segment_count = 0

        layout.addWidget(title)
        layout.addSpacing(8)
        layout.addWidget(scroll, 1)

    def segment_count(self) -> int:
        return self._segment_count

    def load_transcript(self, segments: list[dict]) -> None:
        for i in reversed(range(self._segments_layout.count())):
            w = self._segments_layout.itemAt(i).widget()
            if w:
                w.setParent(None)
        self._segment_count = 0

        for seg in segments:
            self._add_segment(seg)
            self._segment_count += 1

    def _add_segment(self, seg: dict) -> None:
        speaker = seg.get("speaker", "unknown").capitalize()
        text = seg.get("text", "")
        emotion = seg.get("emotion")
        confidence = seg.get("emotion_confidence")
        start = seg.get("start", 0.0)
        end = seg.get("end", 0.0)

        seg_text = f"[{start:.1f}s - {end:.1f}s] {speaker}: {text}"
        if emotion:
            seg_text += f"  [{emotion} ({confidence:.0%})]" if confidence else f"  [{emotion}]"

        label = QLabel(seg_text)
        label.setWordWrap(True)
        label.setStyleSheet(
            "background: #ffffff; border: 1px solid #e0e0e0; border-radius: 4px; "
            "padding: 8px 12px; margin: 2px 0; font-size: 13px;"
        )
        self._segments_layout.addWidget(label)
        self._segments_layout.addStretch()
