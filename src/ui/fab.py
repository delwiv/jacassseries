from __future__ import annotations

import qtawesome as qta
from PySide6.QtWidgets import QWidget, QMenu
from PySide6.QtCore import Qt, QSize, Signal, QPoint, QTimer, QRect
from PySide6.QtGui import QColor, QMouseEvent, QPainter, QBrush, QPen

from src.pipeline.orchestrator import Mode, State


COLORS = {
    State.IDLE: "#9E9E9E",
    State.RECORDING: "#F44336",
    State.TRANSCRIBING: "#FF9800",
    State.LLM: "#2196F3",
    State.TTS: "#4CAF50",
}

CONVERSATION_ICONS = {
    State.IDLE: "fa6s.microphone",
    State.RECORDING: "fa6s.microphone",
    State.TRANSCRIBING: "fa6s.pen",
    State.LLM: "fa6s.robot",
    State.TTS: "fa6s.volume-high",
}

DICTATION_ICONS = {
    State.IDLE: "fa6s.keyboard",
    State.RECORDING: "fa6s.microphone",
    State.TRANSCRIBING: "fa6s.pen",
    State.LLM: "fa6s.robot",
    State.TTS: "fa6s.volume-high",
}

FAB_SIZE = 56


class FAB(QWidget):
    clicked = Signal()
    long_pressed = Signal()
    config_requested = Signal()
    reset_requested = Signal()
    quit_requested = Signal()
    mode_change_requested = Signal(object)

    _DRAG_THRESHOLD = 5

    def __init__(self) -> None:
        super().__init__()
        self._state = State.IDLE
        self._mode = Mode.CONVERSATION
        self._drag_pos: QPoint | None = None
        self._press_pos: QPoint | None = None
        self._dragged = False
        self._long_press_fired = False
        self._hovered = False
        self._long_press_timer = QTimer(self)
        self._long_press_timer.setSingleShot(True)
        self._long_press_timer.timeout.connect(self._on_long_press)
        self._setup_window()

    def _setup_window(self) -> None:
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_Hover)
        self.setFixedSize(FAB_SIZE, FAB_SIZE)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    @property
    def state(self) -> State:
        return self._state

    @state.setter
    def state(self, new_state: State) -> None:
        if new_state != self._state:
            self._state = new_state
            self.update()

    @property
    def mode(self) -> Mode:
        return self._mode

    def set_mode(self, mode: Mode) -> None:
        self._mode = mode
        self.update()

    def _icons(self) -> dict:
        return DICTATION_ICONS if self._mode == Mode.DICTATION else CONVERSATION_ICONS

    def _icon_name(self) -> str:
        return self._icons().get(self._state, CONVERSATION_ICONS[State.IDLE])

    def _color(self) -> str:
        return COLORS.get(self._state, COLORS[State.IDLE])

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        color = QColor(self._color())
        if self._hovered:
            color = QColor(self._color())
            color.setAlpha(204)
        rect = self.rect()
        painter.setBrush(QBrush(color))
        painter.setPen(QPen(color.lighter(120), 0))
        painter.drawEllipse(rect)
        icon = qta.icon(self._icon_name(), color="#FFFFFF")
        icon_size = 24
        icon_rect = QRect(
            (rect.width() - icon_size) // 2,
            (rect.height() - icon_size) // 2,
            icon_size,
            icon_size,
        )
        icon.paint(painter, icon_rect)

    def _on_long_press(self) -> None:
        self._long_press_fired = True
        self.long_pressed.emit()

    def contextMenuEvent(self, event) -> None:
        menu = QMenu(self)
        reset_action = menu.addAction("Nouvelle discussion")
        reset_action.triggered.connect(self.reset_requested.emit)
        menu.addSeparator()
        mode_action = menu.addAction("Mode dictée")
        mode_action.setCheckable(True)
        mode_action.setChecked(self._mode == Mode.DICTATION)
        mode_action.triggered.connect(self._toggle_mode)
        menu.addSeparator()
        config_action = menu.addAction("Configuration")
        config_action.triggered.connect(self.config_requested.emit)
        menu.addSeparator()
        quit_action = menu.addAction("Quitter")
        quit_action.triggered.connect(self.quit_requested.emit)
        menu.exec(event.globalPos())

    def _toggle_mode(self) -> None:
        new_mode = Mode.DICTATION if self._mode == Mode.CONVERSATION else Mode.CONVERSATION
        self.mode_change_requested.emit(new_mode)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            self._press_pos = event.globalPosition().toPoint()
            self._dragged = False
            self._long_press_fired = False
            self._long_press_timer.start(1000)
            event.accept()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if event.buttons() == Qt.MouseButton.LeftButton and self._drag_pos is not None:
            if self._press_pos:
                delta = event.globalPosition().toPoint() - self._press_pos
                if delta.manhattanLength() > self._DRAG_THRESHOLD:
                    self._dragged = True
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._long_press_timer.stop()
            if not self._long_press_fired and not self._dragged:
                self.clicked.emit()
            self._drag_pos = None
            self._press_pos = None
            self._dragged = False
            event.accept()

    def enterEvent(self, event) -> None:
        self._hovered = True
        self.update()

    def leaveEvent(self, event) -> None:
        self._hovered = False
        self.update()
