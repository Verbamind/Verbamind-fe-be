"""Unicolor (monochrome) vector icons drawn with QPainter."""

import math

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPainterPath, QPen, QPixmap


def make_icon(kind: str, size: int = 16, color: str = "#1a1a1a") -> QIcon:
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)

    pen = QPen(QColor(color))
    pen.setWidthF(1.5)
    pen.setCapStyle(Qt.RoundCap)
    pen.setJoinStyle(Qt.RoundJoin)
    p.setPen(pen)
    p.setBrush(Qt.NoBrush)

    m = 2.5
    w = size - 2 * m
    cx = cy = size / 2

    if kind == "dashboard":
        gap = 2.0
        cell = (w - gap) / 2
        for r in range(2):
            for c in range(2):
                x = m + c * (cell + gap)
                y = m + r * (cell + gap)
                p.drawRoundedRect(QRectF(x, y, cell, cell), 1.5, 1.5)

    elif kind == "patients":
        p.drawEllipse(QPointF(cx, m + 3.0), 2.2, 2.2)
        body = QPainterPath()
        body.moveTo(m + 1.5, size - m)
        body.quadTo(cx, m + 7.0, size - m - 1.5, size - m)
        p.drawPath(body)

    elif kind == "record":
        p.setBrush(QColor(color))
        p.setPen(Qt.NoPen)
        p.drawEllipse(QPointF(cx, cy), 3.5, 3.5)

    elif kind == "audit":
        for y in (m + 2.0, cy, size - m - 2.0):
            p.drawLine(QPointF(m, y), QPointF(size - m, y))

    elif kind == "settings":
        p.drawEllipse(QPointF(cx, cy), 2.8, 2.8)
        for i in range(8):
            ang = i * math.pi / 4
            p.drawLine(
                QPointF(cx + math.cos(ang) * 4.0, cy + math.sin(ang) * 4.0),
                QPointF(cx + math.cos(ang) * 5.5, cy + math.sin(ang) * 5.5),
            )

    elif kind == "mic":
        p.drawRoundedRect(QRectF(cx - 2.2, m, 4.4, 5.5), 2.2, 2.2)
        p.drawArc(QRectF(cx - 3.2, m + 2.5, 6.4, 5.0), 0, 180 * 16)
        p.drawLine(QPointF(cx, m + 5.5), QPointF(cx, size - m - 1.5))
        p.drawLine(QPointF(cx - 2.5, size - m - 1.5), QPointF(cx + 2.5, size - m - 1.5))

    elif kind == "play":
        path = QPainterPath()
        path.moveTo(m + 1, m + 0.5)
        path.lineTo(size - m, cy)
        path.lineTo(m + 1, size - m - 0.5)
        path.closeSubpath()
        p.setBrush(QColor(color))
        p.setPen(Qt.NoPen)
        p.drawPath(path)

    elif kind == "pause":
        p.setBrush(QColor(color))
        p.setPen(Qt.NoPen)
        bar_w = 3.2
        p.drawRoundedRect(QRectF(m + 1, m, bar_w, w), 1, 1)
        p.drawRoundedRect(QRectF(size - m - 1 - bar_w, m, bar_w, w), 1, 1)

    elif kind == "stop":
        p.setBrush(QColor(color))
        p.setPen(Qt.NoPen)
        p.drawRoundedRect(QRectF(m + 1, m + 1, w - 2, w - 2), 1.5, 1.5)

    elif kind == "trash":
        p.drawLine(QPointF(m + 1.5, m + 2.0), QPointF(size - m - 1.5, m + 2.0))
        p.drawLine(QPointF(cx - 1.0, m), QPointF(cx + 1.0, m))
        p.drawRoundedRect(QRectF(m + 2.5, m + 3.5, w - 5.0, w - 3.5), 1.0, 1.0)
        p.drawLine(QPointF(cx - 1.5, m + 5.5), QPointF(cx - 1.5, size - m - 1.0))
        p.drawLine(QPointF(cx + 1.5, m + 5.5), QPointF(cx + 1.5, size - m - 1.0))

    p.end()
    return QIcon(pm)
