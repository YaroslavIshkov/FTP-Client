# SPDX-FileCopyrightText: 2026 YaroslavIshkov
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""Диалог подтверждения перезаписи файла.

Содержит класс OverwriteDialog - модальное окно с вопросом, 
перезаписать ли существующий файл. Используется при скачивании
и загрузке, если файл уже существует.
"""

from typing import Optional
from PyQt5.QtWidgets import (QDialog, QFrame, QLabel, QPushButton, 
    QVBoxLayout, QHBoxLayout, QSizePolicy, QMainWindow)
from PyQt5.QtCore import Qt
from core.frontend.ui.styles.styles import (WHITE_FRAME, TRANSPARENT_LABEL, 
    TRANSPARENT_BUTTON, SHADOW_MARGIN, apply_shadow)


class OverwriteDialog(QDialog):
    """Диалог подтверждения перезаписи файла.
    
    Отображает сообщение с именем файла и две кнопки: 'Отмена' и 'Перезаписать'.
    Закрывается с кодом Accepted при потверждении.

    Attributes:
        title_label: Заголовок диалога.
        message_label: Текст с вопросом о перезаписи.
        cancel_button: Кнопка отмены.
        overwrite_button: Кнопка подтверждения перезаписи.
    """
    def __init__(self, 
                    parent: Optional[QMainWindow] = None, 
                    filename: str = ""):
        super().__init__(parent)
        self.setWindowFlag(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setMinimumWidth(420)

        self.outer_layout = QVBoxLayout(self)
        self.outer_layout.setContentsMargins(SHADOW_MARGIN, SHADOW_MARGIN, 
            SHADOW_MARGIN, SHADOW_MARGIN)

        self.frame = QFrame()
        self.frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.frame.setStyleSheet(WHITE_FRAME)
        apply_shadow(self.frame)
        self.outer_layout.addWidget(self.frame)

        self.inner_layout = QVBoxLayout(self.frame)
        self.inner_layout.setContentsMargins(20, 20, 20, 15)
        self.inner_layout.setSpacing(15)

        self.title_label = QLabel()
        self.title_label.setText("Файл уже существует")
        self.title_label.setStyleSheet(TRANSPARENT_LABEL)
        self.inner_layout.addWidget(self.title_label)

        msg = (
            f"Файл '{filename}' уже есть в этой папке.\n\n"
            "Перезаписать его?"
        )
        self.message_label = QLabel()
        self.message_label.setText(msg)
        self.message_label.setWordWrap(True)
        self.message_label.setStyleSheet(TRANSPARENT_LABEL)
        self.inner_layout.addWidget(self.message_label)

        self.button_layout = QHBoxLayout()
        self.button_layout.setContentsMargins(0, 10, 0, 0)
        self.button_layout.setSpacing(10)
        self.button_layout.addStretch()

        self.cancel_button = QPushButton()
        self.cancel_button.setText("Отмена")
        self.cancel_button.setFixedSize(100, 36)
        self.cancel_button.setCursor(Qt.PointingHandCursor)
        self.cancel_button.clicked.connect(self.reject)
        self.cancel_button.setStyleSheet(TRANSPARENT_BUTTON)
        self.button_layout.addWidget(self.cancel_button)

        self.overwrite_button = QPushButton()
        self.overwrite_button.setText("Перезаписать")
        self.overwrite_button.setFixedSize(140, 36)
        self.overwrite_button.setCursor(Qt.PointingHandCursor)
        self.overwrite_button.clicked.connect(self.accept)
        self.overwrite_button.setStyleSheet(TRANSPARENT_BUTTON)
        self.button_layout.addWidget(self.overwrite_button)

        self.inner_layout.addLayout(self.button_layout)
