"""12-segment audio level meter (low green / mid yellow / high red) — mockup parity."""

from PySide6.QtWidgets import QHBoxLayout, QLabel, QWidget

SEG_COLORS = ["#2ecc57"] * 4 + ["#d8a400"] * 4 + ["#c0392b"] * 4


class LevelMeter(QWidget):
    def __init__(self, segments: int = 12, parent=None):
        super().__init__(parent)
        self.setFixedHeight(14)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        self._segs: list[QLabel] = []
        for i in range(segments):
            seg = QLabel()
            seg.setFixedSize(14, 10)
            seg.setStyleSheet("background: #e0e0e0; border-radius: 1px;")
            layout.addWidget(seg)
            self._segs.append(seg)
        layout.addStretch()

    def set_level(self, level: float) -> None:
        """level 0.0–1.0."""
        active = int(max(0.0, min(1.0, level)) * len(self._segs))
        for i, seg in enumerate(self._segs):
            if i < active:
                seg.setStyleSheet(f"background: {SEG_COLORS[i]}; border-radius: 1px;")
            else:
                seg.setStyleSheet("background: #e0e0e0; border-radius: 1px;")
