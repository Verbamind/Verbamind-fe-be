"""Dashboard — live stat cards + recent sessions table (searchable, clickable)."""

from PySide6.QtCore import Qt, Signal
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

from verbamind.gui.widgets.section_title import SectionTitle


def _fmt_duration(seconds: int) -> str:
    if seconds <= 0:
        return "—"
    m = seconds // 60
    s = seconds % 60
    if m > 0:
        return f"{m}m {s}s" if s else f"{m} menit"
    return f"{s} dtk"


class StatCard(QWidget):
    def __init__(self, number: str, label: str, parent=None):
        super().__init__(parent)
        self.setObjectName("stat_card")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(2)
        num = QLabel(number)
        num.setObjectName("stat_number")
        layout.addWidget(num)
        lbl = QLabel(label)
        lbl.setObjectName("stat_label")
        layout.addWidget(lbl)

    def set_value(self, value: str) -> None:
        self.findChild(QLabel, "stat_number").setText(value)


class DashboardPage(QWidget):

    new_session_requested = Signal()
    view_session_requested = Signal(int)  # session_id

    def __init__(self, parent=None):
        super().__init__(parent)
        self._sessions: list[dict] = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        title = SectionTitle("Dashboard")

        # Stat cards — mockup parity
        self._stat_patients = StatCard("0", "Total Pasien")
        self._stat_month = StatCard("0", "Sesi Bulan Ini")
        self._stat_birp = StatCard("0", "BIRP Belum Direview")
        self._stat_audio = StatCard("0", "Audio Menunggu Keputusan Hapus")

        cards = QHBoxLayout()
        cards.setSpacing(12)
        cards.addWidget(self._stat_patients)
        cards.addWidget(self._stat_month)
        cards.addWidget(self._stat_birp)
        cards.addWidget(self._stat_audio)
        cards_widget = QWidget()
        cards_widget.setLayout(cards)

        # Search row
        search_row = QHBoxLayout()
        search_lbl = QLabel("Cari:")
        search_lbl.setObjectName("text_dim")
        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("Cari nama pasien atau ID sesi...")
        self._search_input.setFixedWidth(260)
        self._search_input.textChanged.connect(lambda _: self._apply_filter())
        search_btn = QPushButton("Cari")
        search_btn.setObjectName("small_btn")
        search_btn.clicked.connect(self._apply_filter)
        new_btn = QPushButton("+ Sesi Baru")
        new_btn.setObjectName("primary_btn")
        new_btn.setStyleSheet("padding: 5px 12px; font-size: 12px;")
        new_btn.clicked.connect(self.new_session_requested.emit)
        search_row.addWidget(search_lbl)
        search_row.addWidget(self._search_input)
        search_row.addWidget(search_btn)
        search_row.addStretch()
        search_row.addWidget(new_btn)

        # Sessions table
        self._table = QTableWidget()
        self._table.setObjectName("session_list")
        self._table.setAlternatingRowColors(True)
        self._table.setColumnCount(5)
        self._table.setHorizontalHeaderLabels(
            ["Tanggal", "Pasien", "Durasi", "Status BIRP", "Status Audio"]
        )
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self._table.verticalHeader().setVisible(False)
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.cellDoubleClicked.connect(self._on_row_activated)

        # Empty state label
        self._empty_label = QLabel(
            'Belum ada sesi tersimpan. Klik "+ Sesi Baru" untuk memulai perekaman.'
        )
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

    def load_dashboard(self, stats: dict, recent_sessions: list[dict]):
        """Load live stats + recent sessions from the backend."""
        self._stat_patients.set_value(str(stats.get("total_patients", 0)))
        self._stat_month.set_value(str(stats.get("sessions_this_month", 0)))
        self._stat_birp.set_value(str(stats.get("birp_pending", 0)))
        self._stat_audio.set_value(str(stats.get("audio_pending", 0)))

        self._sessions = list(recent_sessions)
        self._apply_filter()

    def load_sessions(self, sessions: list[dict]):
        """Legacy: load sessions only (stats untouched)."""
        self.load_dashboard({}, sessions)

    def _apply_filter(self):
        text = (self._search_input.text() or "").lower()
        sessions = [
            s for s in self._sessions
            if text in str(s.get("patient_name", "")).lower()
            or text in f"S-{s.get('id', 0):04d}"
        ]

        if not sessions:
            self._empty_label.setVisible(True)
            self._table.setVisible(False)
            self._table.setRowCount(0)
            return

        self._empty_label.setVisible(False)
        self._table.setVisible(True)
        self._table.setRowCount(len(sessions))
        for i, s in enumerate(sessions):
            date_item = QTableWidgetItem(s.get("date", "—"))
            date_item.setData(Qt.UserRole, s.get("id"))
            self._table.setItem(i, 0, date_item)
            self._table.setItem(i, 1, QTableWidgetItem(s.get("patient_name", "—")))
            self._table.setItem(
                i, 2, QTableWidgetItem(_fmt_duration(s.get("duration_seconds", 0)))
            )
            self._table.setItem(i, 3, QTableWidgetItem(s.get("birp_status", "Belum")))
            self._table.setItem(i, 4, QTableWidgetItem(s.get("audio_status", "Tersimpan")))

    def _on_row_activated(self, row: int, _col: int):
        item = self._table.item(row, 0)
        if item is not None and item.data(Qt.UserRole) is not None:
            self.view_session_requested.emit(int(item.data(Qt.UserRole)))
