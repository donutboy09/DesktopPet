from __future__ import annotations

import math

from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QBrush, QColor, QFont, QPainterPath, QPen

PALETTES = {
    "cat": {
        "body": "#F5A623",
        "body_dark": "#E08A0F",
        "belly": "#FFE9CC",
        "ear_inner": "#FFC2D6",
        "nose": "#FF7BAC",
        "eye": "#3A2A1A",
        "blush": "#FFB3C6",
        "outline": "#B96B08",
    },
    "dog": {
        "body": "#C98A4B",
        "body_dark": "#A96B32",
        "belly": "#F4DCBC",
        "ear_inner": "#E0A06A",
        "nose": "#4A3220",
        "eye": "#2E2014",
        "blush": "#E8A88A",
        "outline": "#8A5320",
    },
}


def _c(hex_str: str, alpha: int = 255) -> QColor:
    color = QColor(hex_str)
    color.setAlpha(alpha)
    return color


def _pen(color: QColor, width: float) -> QPen:
    pen = QPen(color)
    pen.setWidthF(width)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    return pen


def _ellipse(painter, cx, cy, rx, ry, fill, outline, width=2.5):
    painter.setPen(_pen(outline, width) if outline else Qt.PenStyle.NoPen)
    painter.setBrush(QBrush(fill))
    painter.drawEllipse(QPointF(cx, cy), rx, ry)


def _tri(painter, pts, fill, outline, width=2.5):
    path = QPainterPath()
    path.moveTo(*pts[0])
    path.lineTo(*pts[1])
    path.lineTo(*pts[2])
    path.closeSubpath()
    painter.setPen(_pen(outline, width) if outline else Qt.PenStyle.NoPen)
    painter.setBrush(QBrush(fill))
    painter.drawPath(path)


def draw_pet(painter, rect, species, palette, state, t, facing, blink, walk_phase):
    scale = min(rect.width(), rect.height()) / 180.0
    painter.save()
    painter.translate(rect.left(), rect.top())
    painter.scale(scale, scale)

    painter.translate(90, 0)
    painter.scale(facing, 1)
    painter.translate(-90, 0)

    body = _c(palette["body"])
    body_dark = _c(palette["body_dark"])
    belly = _c(palette["belly"])
    ear_inner = _c(palette["ear_inner"])
    nose = _c(palette["nose"])
    eye = _c(palette["eye"])
    blush = _c(palette["blush"])
    outline = _c(palette["outline"])

    sleeping = state == "sleep"
    walking = state == "walk"
    happy = state == "happy"
    dragging = state == "drag"

    speed = 1.6 if sleeping else 3.0
    bob = math.sin(t * speed) * (1.2 if sleeping else 2.2)
    if happy:
        bob = -abs(math.sin(t * 9.0)) * 8.0
    if dragging:
        bob = math.sin(t * 6.0) * 1.5

    tail_wag = math.sin(t * (10.0 if walking or happy else 2.5)) * (0.5 if walking or happy else 0.22)
    head_tilt = math.sin(t * 1.4) * 2.0 if not walking else math.sin(t * 4) * 1.5

    _draw_tail(painter, species, body, body_dark, outline, tail_wag, sleeping)

    leg_swing = math.sin(walk_phase) * 5.0 if walking else 0.0
    _ellipse(painter, 70, 150 + leg_swing, 13, 9, body, outline)
    _ellipse(painter, 110, 150 - leg_swing, 13, 9, body, outline)

    _ellipse(painter, 90, 126 + bob, 42, 36, body, outline)
    _ellipse(painter, 90, 136 + bob, 25, 21, belly, None)

    head_y = 76 + bob * 1.15
    _draw_ears(painter, species, body, body_dark, ear_inner, outline, head_y, tail_wag, sleeping)

    _ellipse(painter, 90, head_y, 35, 31, body, outline)

    if species == "cat":
        _draw_whiskers(painter, outline, head_y)
        _draw_muzzle(painter, nose, outline, head_y, cat=True)
    else:
        _draw_muzzle(painter, nose, outline, head_y, cat=False)

    _draw_eyes(painter, eye, head_y, blink, sleeping, happy)

    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QBrush(blush))
    painter.drawEllipse(QPointF(66, head_y + 12), 6, 4)
    painter.drawEllipse(QPointF(114, head_y + 12), 6, 4)

    painter.restore()

    if sleeping:
        _draw_zzz(painter, rect, scale, t)
    if happy:
        _draw_hearts(painter, rect, scale, t)


def _draw_tail(painter, species, body, body_dark, outline, wag, sleeping):
    painter.setPen(_pen(outline, 3.0))
    painter.setBrush(Qt.BrushStyle.NoBrush)
    path = QPainterPath()
    if species == "cat":
        start = QPointF(128, 132)
        ctrl = QPointF(168 + wag * 20, 96 - wag * 12)
        end = QPointF(150 + wag * 30, 66)
        path.moveTo(start)
        path.quadTo(ctrl, end)
        pen = _pen(body_dark, 11.0)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.drawPath(path)
        painter.setPen(_pen(outline, 2.0))
        painter.drawPath(path)
    else:
        start = QPointF(126, 128)
        ctrl = QPointF(158 + wag * 14, 116 - wag * 8)
        end = QPointF(150 + wag * 20, 96)
        path.moveTo(start)
        path.quadTo(ctrl, end)
        pen = _pen(body_dark, 12.0)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.drawPath(path)
        painter.setPen(_pen(outline, 2.0))
        painter.drawPath(path)


