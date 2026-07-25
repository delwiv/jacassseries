from __future__ import annotations

from PySide6.QtWidgets import QSystemTrayIcon, QMenu
from PySide6.QtCore import Signal, QSize
from PySide6.QtGui import QPixmap, QPainter, QColor, QBrush

from src.pipeline.orchestrator import Mode


class SystemTray(QSystemTrayIcon):
    show_requested = Signal()
    config_requested = Signal()
    quit_requested = Signal()
    mode_change_requested = Signal(object)

    def __init__(self) -> None:
        super().__init__()
        self._mode = Mode.CONVERSATION
        self.setIcon(self._make_icon())
        self.setToolTip("jacasseries")
        menu = QMenu()
        show_action = menu.addAction("Afficher / Masquer")
        show_action.triggered.connect(self.show_requested.emit)
        self._mode_action = menu.addAction("Mode dictée")
        self._mode_action.setCheckable(True)
        self._mode_action.triggered.connect(self._toggle_mode)
        config_action = menu.addAction("Configuration")
        config_action.triggered.connect(self.config_requested.emit)
        menu.addSeparator()
        quit_action = menu.addAction("Quitter")
        quit_action.triggered.connect(self.quit_requested.emit)
        self.setContextMenu(menu)
        self.activated.connect(self._on_activated)

    def set_mode(self, mode: Mode) -> None:
        self._mode = mode
        self._mode_action.setChecked(mode == Mode.DICTATION)

    def _toggle_mode(self) -> None:
        new_mode = Mode.DICTATION if self._mode == Mode.CONVERSATION else Mode.CONVERSATION
        self.mode_change_requested.emit(new_mode)

    def _on_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show_requested.emit()

    @staticmethod
    def _make_icon():
        pixmap = QPixmap(22, 22)
        pixmap.fill(QColor(0, 0, 0, 0))
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(QBrush(QColor("#9E9E9E")))
        painter.setPen(QColor(0, 0, 0, 0))
        painter.drawEllipse(1, 1, 20, 20)
        painter.end()
        return pixmap
