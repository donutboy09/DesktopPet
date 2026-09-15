from __future__ import annotations

import math

from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QBrush, QColor, QFont, QPainterPath, QPen

PALETTES = {
    "cat": {
        "body": "#FFF6EA",
        "body_dark": "#F0DFC8",
        "patch": "#F5A93F",
        "belly": "#FFFFFF",
        "ear_inner": "#FFC2D6",
        "nose": "#FF7BAC",
        "eye": "#3A2A1A",
        "blush": "#FFB3C6",
        "outline": "#C6A177",
        "collar": "#E4572E",
        "bell": "#F4C430",
    },
    "dog": {
        "body": "#F2B45C",
        "body_dark": "#DE9A3E",
        "patch": "#FFF6EA",
        "belly": "#FFF6EA",
        "ear_inner": "#E8A06A",
        "nose": "#4A3220",
        "eye": "#2E2014",
        "blush": "#E8A88A",
        "outline": "#B47A2E",
        "collar": "#3E8EDE",
        "bell": "#F4C430",
    },
}

SIZE_PRESETS = {"small": 110, "medium": 140, "large": 175}


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


def _ellipse(painter, cx, cy, rx, ry, fill, outline=None, width=2.4):
    painter.setPen(_pen(outline, width) if outline else Qt.PenStyle.NoPen)
    painter.setBrush(QBrush(fill))
    painter.drawEllipse(QPointF(cx, cy), rx, ry)


def _tri(painter, pts, fill, outline=None, width=2.4):
    path = QPainterPath()
    path.moveTo(*pts[0])
    path.lineTo(*pts[1])
    path.lineTo(*pts[2])
    path.closeSubpath()
    painter.setPen(_pen(outline, width) if outline else Qt.PenStyle.NoPen)
    painter.setBrush(QBrush(fill))
    painter.drawPath(path)


def draw_pet(painter, rect, species, palette, state, t, facing, blink, walk_phase, hunger=100):
    scale = min(rect.width(), rect.height()) / 180.0
    painter.save()
    painter.translate(rect.left(), rect.top())
    painter.scale(scale, scale)
    painter.translate(90, 0)
    painter.scale(facing, 1)
    painter.translate(-90, 0)

    body = _c(palette["body"])
    body_dark = _c(palette["body_dark"])
    patch = _c(palette["patch"])
    belly = _c(palette["belly"])
    ear_inner = _c(palette["ear_inner"])
    nose = _c(palette["nose"])
    eye = _c(palette["eye"])
    blush = _c(palette["blush"])
    outline = _c(palette["outline"])
    collar = _c(palette["collar"])
    bell = _c(palette["bell"])

    sleeping = state == "sleep"
    walking = state == "walk"
    happy = state == "happy"
    dragging = state == "drag"
    eating = state == "eat"

    speed = 1.5 if sleeping else 3.0
    bob = math.sin(t * speed) * (1.0 if sleeping else 1.8)
    if happy:
        bob = -abs(math.sin(t * 9.0)) * 7.0
    if dragging:
        bob = math.sin(t * 6.0) * 1.5

    wag = math.sin(t * (11.0 if walking or happy else 2.6)) * (0.55 if walking or happy else 0.25)
    leg_swing = math.sin(walk_phase) * 5.0 if walking else 0.0
    head_drop = 15.0 if eating else 0.0
    if eating:
        head_drop += math.sin(t * 12.0) * 2.5

    _draw_tail(painter, species, body_dark, patch, outline, wag, sleeping)

    _ellipse(painter, 66, 164 + leg_swing, 15, 10, body, outline)
    _ellipse(painter, 114, 164 - leg_swing, 15, 10, body, outline)

    _ellipse(painter, 90, 138 + bob, 41, 34, body, outline)
    _ellipse(painter, 90, 145 + bob, 24, 21, belly, None)

    if species == "dog":
        _ellipse(painter, 90, 140 + bob, 20, 18, patch, None)

    head_y = 74 + bob * 1.1 + head_drop

    _draw_ears(painter, species, body, body_dark, patch, ear_inner, outline, head_y)
    _ellipse(painter, 90, head_y, 46, 42, body, outline)

    if species == "cat":
        _draw_stripes(painter, patch, head_y)
    else:
        _ellipse(painter, 90, head_y + 12, 22, 17, patch, None)

    _draw_face(painter, species, eye, nose, blush, outline, head_y, blink, sleeping, happy, eating)
    _draw_collar(painter, collar, bell, head_y)

    painter.restore()

    if eating:
        _draw_bowl(painter, rect, scale, t)
    if sleeping:
        _draw_zzz(painter, rect, scale, t)
    if happy:
        _draw_hearts(painter, rect, scale, t)
    if not eating and not sleeping and hunger < 30:
        _draw_hungry(painter, rect, scale, t, species)


