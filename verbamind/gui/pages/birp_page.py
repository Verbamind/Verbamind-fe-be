"""BIRP viewer page — 4-card layout for Behavior, Intervention, Response, Plan."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

BIRP_LABELS = {
    "behavior": "Behavior",
    "intervention": "Intervention",
    "response": "Response",
    "plan": "Plan",
}


class BIRPPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._has_data = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)

        title = QLabel("BIRP Summary")
        title.setObjectName("section_title")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #1a1a1a;")

        self._cards_layout = QVBoxLayout()
        cards_widget = QWidget()
        cards_widget.setLayout(self._cards_layout)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(cards_widget)
        scroll.setStyleSheet("QScrollArea { border: none; background: #ffffff; }")

        self._pending_label = QLabel("No BIRP data generated yet. Complete a recording and run the AI pipeline.")
        self._pending_label.setWordWrap(True)
        self._pending_label.setStyleSheet("color: #5a5a5a; font-size: 13px; padding: 20px;")
        self._cards_layout.addWidget(self._pending_label)

        layout.addWidget(title)
        layout.addSpacing(8)
        layout.addWidget(scroll, 1)

    def has_data(self) -> bool:
        return self._has_data

    def load_birp(self, data: dict) -> None:
        for i in reversed(range(self._cards_layout.count())):
            w = self._cards_layout.itemAt(i).widget()
            if w:
                w.setParent(None)

        self._has_data = True
        for key in ("behavior", "intervention", "response", "plan"):
            label = BIRP_LABELS.get(key, key.capitalize())
            value = data.get(key, "—")
            card = self._create_card(label, value)
            card.setObjectName("birp_card")
            self._cards_layout.addWidget(card)
        self._cards_layout.addStretch()

    def _create_card(self, title: str, content: str) -> QFrame:
        card = QFrame()
        card.setStyleSheet(
            "QFrame { background: #ffffff; border: 1px solid #b1b1b1; "
            "border-radius: 6px; padding: 12px; margin: 4px 0; }"
        )
        card_layout = QVBoxLayout(card)

        header = QLabel(title)
        header.setStyleSheet(
            "font-size: 14px; font-weight: bold; color: #0a5fc4; border: none; padding-bottom: 4px;"
        )
        body = QLabel(content)
        body.setWordWrap(True)
        body.setStyleSheet("font-size: 13px; color: #1a1a1a; border: none;")

        card_layout.addWidget(header)
        card_layout.addWidget(body)
        return card
