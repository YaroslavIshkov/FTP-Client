# SPDX-FileCopyrightText: 2026 YaroslavIshkov
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""Шапка (header) главное окно FTP-Client.

Содержит название приложения и три кнопки управления окном:
свернуть, развернуть/восстановить, закрыть. Иконки
кнопок загружаются из icons/header/ через Application.get_header_icon().
"""

from typing import Optional
from PyQt5.QtWidgets import (QFrame, QLabel, QSizePolicy, QHBoxLayout, 
    QPushButton)
from PyQt5.QtCore import Qt, QSize, QTimer
from PyQt5.QtGui import QIcon, QPixmap
from core.frontend.ui.styles.styles import (TRANSPARENT_FRAME, HEADER_LABEL, 
    HEADER_BUTTON)
from core.app.application import Application


class HeaderFrame(QFrame):
    """Шапка окна с названием и кнопками управления.
    
    Frameless-режим, поэтому все три кнопки (minimize, maximize, close)
    реализованы вручную. Иконка кнопки разворачивания менается автоматически:
    maximize -> restore и обратно.

    Attributes:
        app: Ссылка на Application.
        title_label: Название приложения окна.
        minimize_button: Кнопка разворачивания/восстановления.
        close_button: Кнопка закрытя приложения.
    """

    def __init__(self, app: Optional[Application] = None):
        """Создаёт шапку с тремя кнопками управления.
        
        Args:
            app: Экземпляр Application - оттуда загружаются иконки через
                get_header_icon().
        """
        super().__init__()
        self.app = app
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setStyleSheet(TRANSPARENT_FRAME)

        self.header_layout = QHBoxLayout(self)
        self.header_layout.setContentsMargins(5, 5, 5, 5)

        self.title_label = QLabel()
        self.title_label.setText("FTP Client")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setFixedHeight(50)
        self.title_label.setStyleSheet(HEADER_LABEL)
        self.header_layout.addWidget(self.title_label)
        self.header_layout.addStretch()

        self.minimize_button = self._make_button(
            self.app.get_header_icon("minimize"), tip="Свернуть")
        self.fullscreen_button = self._make_button(
            self.app.get_header_icon("maximize"), tip="Развернуть")
        self.close_button = self._make_button(
            self.app.get_header_icon("close"), tip="Закрыть")

        self.minimize_button.clicked.connect(self._on_minimize)
        self.fullscreen_button.clicked.connect(self._on_fullscreen)
        self.close_button.clicked.connect(self._on_close)

        self.header_layout.addWidget(self.minimize_button)
        self.header_layout.addWidget(self.fullscreen_button)
        self.header_layout.addWidget(self.close_button)
        self._update_fullscreen_icon()
    
    def _make_button(self, pixmap: QPixmap, tip: str = "") -> QPushButton:
        """Создаёт кнопку с иконкой для шапки.
        
        Args:
            pixmap: Готовая иконка (QPixmap из Application).
            tip: Текст подсказки при наведении.
        
        Returns:
            Готовая кнопка QPushButton с настройкой стиля.
        """
        btn = QPushButton()
        btn.setIcon(QIcon(pixmap))
        btn.setIconSize(QSize(30, 30))
        btn.setFixedSize(50, 50)
        btn.setToolTip(tip)
        btn.setStyleSheet(HEADER_BUTTON)
        return btn
    
    def _on_minimize(self):
        """Сворачивает окно (showMinimized)."""
        self.window().showMinimized()
    
    def _on_fullscreen(self):
        """Разворачивает окно или восстанавливает его.
        
        После смены состояния иконка обновляется через QTimer
        с задержкой 50 мс - Qt меняет WindowState асинхронно, 
        поэтому сразу после showMaximized() метод isMaximized()
        ещё возвращает старое значение.
        """
        window = self.window()
        if window.isMaximized() or window.isFullScreen():
            window.showNormal()
        else:
            window.showMaximized()
        
        QTimer.singleShot(50, self._update_fullscreen_icon)
    
    def _update_fullscreen_icon(self):
        """Меняет иконку разворачивания по состоянию окна.
        
        Если окно развёрнуто - иконка 'restore' (для квадрата), 
        иначе - 'maximize' (один квадрат).
        """
        window = self.window()
        if window.isMaximized() or window.isFullScreen():
            icon_name = "restore"
        else:
            icon_name = "maximize"
        self.fullscreen_button.setIcon(
            QIcon(self.app.get_header_icon(icon_name))
        )
    
    def _on_close(self):
        """Закрывает главное окно приложения."""
        self.window().close()