def _draw_tail(painter, species, body_dark, patch, outline, wag, sleeping):
    path = QPainterPath()
    if species == "cat":
        path.moveTo(126, 140)
        path.quadTo(176 + wag * 22, 118 - wag * 14, 150 + wag * 34, 74)
        pen = _pen(body_dark, 13.0)
    else:
        path.moveTo(122, 132)
        path.cubicTo(168 + wag * 16, 130, 172, 92, 142 + wag * 12, 96)
        pen = _pen(body_dark, 15.0)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    painter.setPen(pen)
    painter.setBrush(Qt.BrushStyle.NoBrush)
    painter.drawPath(path)
    painter.setPen(_pen(outline, 2.0))
    painter.drawPath(path)
    if species == "cat":
        painter.setPen(_pen(patch, 6.0))
        for i in range(3):
            seg = QPainterPath()
            x = 138 + i * 8
            seg.moveTo(x, 132 - i * 6)
            seg.lineTo(x + 6, 126 - i * 6)
            painter.drawPath(seg)


def _draw_ears(painter, species, body, body_dark, patch, ear_inner, outline, head_y):
    top = head_y - 40
    if species == "cat":
        _tri(painter, [(56, top + 20), (50, top - 14), (84, top + 4)], body, outline)
        _tri(painter, [(124, top + 20), (130, top - 14), (96, top + 4)], body, outline)
        _tri(painter, [(62, top + 14), (58, top - 4), (80, top + 4)], ear_inner, None, 0)
        _tri(painter, [(118, top + 14), (122, top - 4), (100, top + 4)], ear_inner, None, 0)
    else:
        _tri(painter, [(54, top + 24), (46, top - 16), (86, top + 2)], body, outline)
        _tri(painter, [(126, top + 24), (134, top - 16), (94, top + 2)], body, outline)
        _tri(painter, [(60, top + 18), (54, top - 4), (82, top + 2)], ear_inner, None, 0)
        _tri(painter, [(120, top + 18), (126, top - 4), (98, top + 2)], ear_inner, None, 0)


def _draw_stripes(painter, patch, head_y):
    painter.setPen(_pen(patch, 5.0))
    painter.setBrush(Qt.BrushStyle.NoBrush)
    for dx in (-12, 0, 12):
        path = QPainterPath()
        path.moveTo(90 + dx, head_y - 34)
        path.lineTo(90 + dx * 0.7, head_y - 22)
        painter.drawPath(path)


def _draw_face(painter, species, eye, nose, blush, outline, head_y, blink, sleeping, happy, eating):
    for cx in (70, 110):
        if sleeping or happy or blink > 0.5:
            painter.setPen(_pen(eye, 3.0))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            path = QPainterPath()
            if happy:
                path.moveTo(cx - 8, head_y + 3)
                path.quadTo(cx, head_y - 6, cx + 8, head_y + 3)
            elif sleeping:
                path.moveTo(cx - 8, head_y - 1)
                path.quadTo(cx, head_y + 5, cx + 8, head_y - 1)
            else:
                path.moveTo(cx - 8, head_y)
                path.lineTo(cx + 8, head_y)
            painter.drawPath(path)
        else:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(eye))
            painter.drawEllipse(QPointF(cx, head_y), 9, 10.5)
            painter.setBrush(QBrush(QColor(255, 255, 255, 235)))
            painter.drawEllipse(QPointF(cx + 3, head_y - 3.5), 3.2, 3.6)
            painter.drawEllipse(QPointF(cx - 3, head_y + 3), 1.7, 1.9)

    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QBrush(blush))
    painter.drawEllipse(QPointF(52, head_y + 16), 8, 5)
    painter.drawEllipse(QPointF(128, head_y + 16), 8, 5)

    if species == "cat":
        painter.setPen(_pen(outline, 1.5))
        for dy in (-3, 3, 9):
            painter.drawLine(QPointF(48, head_y + dy), QPointF(24, head_y + dy - 5))
            painter.drawLine(QPointF(132, head_y + dy), QPointF(156, head_y + dy - 5))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(nose))
        _tri(painter, [(85, head_y + 10), (95, head_y + 10), (90, head_y + 16)], nose, None, 0)
    else:
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(nose))
        painter.drawEllipse(QPointF(90, head_y + 12), 7, 5.5)

    mouth_top = head_y + (16 if species == "cat" else 17)
    painter.setPen(_pen(outline, 2.2))
    painter.setBrush(Qt.BrushStyle.NoBrush)
    mouth = QPainterPath()
    if eating:
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor("#C24A5A")))
        painter.drawEllipse(QPointF(90, mouth_top + 4), 7, 6)
    else:
        mouth.moveTo(90, mouth_top)
        mouth.quadTo(83, mouth_top + 8, 77, mouth_top + 1)
        mouth.moveTo(90, mouth_top)
        mouth.quadTo(97, mouth_top + 8, 103, mouth_top + 1)
        painter.drawPath(mouth)
    if species == "dog" and not eating:
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor("#FF6B8A")))
        painter.drawEllipse(QPointF(90, mouth_top + 7), 6, 5)


