"""Dashboard page — stat cards, patient table, search bar."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)


class StatCard(QWidget):
    def __init__(self, number: str, label: str, parent=None):
        super().__init__(parent)
        self.setStyleSheet(
            "QWidget { border: 1px solid #b1b1b1; background: #ffffff; "
            "border-radius: 2px; padding: 10px 12px; }"
        )
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(2)
        num = QLabel(number)
        num.setObjectName("stat_number")
        layout.addWidget(num)
        lbl = QLabel(label)
        lbl.setObjectName("stat_label")
        layout.addWidget(lbl)


class DashboardPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        title = QLabel("Dashboard")
        title.setObjectName("section_title")

        cards = QHBoxLayout()
        cards.setSpacing(12)
        cards.addWidget(StatCard("3", "Total Sessions"))
        cards.addWidget(StatCard("1", "Patients"))
        cards.addWidget(StatCard("2", "BIRP Reports"))
        cards.addWidget(StatCard("0", "Pending Review"))
        cards_widget = QWidget()
        cards_widget.setLayout(cards)

        search_row = QHBoxLayout()
        search_row.addWidget(QLabel("Search:"))
        search_input = QLineEdit()
        search_input.setPlaceholderText("Type patient name or session ID...")
        search_input.setFixedWidth(260)
        search_row.addWidget(search_input)
        search_row.addStretch()

        table = QTableWidget()
        table.setAlternatingRowColors(True)
        table.setColumnCount(5)
        table.setHorizontalHeaderLabels(["Date", "Patient", "Session ID", "Status", "BIRP"])
        table.horizontalHeader().setStretchLastSection(True)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table.verticalHeader().setVisible(False)
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.setRowCount(3)
        data = [
            ("12 Mar 2026", "Andi Pratama", "S001", "Completed", "✅"),
            ("10 Mar 2026", "Budi Santoso", "S002", "Draft", "—"),
            ("08 Mar 2026", "Citra Dewi", "S003", "Completed", "✅"),
        ]
        for r, (date, name, sid, status, birp) in enumerate(data):
            table.setItem(r, 0, QTableWidgetItem(date))
            table.setItem(r, 1, QTableWidgetItem(name))
            table.setItem(r, 2, QTableWidgetItem(sid))
            table.setItem(r, 3, QTableWidgetItem(status))
            table.setItem(r, 4, QTableWidgetItem(birp))

        session_group = QGroupBox("Recent Sessions")
        session_layout = QVBoxLayout(session_group)
        session_layout.addLayout(search_row)
        session_layout.addWidget(table)

        layout.addWidget(title)
        layout.addWidget(cards_widget)
        layout.addWidget(session_group, 1)
