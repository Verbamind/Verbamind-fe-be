"""BIRP page — editable fields with labels (Behavior, Intervention, Response, Plan)."""

from PySide6.QtCore import Qt
from verbamind.gui.widgets.section_title import SectionTitle
from PySide6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

BIRP_FIELDS = [
    ("behavior", "Behavior", "Patient's observable behavior and presentation during session."),
    ("intervention", "Intervention", "Therapeutic techniques and approaches applied."),
    ("response", "Response", "Patient's response to the intervention."),
    ("plan", "Plan", "Follow-up plan and recommendations."),
]


class BIRPPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        header = QHBoxLayout()
        title = SectionTitle("BIRP Clinical Summary")
        self._status_label = QLabel("")
        self._status_label.setStyleSheet(
            "font-size: 11px; font-weight: 600; padding: 3px 10px; "
            "border-radius: 9px; color: #ffffff;"
        )
        header.addWidget(title, 1)
        header.addWidget(self._status_label)

        self._fields: dict[str, QTextEdit] = {}
        self._has_data = False

        cards_layout = QVBoxLayout()
        cards_layout.setSpacing(8)

        for key, label, hint in BIRP_FIELDS:
            group = QGroupBox(label)
            group_layout = QVBoxLayout(group)
            group_layout.setContentsMargins(10, 8, 10, 10)
            editor = QTextEdit()
            editor.setPlaceholderText(hint)
            editor.setMinimumHeight(100)
            editor.setObjectName(f"birp_{key}")
            group_layout.addWidget(editor)
            self._fields[key] = editor
            cards_layout.addWidget(group)

        buttons = QHBoxLayout()
        buttons.setSpacing(8)
        save_btn = QPushButton("Save")
        save_btn.setObjectName("primary_btn")
        export_btn = QPushButton("Export PDF")
        buttons.addWidget(save_btn)
        buttons.addWidget(export_btn)
        buttons.addStretch()

        layout.addLayout(header)
        layout.addLayout(cards_layout, 1)
        layout.addLayout(buttons)

    def has_data(self) -> bool:
        return self._has_data

    def load_birp(self, data: dict) -> None:
        for key, editor in self._fields.items():
            value = data.get(key, "")
            editor.setPlainText(str(value) if value else "")
        self._has_data = bool(any(data.get(k) for k in self._fields))
        self._update_status()

    def _update_status(self):
        if self._has_data:
            self._status_label.setText("✅ Generated")
            self._status_label.setStyleSheet(
                "font-size: 11px; font-weight: 600; padding: 3px 10px; border-radius: 9px; "
                "background: #2e9e5b; color: #ffffff;"
            )
        else:
            self._status_label.setText("⏳ Pending")
            self._status_label.setStyleSheet(
                "font-size: 11px; font-weight: 600; padding: 3px 10px; border-radius: 9px; "
                "background: #c8790b; color: #ffffff;"
            )
