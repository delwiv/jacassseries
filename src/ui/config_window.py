from __future__ import annotations

from typing import Optional

import qtawesome as qta
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QFormLayout,
    QLineEdit,
    QComboBox,
    QPushButton,
    QHBoxLayout,
    QDialogButtonBox,
    QMessageBox,
    QLabel,
)

from ..audio.capture import AudioCapture
from ..config import Config
from ..llm.client import LLMClient
from ..tts.synthesizer import KNOWN_VOICES


class ConfigWindow(QDialog):
    def __init__(self, config: Config, llm_client: Optional[LLMClient] = None) -> None:
        super().__init__()
        self._config = config
        self._llm_client = llm_client
        self.setWindowTitle("Configuration jacasseries")
        self.setMinimumWidth(500)
        self._setup_ui()
        self._populate()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.api_url = QLineEdit()
        form.addRow("API URL :", self.api_url)

        self.api_key = QLineEdit()
        self.api_key.setEchoMode(QLineEdit.EchoMode.Password)
        form.addRow("API Key :", self.api_key)

        model_row = QHBoxLayout()
        self.llm_model = QComboBox()
        self.llm_model.setEditable(True)
        model_row.addWidget(self.llm_model)
        refresh_btn = QPushButton()
        refresh_btn.setIcon(qta.icon("fa6s.rotate", color="#555555"))
        refresh_btn.setFixedSize(32, 32)
        refresh_btn.setToolTip("Rafraîchir la liste des modèles")
        refresh_btn.clicked.connect(self._refresh_models)
        model_row.addWidget(refresh_btn)
        form.addRow("Modèle LLM :", model_row)

        self.stt_language = QComboBox()
        self.stt_language.addItems(["fr", "en", "auto"])
        form.addRow("Langue STT :", self.stt_language)

        self.stt_model_size = QComboBox()
        self.stt_model_size.addItems(["small", "medium", "large-v3", "large-v3-turbo"])
        form.addRow("Modèle STT :", self.stt_model_size)

        self.tts_voice = QComboBox()
        self.tts_voice.addItems(sorted(KNOWN_VOICES))
        form.addRow("Voix TTS :", self.tts_voice)

        self.microphone = QComboBox()
        self.microphone.addItem("Défaut", "")
        for dev in AudioCapture.list_input_devices():
            dev_id = dev.split(":")[0]
            self.microphone.addItem(dev, dev_id)
        form.addRow("Microphone :", self.microphone)

        self.keyboard_shortcut = QLineEdit()
        self.keyboard_shortcut.setPlaceholderText("ex: Ctrl+Space")
        form.addRow("Raccourci :", self.keyboard_shortcut)

        layout.addLayout(form)
        layout.addStretch()

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _populate(self) -> None:
        self.api_url.setText(self._config.api_url)
        self.api_key.setText(self._config.api_key)

        idx = self.llm_model.findText(self._config.llm_model)
        if idx >= 0:
            self.llm_model.setCurrentIndex(idx)
        else:
            self.llm_model.setCurrentText(self._config.llm_model)

        idx = self.stt_language.findText(self._config.stt_language)
        if idx >= 0:
            self.stt_language.setCurrentIndex(idx)

        idx = self.stt_model_size.findText(self._config.stt_model_size)
        if idx >= 0:
            self.stt_model_size.setCurrentIndex(idx)

        idx = self.tts_voice.findText(self._config.tts_voice or "fr_FR-siwis-medium")
        if idx >= 0:
            self.tts_voice.setCurrentIndex(idx)

        for i in range(self.microphone.count()):
            if self.microphone.itemData(i) == self._config.microphone:
                self.microphone.setCurrentIndex(i)
                break

        self.keyboard_shortcut.setText(self._config.keyboard_shortcut)

    def _refresh_models(self) -> None:
        if self._llm_client is None:
            QMessageBox.warning(self, "Info", "Client LLM non disponible")
            return
        url = self.api_url.text().strip()
        key = self.api_key.text().strip()
        client = LLMClient(base_url=url, api_key=key)
        try:
            models = client.list_models()
        except Exception as e:
            QMessageBox.warning(self, "Erreur", f"Impossible de récupérer les modèles :\n{e}")
            return
        current = self.llm_model.currentText()
        self.llm_model.clear()
        self.llm_model.addItems(models)
        idx = self.llm_model.findText(current)
        if idx >= 0:
            self.llm_model.setCurrentIndex(idx)
        elif models:
            self.llm_model.setCurrentIndex(0)

    def _save(self) -> None:
        self._config.api_url = self.api_url.text().strip()
        self._config.api_key = self.api_key.text().strip()
        self._config.llm_model = self.llm_model.currentText().strip()
        self._config.stt_language = self.stt_language.currentText().strip()
        self._config.stt_model_size = self.stt_model_size.currentText().strip()
        self._config.tts_voice = self.tts_voice.currentText().strip()
        self._config.microphone = str(self.microphone.currentData() or "")
        self._config.keyboard_shortcut = self.keyboard_shortcut.text().strip()
        self._config.save()
        self.accept()