def _draw_ears(painter, species, body, body_dark, ear_inner, outline, head_y, wag, sleeping):
    top = head_y - 30
    if species == "cat":
        _tri(painter, [(64, top + 12), (58, top - 22), (84, top + 2)], body, outline)
        _tri(painter, [(116, top + 12), (122, top - 22), (96, top + 2)], body, outline)
        _tri(painter, [(68, top + 8), (64, top - 12), (80, top + 2)], ear_inner, None, 0)
        _tri(painter, [(112, top + 8), (116, top - 12), (100, top + 2)], ear_inner, None, 0)
    else:
        painter.save()
        painter.translate(60, top + 4)
        painter.rotate(-28)
        _ellipse(painter, 0, 18, 12, 24, body_dark, outline)
        painter.restore()
        painter.save()
        painter.translate(120, top + 4)
        painter.rotate(28)
        _ellipse(painter, 0, 18, 12, 24, body_dark, outline)
        painter.restore()


def _draw_whiskers(painter, outline, head_y):
    painter.setPen(_pen(outline, 1.6))
    for dy, length in ((-2, 20), (4, 22), (10, 20)):
        painter.drawLine(QPointF(60, head_y + dy), QPointF(60 - length, head_y + dy - 4))
        painter.drawLine(QPointF(120, head_y + dy), QPointF(120 + length, head_y + dy - 4))


def _draw_muzzle(painter, nose, outline, head_y, cat):
    painter.setPen(_pen(nose.darker(140), 1.6))
    painter.setBrush(QBrush(nose))
    if cat:
        _tri(painter, [(86, head_y + 8), (94, head_y + 8), (90, head_y + 13)], nose, None, 0)
    else:
        painter.drawEllipse(QPointF(90, head_y + 10), 6, 5)
    painter.setPen(_pen(outline, 2.0))
    painter.setBrush(Qt.BrushStyle.NoBrush)
    mouth = QPainterPath()
    mouth.moveTo(90, head_y + (13 if cat else 15))
    mouth.quadTo(84, head_y + 20, 79, head_y + 14)
    mouth.moveTo(90, head_y + (13 if cat else 15))
    mouth.quadTo(96, head_y + 20, 101, head_y + 14)
    painter.drawPath(mouth)
    if not cat:
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor("#FF6B8A")))
        painter.drawEllipse(QPointF(90, head_y + 24), 6, 5)


def _draw_eyes(painter, eye, head_y, blink, sleeping, happy):
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QBrush(eye))
    for cx in (76, 104):
        if sleeping:
            pen = _pen(eye, 2.6)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            path = QPainterPath()
            path.moveTo(cx - 7, head_y - 1)
            path.quadTo(cx, head_y + 5, cx + 7, head_y - 1)
            painter.drawPath(path)
        elif blink > 0.5:
            pen = _pen(eye, 2.6)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawLine(QPointF(cx - 7, head_y), QPointF(cx + 7, head_y))
        else:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(eye))
            painter.drawEllipse(QPointF(cx, head_y), 6.5, 7.5 if not happy else 8.5)
            painter.setBrush(QBrush(QColor(255, 255, 255, 230)))
            painter.drawEllipse(QPointF(cx + 2.2, head_y - 2.6), 2.2, 2.6)


def _draw_zzz(painter, rect, scale, t):
    painter.save()
    painter.translate(rect.center().x() + 45 * scale, rect.top() + 40 * scale)
    painter.scale(scale, scale)
    font = QFont()
    font.setBold(True)
    font.setPointSize(14)
    painter.setFont(font)
    for i in range(3):
        phase = (t * 0.6 + i * 0.33) % 1.0
        alpha = int(255 * (1.0 - phase))
        painter.setPen(QColor(90, 90, 120, max(0, alpha)))
        size = 10 + i * 4
        font.setPointSize(size)
        painter.setFont(font)
        painter.drawText(QPointF(i * 10, -phase * 30 - i * 6), "z")
    painter.restore()


def _draw_hearts(painter, rect, scale, t):
    painter.save()
    painter.translate(rect.center().x(), rect.top() + 30 * scale)
    painter.scale(scale, scale)
    for i in range(3):
        phase = (t * 1.2 + i * 0.4) % 1.0
        alpha = int(230 * (1.0 - phase))
        x = -20 + i * 20
        y = -phase * 35
        size = 6 - i
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(255, 90, 130, max(0, alpha)))
        path = QPainterPath()
        path.moveTo(x, y + size)
        path.cubicTo(x - size * 2, y - size, x - size * 0.5, y - size * 1.8, x, y - size * 0.5)
        path.cubicTo(x + size * 0.5, y - size * 1.8, x + size * 2, y - size, x, y + size)
        painter.drawPath(path)
    painter.restore()