def _draw_collar(painter, collar, bell, head_y):
    painter.setPen(_pen(collar, 7.0))
    painter.setBrush(Qt.BrushStyle.NoBrush)
    path = QPainterPath()
    path.moveTo(56, head_y + 34)
    path.quadTo(90, head_y + 48, 124, head_y + 34)
    painter.drawPath(path)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QBrush(bell))
    painter.drawEllipse(QPointF(90, head_y + 46), 6, 6)
    painter.setBrush(QBrush(QColor(255, 255, 255, 160)))
    painter.drawEllipse(QPointF(88, head_y + 44), 2, 2)


def _draw_bowl(painter, rect, scale, t):
    painter.save()
    painter.translate(rect.left(), rect.top())
    painter.scale(scale, scale)
    painter.setPen(_pen(QColor("#B0B7C3"), 2.4))
    painter.setBrush(QBrush(QColor("#D9DEE7")))
    path = QPainterPath()
    path.moveTo(54, 150)
    path.lineTo(126, 150)
    path.quadTo(120, 176, 90, 176)
    path.quadTo(60, 176, 54, 150)
    path.closeSubpath()
    painter.drawPath(path)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QBrush(QColor("#8A5A2B")))
    for i in range(8):
        x = 62 + (i % 4) * 18
        y = 148 - (i // 4) * 7
        painter.drawEllipse(QPointF(x, y), 5.5, 4.5)
    painter.restore()


def _draw_zzz(painter, rect, scale, t):
    painter.save()
    painter.translate(rect.center().x() + 42 * scale, rect.top() + 36 * scale)
    painter.scale(scale, scale)
    font = QFont()
    font.setBold(True)
    for i in range(3):
        phase = (t * 0.6 + i * 0.33) % 1.0
        alpha = int(255 * (1.0 - phase))
        font.setPointSize(10 + i * 4)
        painter.setFont(font)
        painter.setPen(QColor(90, 90, 120, max(0, alpha)))
        painter.drawText(QPointF(i * 10, -phase * 30 - i * 6), "z")
    painter.restore()


def _draw_hearts(painter, rect, scale, t):
    painter.save()
    painter.translate(rect.center().x(), rect.top() + 26 * scale)
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


def _draw_hungry(painter, rect, scale, t, species):
    painter.save()
    painter.translate(rect.center().x() + 44 * scale, rect.top() + 30 * scale)
    painter.scale(scale, scale)
    pulse = 0.85 + 0.15 * math.sin(t * 4.0)
    painter.setPen(_pen(QColor(255, 255, 255, 230), 2.0))
    painter.setBrush(QBrush(QColor(255, 255, 255, 220)))
    painter.drawEllipse(QPointF(0, 0), 20 * pulse, 16 * pulse)
    painter.drawEllipse(QPointF(-12, 14), 4, 3)
    painter.drawEllipse(QPointF(-17, 20), 2.5, 2)
    if species == "cat":
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor("#5AA9E6")))
        fish = QPainterPath()
        fish.moveTo(-10, 0)
        fish.quadTo(0, -9, 10, 0)
        fish.quadTo(0, 9, -10, 0)
        painter.drawPath(fish)
        painter.setBrush(QBrush(QColor("#5AA9E6")))
        _tri(painter, [(-10, 0), (-18, -6), (-18, 6)], QColor("#5AA9E6"), None, 0)
    else:
        painter.setPen(_pen(QColor("#FFF6EA"), 4.0))
        painter.setBrush(QBrush(QColor("#FFF6EA")))
        painter.drawLine(QPointF(-12, -3), QPointF(12, -3))
        painter.drawEllipse(QPointF(-12, -3), 3.5, 3.5)
        painter.drawEllipse(QPointF(12, -3), 3.5, 3.5)
        painter.drawEllipse(QPointF(-9, 2), 3.5, 3.5)
        painter.drawEllipse(QPointF(9, 2), 3.5, 3.5)
    painter.restore()
