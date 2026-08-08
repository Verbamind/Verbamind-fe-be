"""Audit Log page — table of system actions with date filter. Empty by default."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)
from PySide6.QtWidgets import QAbstractItemView


class AuditLogPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        title = QLabel("Audit Log")
        title.setObjectName("section_title")

        filter_row = QHBoxLayout()
        action_combo = QComboBox()
        action_combo.addItems(["Semua Aksi", "Login", "Buat Sesi", "Edit", "Delete", "Logout"])
        from_lbl = QLabel("Dari:")
        from_lbl.setObjectName("text_dim")
        from_date = QDateEdit()
        from_date.setCalendarPopup(True)
        to_lbl = QLabel("Sampai:")
        to_lbl.setObjectName("text_dim")
        to_date = QDateEdit()
        to_date.setCalendarPopup(True)
        to_date.setDateTime(to_date.dateTime().currentDateTime())
        filter_btn = QPushButton("Filter")
        filter_btn.setObjectName("small_btn")

        filter_row.addWidget(action_combo)
        filter_row.addWidget(from_lbl)
        filter_row.addWidget(from_date)
        filter_row.addWidget(to_lbl)
        filter_row.addWidget(to_date)
        filter_row.addWidget(filter_btn)
        filter_row.addStretch()

        self._table = QTableWidget()
        self._table.setAlternatingRowColors(True)
        self._table.setColumnCount(4)
        self._table.setHorizontalHeaderLabels(["Timestamp", "Aksi", "Detail", "ID Sesi / Pasien"])
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self._table.verticalHeader().setVisible(False)
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.setRowCount(0)

        self._empty_label = QLabel("Belum ada aktivitas tercatat.")
        self._empty_label.setAlignment(Qt.AlignCenter)
        self._empty_label.setStyleSheet(
            "color: #5a5a5a; font-size: 12.5px; padding: 24px; background: #fafafa; "
            "border: 1px dashed #b1b1b1; border-radius: 2px;"
        )

        layout.addWidget(title)
        layout.addLayout(filter_row)
        layout.addWidget(self._empty_label)
        layout.addWidget(self._table)
        self._table.setVisible(False)
        layout.addStretch()

    def load_logs(self, logs: list[dict]):
        if not logs:
            self._empty_label.setVisible(True)
            self._table.setVisible(False)
            return
        self._empty_label.setVisible(False)
        self._table.setVisible(True)
        self._table.setRowCount(len(logs))
        for i, log in enumerate(logs):
            self._table.setItem(i, 0, QTableWidgetItem(log.get("timestamp", "")))
            self._table.setItem(i, 1, QTableWidgetItem(log.get("action", "")))
            self._table.setItem(i, 2, QTableWidgetItem(log.get("details", "")))
            self._table.setItem(i, 3, QTableWidgetItem(log.get("ref_id", "—")))
