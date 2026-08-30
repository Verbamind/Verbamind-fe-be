"""PDF export via QPdfWriter — transcript & BIRP reports."""

from PySide6.QtCore import QRectF
from PySide6.QtGui import QFont, QPageSize, QPainter, QPdfWriter, QPen

MARGIN = 56.0  # ~2cm


def _writer(path: str) -> tuple[QPdfWriter, QPainter]:
    writer = QPdfWriter(path)
    writer.setPageSize(QPageSize(QPageSize.A4))
    writer.setResolution(72)
    painter = QPainter(writer)
    return writer, painter


def _title_block(painter: QPainter, width: float, title: str, subtitle: str) -> float:
    y = MARGIN
    bold = QFont("Segoe UI", 14)
    bold.setBold(True)
    painter.setFont(bold)
    painter.drawText(QRectF(MARGIN, y, width - 2 * MARGIN, 30), 0, title)
    y += 34
    normal = QFont("Segoe UI", 9)
    painter.setFont(normal)
    painter.setPen(QPen("#5a5a5a"))
    painter.drawText(QRectF(MARGIN, y, width - 2 * MARGIN, 16), 0, subtitle)
    y += 24
    painter.setPen(QPen("#b1b1b1"))
    painter.drawLine(int(MARGIN), int(y), int(width - MARGIN), int(y))
    painter.setPen(QPen("#1a1a1a"))
    y += 14
    return y


def export_transcript_pdf(path: str, session: dict, segments: list[dict]) -> None:
    writer, painter = _writer(path)
    try:
        page_rect = writer.pageRect(0)
        width = float(page_rect.width())
        height = float(page_rect.height())
        y = _title_block(
            painter,
            width,
            "Transkrip Sesi Konseling",
            f"Pasien: {session.get('patient_name', '—')}   |   "
            f"Tanggal: {session.get('date', '—')}   |   Sesi: S-{session.get('id', 0):04d}",
        )
        header_font = QFont("Segoe UI", 9)
        header_font.setBold(True)
        body_font = QFont("Segoe UI", 9)
        row_h = 20.0

        for i, seg in enumerate(segments):
            if y + row_h * 2 > height - MARGIN:
                painter.end()
                if not writer.newPage():
                    break
                y = _title_block(
                    painter, width, "Transkrip Sesi Konseling (lanjutan)", ""
                )
            painter.setFont(header_font)
            speaker = str(seg.get("speaker", "—"))
            start = seg.get("start", "")
            painter.drawText(QRectF(MARGIN, y, width - 2 * MARGIN, row_h), 0, f"[{start}] {speaker}")
            y += row_h
            painter.setFont(body_font)
            text = str(seg.get("text", ""))
            lines = max(1, int(len(text) / 80) + 1)
            painter.drawText(
                QRectF(MARGIN + 14, y, width - 2 * MARGIN - 14, row_h * lines), 0, text
            )
            y += row_h * lines + 6
    finally:
        painter.end()


def export_birp_pdf(path: str, session: dict, birp: dict) -> None:
    writer, painter = _writer(path)
    try:
        page_rect = writer.pageRect(0)
        width = float(page_rect.width())
        y = _title_block(
            painter,
            width,
            "Ringkasan BIRP",
            f"Pasien: {session.get('patient_name', '—')}   |   "
            f"Tanggal: {session.get('date', '—')}   |   Sesi: S-{session.get('id', 0):04d}",
        )
        label_font = QFont("Segoe UI", 10)
        label_font.setBold(True)
        body_font = QFont("Segoe UI", 9)
        row_h = 18.0

        for key, label in [
            ("behavior", "B (Behavior)"),
            ("intervention", "I (Intervention)"),
            ("response", "R (Response)"),
            ("plan", "P (Plan)"),
        ]:
            painter.setFont(label_font)
            painter.drawText(QRectF(MARGIN, y, width - 2 * MARGIN, row_h), 0, label)
            y += row_h
            painter.setFont(body_font)
            text = str(birp.get(key, ""))
            lines = max(1, int(len(text) / 85) + 1)
            painter.drawText(
                QRectF(MARGIN + 14, y, width - 2 * MARGIN - 14, row_h * lines), 0, text
            )
            y += row_h * lines + 14
    finally:
        painter.end()
