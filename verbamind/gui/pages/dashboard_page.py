"""Dashboard — stat cards + recent sessions table. No dummy data — pulls from SessionManager."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
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

        # Stat cards — pulled from real session manager
        self._stat_sessions = StatCard("0", "Total Sesi")
        self._stat_patients = StatCard("0", "Total Pasien")
        self._stat_birp = StatCard("0", "BIRP Selesai")
        self._stat_pending = StatCard("0", "Menunggu Review")

        cards = QHBoxLayout()
        cards.setSpacing(12)
        cards.addWidget(self._stat_sessions)
        cards.addWidget(self._stat_patients)
        cards.addWidget(self._stat_birp)
        cards.addWidget(self._stat_pending)
        cards_widget = QWidget()
        cards_widget.setLayout(cards)

        # Search row
        search_row = QHBoxLayout()
        search_lbl = QLabel("Cari:")
        search_lbl.setObjectName("text_dim")
        search_input = QLineEdit()
        search_input.setPlaceholderText("Cari nama pasien atau ID sesi...")
        search_input.setFixedWidth(260)
        search_btn = QPushButton("Cari")
        search_btn.setObjectName("small_btn")
        new_btn = QPushButton("+ Sesi Baru")
        new_btn.setObjectName("primary_btn")
        new_btn.setStyleSheet("padding: 5px 12px; font-size: 12px;")
        search_row.addWidget(search_lbl)
        search_row.addWidget(search_input)
        search_row.addWidget(search_btn)
        search_row.addStretch()
        search_row.addWidget(new_btn)

        # Sessions table
        self._table = QTableWidget()
        self._table.setObjectName("session_list")
        self._table.setAlternatingRowColors(True)
        self._table.setColumnCount(5)
        self._table.setHorizontalHeaderLabels(["Tanggal", "Pasien", "ID Sesi", "Status BIRP", "Status Audio"])
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self._table.verticalHeader().setVisible(False)
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

        # Empty state label — no dummy data
        self._empty_label = QLabel("Belum ada sesi tersimpan. Klik \"+ Sesi Baru\" untuk memulai perekaman.")
        self._empty_label.setAlignment(Qt.AlignCenter)
        self._empty_label.setStyleSheet(
            "color: #5a5a5a; font-size: 12.5px; padding: 24px; background: #fafafa; "
            "border: 1px dashed #b1b1b1; border-radius: 2px;"
        )

        session_group = QGroupBox("Sesi Terbaru")
        session_layout = QVBoxLayout(session_group)
        session_layout.addLayout(search_row)
        session_layout.addWidget(self._empty_label)
        session_layout.addWidget(self._table)
        self._table.setVisible(False)

        layout.addWidget(title)
        layout.addWidget(cards_widget)
        layout.addWidget(session_group, 1)

    def load_sessions(self, sessions: list[dict]):
        """Load real sessions from SessionManager. Empty list → show empty state."""
        if not sessions:
            self._empty_label.setVisible(True)
            self._table.setVisible(False)
            self._table.setRowCount(0)
            self._stat_sessions.setProperty("text", "0")
            return

        self._empty_label.setVisible(False)
        self._table.setVisible(True)
        self._table.setRowCount(len(sessions))
        for i, s in enumerate(sessions):
            date = QTableWidgetItem(s.get("created_at", "")[:10])
            patient = QTableWidgetItem(s.get("patient_name", f"Patient #{s.get('patient_id', '?')}"))
            sid = QTableWidgetItem(s.get("session_id", ""))
            birp = QTableWidgetItem(s.get("birp_status", "—"))
            audio = QTableWidgetItem(s.get("audio_status", "Tersimpan"))
            self._table.setItem(i, 0, date)
            self._table.setItem(i, 1, patient)
            self._table.setItem(i, 2, sid)
            self._table.setItem(i, 3, birp)
            self._table.setItem(i, 4, audio)

        # Update stat cards
        self._stat_sessions.findChild(QLabel, "stat_number").setText(str(len(sessions)))
