# SPDX-FileCopyrightText: 2026 YaroslavIshkov
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""Точка входа FTP-Client.

Инициализирует QApplication, настраивает шрифт и tooltip-стиль, 
создаёт главное окно и запускает цикл обработки событий Qt.
"""

import sys
from functools import cached_property
from typing import Optional, TYPE_CHECKING

from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtCore import Qt, QEvent
from PyQt5.QtGui import QFont

if TYPE_CHECKING:
    from core.screen.screen import Screen
    from core.app.application import Application


class MainWindow(QMainWindow):
    """Главное окно приложения.
    
    Frameless-окно с прозрачным фоном. Центрируется на экране, 
    запускает Application и следит за сменой состояния окна
    (свёрнуто/развёрнуто) - чтобы обновлять иконку в хедере.

    Attributes:
        width: Ширина окна в пикселях.
        height: Высота окна в пикселях.
    """

    def __init__(self):
        """Создаёт главное окно и запускает Application.
        
        Устанавливает frameless-режим, прозрачный фон, размеры, 
        центрирует окно на мониторе и вызывает Application.start().
        """
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.width: int = 1000
        self.height: int = 600

        self.screen.center_window(self, self.width, self.height)
        self.application.start()
    
    @cached_property
    def screen(self) -> "Screen":
        """Ленивая инициализация Screen (работа с монитором).
        
        Импорт внутри свойства - чтобы избежать циклических
        зависимостей при старте.

        Returns:
            Экземпляр Screen.
        """
        from core.screen.screen import Screen
        return Screen()
    
    @cached_property
    def application(self) -> "Application":
        """Ленивая инициализация Application (центральный контроллер).
        
        Returns:
            Экземпляр Application с ссылкой на это окно как parent.
        """
        from core.app.application import Application
        return Application(parent=self)

    def changeEvent(self, event: Optional[QEvent]):
        """Реагирует на смену состояния окна (свёрнуто/развёрнуто).
        
        При изменении WindowState обновляет иконку кнопки
        разворачивания на хедере (maximize <-> restore).

        Args:
            event: Событие от Qt.
        """
        super().changeEvent(event)
        if event.type() == QEvent.WindowStateChange:
            header = self.application.frontend.header
            if hasattr(header, "_update_fullscreen_icon"):
                header._update_fullscreen_icon()

if __name__ == "__main__":
    app = QApplication(sys.argv)

    app.setStyleSheet("""
        QToolTip {
            background-color: #202124; 
            border: none; 
            border-radius: 4px; 
            color: white; 
            padding: 6px 10px; 
            font-family: Segoe UI; 
            font-size: 10pt; 
            opacity: 240;
        }
    """)

    font = app.font()
    font.setStyleStrategy(QFont.PreferAntialias)
    font.setHintingPreference(QFont.PreferNoHinting)
    app.setFont(font)

    window = MainWindow()
    window.show()

    sys.exit(app.exec_())
