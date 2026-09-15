from __future__ import annotations

import math
import random

from PySide6.QtCore import QPoint, Qt, QTimer
from PySide6.QtGui import QCursor, QGuiApplication, QPainter
from PySide6.QtWidgets import QWidget

from pet_art import PALETTES, draw_pet

IDLE = "idle"
WALK = "walk"
SLEEP = "sleep"
DRAG = "drag"
HAPPY = "happy"


class Pet(QWidget):
    def __init__(self, species: str = "cat", scale: float = 1.0, parent=None):
        super().__init__(parent)
        self.species = species
        self.pet_scale = scale
        self.base_size = 180
        self.setFixedSize(self.base_size, self.base_size)

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground)
        self.setCursor(QCursor(Qt.CursorShape.OpenHandCursor))

        self.state = IDLE
        self.frame = 0
        self.t = 0.0
        self.facing = 1
        self.blink = 0.0
        self._next_blink = random.randint(30, 120)
        self._state_timer = 0.0
        self._state_duration = random.uniform(4.0, 9.0)
        self._drag_offset = QPoint()
        self._press_pos = QPoint()
        self._dragged = False
        self._happy_timer = 0.0
        self._target_x = None
        self._speed = random.uniform(35.0, 70.0)
        self._walk_phase = 0.0

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(33)

    def set_species(self, species: str):
        self.species = species
        self.update()

    def _screen_rect(self):
        screen = QGuiApplication.screenAt(self.frameGeometry().center())
        if screen is None:
            screen = QGuiApplication.primaryScreen()
        return screen.availableGeometry()

    def _tick(self):
        self.t += 0.033
        self.frame += 1
        self.blink = max(0.0, self.blink - 0.08)

        if self._next_blink <= 0:
            self.blink = 1.0
            self._next_blink = random.randint(40, 140)
        self._next_blink -= 1

        if self.state == DRAG:
            self._walk_phase += 0.2
            self.update()
            return

        self._state_timer += 0.033

        if self.state == HAPPY:
            self._happy_timer -= 0.033
            if self._happy_timer <= 0:
                self._change_state(IDLE)
        elif self.state == SLEEP:
            if self._state_timer > self._state_duration:
                self._change_state(IDLE)
        elif self.state == WALK:
            self._walk_phase += 0.18
            self._move_walk()
            if self._target_x is None or self._state_timer > self._state_duration:
                self._change_state(IDLE)
        else:
            self._walk_phase = 0.0
            if self._state_timer > self._state_duration:
                self._change_state(random.choices([WALK, SLEEP, IDLE], weights=[5, 2, 3])[0])

        self.update()

    def _change_state(self, state: str):
        self.state = state
        self._state_timer = 0.0
        if state == WALK:
            self._state_duration = random.uniform(4.0, 10.0)
            self._speed = random.uniform(35.0, 70.0)
            rect = self._screen_rect()
            self._target_x = random.randint(rect.left(), max(rect.left(), rect.right() - self.width()))
            if self._target_x < self.x():
                self.facing = -1
            else:
                self.facing = 1
        elif state == SLEEP:
            self._state_duration = random.uniform(8.0, 20.0)
        else:
            self._state_duration = random.uniform(3.0, 8.0)

    def _move_walk(self):
        if self._target_x is None:
            return
        dx = self._target_x - self.x()
        if abs(dx) < 3:
            self._target_x = None
            self._change_state(IDLE)
            return
        self.facing = 1 if dx > 0 else -1
        step = self._speed * 0.033 * self.facing
        if abs(step) > abs(dx):
            step = dx
        self.move(self.x() + int(round(step)), self.y())

    def trigger_happy(self):
        self._change_state(HAPPY)
        self._happy_timer = 1.6
        self.facing = random.choice([-1, 1])

    def toggle_sleep(self):
        if self.state == SLEEP:
            self._change_state(IDLE)
        else:
            self._change_state(SLEEP)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._press_pos = event.globalPosition().toPoint()
            self._drag_offset = self._press_pos - self.frameGeometry().topLeft()
            self._dragged = False
            self.setCursor(QCursor(Qt.CursorShape.ClosedHandCursor))
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.MouseButton.LeftButton:
            pos = event.globalPosition().toPoint()
            if (pos - self._press_pos).manhattanLength() > 4:
                self._dragged = True
            if self._dragged:
                if self.state != DRAG:
                    self._change_state(DRAG)
                self.move(pos - self._drag_offset)
            event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.setCursor(QCursor(Qt.CursorShape.OpenHandCursor))
            if self._dragged:
                self._snap_to_screen()
                self._change_state(IDLE)
            event.accept()

    def mouseDoubleClickEvent(self, event):
        self.trigger_happy()
        event.accept()

    def _snap_to_screen(self):
        rect = self._screen_rect()
        x = min(max(self.x(), rect.left()), rect.right() - self.width())
        y = min(max(self.y(), rect.top()), rect.bottom() - self.height())
        self.move(x, y)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
        palette = PALETTES[self.species]
        draw_pet(
            painter,
            self.rect(),
            self.species,
            palette,
            self.state,
            self.t,
            self.facing,
            self.blink,
            self._walk_phase,
        )
