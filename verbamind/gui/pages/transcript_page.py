"""Transcript page — table-based verbatim with emotion badges and timestamps."""

from PySide6.QtCore import Qt
from verbamind.gui.widgets.section_title import SectionTitle
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHeaderView,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

EMOTION_COLORS = {
    "sedih": "#3b6fb5",
    "marah": "#c0392b",
    "netral": "#8a8a8a",
    "senang": "#2e9e5b",
    "cemas": "#c8790b",
    "anxious": "#c8790b",
    "sad": "#3b6fb5",
    "angry": "#c0392b",
    "neutral": "#8a8a8a",
    "happy": "#2e9e5b",
    "calm": "#2e9e5b",
    "fearful": "#c8790b",
}


def _emotion_badge(emotion: str, confidence: float | None = None) -> str:
    emoji_map = {
        "sedih": "😢", "sad": "😢",
        "marah": "😠", "angry": "😠",
        "netral": "😐", "neutral": "😐",
        "senang": "😊", "happy": "😊", "calm": "😊",
        "cemas": "😰", "anxious": "😰", "fearful": "😰",
    }
    emoji = emoji_map.get(str(emotion).lower(), "")
    conf = f" {confidence:.0%}" if confidence else ""
    return f"{emoji} {emotion}{conf}"


class TranscriptPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        title = SectionTitle("Transcript & Verbatim")

        self._table = QTableWidget()
        self._table.setAlternatingRowColors(True)
        self._table.setColumnCount(5)
        self._table.setHorizontalHeaderLabels(["Time", "Speaker", "Text", "Emotion", "Physiological"])
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self._table.verticalHeader().setVisible(False)
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)

        self._segment_count = 0
        layout.addWidget(title)
        layout.addWidget(self._table, 1)

    def segment_count(self) -> int:
        return self._segment_count

    def load_transcript(self, segments: list[dict]) -> None:
        self._table.setRowCount(len(segments))
        self._segment_count = 0
        for i, seg in enumerate(segments):
            speaker = seg.get("speaker", "unknown").capitalize()
            text = seg.get("text", "")
            emotion = seg.get("emotion")
            confidence = seg.get("emotion_confidence")
            start = seg.get("start", 0.0)

            time_item = QTableWidgetItem(f"{start:.1f}s")
            speaker_item = QTableWidgetItem(speaker)
            text_item = QTableWidgetItem(text)

            if emotion:
                badge = _emotion_badge(str(emotion), confidence)
            else:
                badge = "—"
            emotion_item = QTableWidgetItem(badge)

            physio = "—"
            if emotion and confidence and confidence > 0.7:
                physio = "Detected"

            self._table.setItem(i, 0, time_item)
            self._table.setItem(i, 1, speaker_item)
            self._table.setItem(i, 2, text_item)
            self._table.setItem(i, 3, QTableWidgetItem(badge))
            self._table.setItem(i, 4, QTableWidgetItem(physio))
            self._segment_count += 1
