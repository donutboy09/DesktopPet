from __future__ import annotations

import math
import random

from PySide6.QtCore import QPoint, Qt, QTimer, Signal
from PySide6.QtGui import QCursor, QGuiApplication, QPainter
from PySide6.QtWidgets import QWidget

from pet_art import PALETTES, SIZE_PRESETS, draw_pet

IDLE = "idle"
WALK = "walk"
SLEEP = "sleep"
DRAG = "drag"
HAPPY = "happy"
EAT = "eat"

HUNGER_DECAY = 100.0 / (15 * 60)


class Pet(QWidget):
    menu_requested = Signal(QPoint)

    def __init__(self, species: str = "cat", size: str = "small", parent=None):
        super().__init__(parent)
        self.species = species
        self.size_name = size
        self.setFixedSize(SIZE_PRESETS[size], SIZE_PRESETS[size])

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground)
        self.setCursor(QCursor(Qt.CursorShape.OpenHandCursor))

        self.state = WALK
        self.free_roam = True
        self.hunger = 100.0
        self.t = 0.0
        self.facing = 1
        self.blink = 0.0
        self._next_blink = random.randint(30, 120)
        self._state_timer = 0.0
        self._state_duration = 0.0
        self._drag_offset = QPoint()
        self._press_pos = QPoint()
        self._dragged = False
        self._happy_timer = 0.0
        self._target = None
        self._speed = random.uniform(45.0, 80.0)
        self._walk_phase = 0.0
        self._manual = False

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(33)
        self._pick_target()

    def set_species(self, species: str):
        self.species = species
        self.update()

    def set_size(self, size: str):
        center = self.frameGeometry().center()
        self.size_name = size
        self.setFixedSize(SIZE_PRESETS[size], SIZE_PRESETS[size])
        self.move(center.x() - self.width() // 2, center.y() - self.height() // 2)
        self._snap_to_screen()
        self.update()

    def set_free_roam(self, free: bool):
        self.free_roam = free
        self._manual = False
        if not free:
            self._change_state(IDLE)
        else:
            self._change_state(WALK)

    def feed(self):
        self.hunger = 100.0
        self._manual = True
        self._change_state(EAT)

    def trigger_happy(self):
        self._manual = True
        self._change_state(HAPPY)
        self._happy_timer = 1.6

    def toggle_sleep(self):
        if self.state == SLEEP:
            self._manual = False
            self._change_state(IDLE if not self.free_roam else WALK)
        else:
            self._manual = True
            self._change_state(SLEEP)

    def _screen_rect(self):
        screen = QGuiApplication.screenAt(self.frameGeometry().center())
        if screen is None:
            screen = QGuiApplication.primaryScreen()
        return screen.availableGeometry()

    def _pick_target(self):
        rect = self._screen_rect()
        max_x = max(rect.left(), rect.right() - self.width())
        max_y = max(rect.top(), rect.bottom() - self.height())
        self._target = QPoint(
            random.randint(rect.left(), max_x),
            random.randint(rect.top(), max_y),
        )
        self._speed = random.uniform(45.0, 85.0)

    def _tick(self):
        self.t += 0.033
        self.blink = max(0.0, self.blink - 0.08)
        if self._next_blink <= 0:
            self.blink = 1.0
            self._next_blink = random.randint(40, 140)
        self._next_blink -= 1

        self.hunger = max(0.0, self.hunger - HUNGER_DECAY * 0.033)

        if self.state != DRAG and self.state != EAT and self.state != SLEEP:
            self._state_timer += 0.033

        if self.state == DRAG:
            self._walk_phase += 0.2
        elif self.state == HAPPY:
            self._happy_timer -= 0.033
            if self._happy_timer <= 0:
                self._manual = False
                self._change_state(WALK if self.free_roam else IDLE)
        elif self.state == SLEEP:
            pass
        elif self.state == EAT:
            if self._state_timer > self._state_duration:
                self._manual = False
                self._change_state(WALK if self.free_roam else IDLE)
        elif self.state == WALK:
            self._walk_phase += 0.2
            self._move_walk()
        else:
            self._walk_phase = 0.0
            if self.free_roam and self._state_timer > self._state_duration:
                self._change_state(WALK)

        self.update()

    def _change_state(self, state: str):
        self.state = state
        self._state_timer = 0.0
        if state == WALK:
            if not self._manual or self._target is None:
                self._pick_target()
            self._state_duration = 0.0
            if self._target is not None:
                self.facing = 1 if self._target.x() >= self.x() else -1
        elif state == EAT:
            self._state_duration = 3.5
        elif state == SLEEP:
            self._state_duration = 0.0
        elif state == IDLE:
            self._state_duration = random.uniform(0.7, 1.8)
        else:
            self._state_duration = 1.6

    def _move_walk(self):
        if self._target is None:
            self._pick_target()
        dx = self._target.x() - self.x()
        dy = self._target.y() - self.y()
        dist = math.hypot(dx, dy)
        if dist < 6:
            if random.random() < 0.2:
                self._change_state(IDLE)
            else:
                self._pick_target()
            return
        self.facing = 1 if dx >= 0 else -1
        step = min(self._speed * 0.033, dist)
        self.move(
            self.x() + int(round(step * dx / dist)),
            self.y() + int(round(step * dy / dist)),
        )
        self._snap_to_screen()

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
                self._manual = False
                self._change_state(WALK if self.free_roam else IDLE)
            event.accept()

    def mouseDoubleClickEvent(self, event):
        self.trigger_happy()
        event.accept()

    def contextMenuEvent(self, event):
        self.menu_requested.emit(event.globalPos())
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
        draw_pet(
            painter,
            self.rect(),
            self.species,
            PALETTES[self.species],
            self.state,
            self.t,
            self.facing,
            self.blink,
            self._walk_phase,
            self.hunger,
        )
