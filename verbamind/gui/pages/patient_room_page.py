"""Patient room page — info pasien readonly + riwayat sesi verbatim (mockup parity)."""

from PySide6.QtCore import Signal
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
    return f"{m} menit" if m > 0 else f"{seconds} dtk"


class PatientRoomPage(QWidget):

    back_requested = Signal()
    new_session_for_patient = Signal(int)  # patient_id
    view_session_requested = Signal(int)  # session_id

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        header = QHBoxLayout()
        back_btn = QPushButton("← Kembali")
        back_btn.setObjectName("small_btn")
        back_btn.clicked.connect(self.back_requested.emit)
        self._title = SectionTitle("Detail Pasien")
        header.addWidget(back_btn)
        header.addWidget(self._title, 1)
        layout.addLayout(header)

        # ---- Informasi Pasien ----
        info_group = QGroupBox("Informasi Pasien")
        info_layout = QHBoxLayout(info_group)
        info_layout.setSpacing(14)
        self._fields: dict[str, QLineEdit] = {}
        for key, label in [
            ("id", "ID Pasien"),
            ("name", "Nama"),
            ("medical_record", "No. Rekam Medis"),
            ("session_count", "Total Sesi"),
        ]:
            col = QVBoxLayout()
            lbl = QLabel(label)
            lbl.setStyleSheet("font-size: 11.5px; color: #5a5a5a;")
            edit = QLineEdit("—")
            edit.setReadOnly(True)
            col.addWidget(lbl)
            col.addWidget(edit)
            self._fields[key] = edit
            info_layout.addLayout(col, 1)
        layout.addWidget(info_group)

        # ---- Riwayat Sesi Verbatim ----
        history_group = QGroupBox("Riwayat Sesi Verbatim")
        history_layout = QVBoxLayout(history_group)

        search_row = QHBoxLayout()
        self._search = QLineEdit()
        self._search.setPlaceholderText("Cari sesi berdasarkan tanggal...")
        self._search.setFixedWidth(240)
        self._search.textChanged.connect(self._apply_filter)
        new_btn = QPushButton("+ Sesi Baru untuk Pasien Ini")
        new_btn.setObjectName("primary_btn")
        new_btn.setStyleSheet("padding: 5px 12px; font-size: 12px;")
        new_btn.clicked.connect(lambda: self.new_session_for_patient.emit(self._patient_id))
        search_row.addWidget(self._search)
        search_row.addStretch()
        search_row.addWidget(new_btn)
        history_layout.addLayout(search_row)

        self._table = QTableWidget()
        self._table.setColumnCount(6)
        self._table.setHorizontalHeaderLabels(
            ["ID Sesi", "Tanggal", "Durasi", "Status BIRP", "Status Audio", "Aksi"]
        )
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self._table.verticalHeader().setVisible(False)
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        history_layout.addWidget(self._table)

        layout.addWidget(history_group, 1)

        self._patient_id: int | None = None
        self._sessions: list[dict] = []

    def load_patient(self, patient: dict, sessions: list[dict]) -> None:
        self._patient_id = patient.get("id")
        self._sessions = sessions
        self._title.set_text(
            f"Detail Pasien — {patient.get('name', '—')} (P-{patient.get('id', '?'):03d})"
        )
        self._fields["id"].setText(f"P-{patient.get('id', 0):03d}")
        self._fields["name"].setText(patient.get("name", "—"))
        self._fields["medical_record"].setText(patient.get("medical_record", "—"))
        self._fields["session_count"].setText(str(patient.get("session_count", "—")))
        self._apply_filter(self._search.text())

    def _apply_filter(self, text: str):
        text = (text or "").lower()
        rows = [s for s in self._sessions if text in str(s.get("date", "")).lower()]
        self._table.setRowCount(len(rows))
        for i, s in enumerate(rows):
            self._table.setItem(i, 0, QTableWidgetItem(f"S-{s['id']:04d}"))
            self._table.setItem(i, 1, QTableWidgetItem(s.get("date", "—")))
            self._table.setItem(
                i, 2, QTableWidgetItem(_fmt_duration(s.get("duration_seconds", 0)))
            )
            self._table.setItem(i, 3, QTableWidgetItem(s.get("birp_status", "Belum")))
            self._table.setItem(i, 4, QTableWidgetItem(s.get("audio_status", "—")))
            view_btn = QPushButton("Lihat")
            view_btn.setObjectName("small_btn")
            view_btn.setMinimumHeight(24)
            session_id = s["id"]
            view_btn.clicked.connect(
                lambda _=False, sid=session_id: self.view_session_requested.emit(sid)
            )

            cell = QWidget()
            cell_layout = QHBoxLayout(cell)
            cell_layout.setContentsMargins(2, 2, 2, 2)
            cell_layout.addStretch()
            cell_layout.addWidget(view_btn)
            cell_layout.addStretch()
            self._table.setCellWidget(i, 5, cell)
            self._table.setRowHeight(i, 36)
