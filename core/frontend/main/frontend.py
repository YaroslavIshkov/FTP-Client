# SPDX-FileCopyrightText: 2026 YaroslavIshkov
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""Сборка главного окна FTP-Client.

Класс Frontend создаёт всю иерархию виджетов: фон с тенью, 
шапку, форму подключения, панель файлов (локальное + сервер), 
прогресс-бар и статус-бар. Все виджеты собираются в один
вертикальный стек внутри QFrame с тенью.
"""

import textwrap
from typing import Optional
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QFrame, QHBoxLayout, 
    QProgressBar, QLabel)
from PyQt5.QtCore import Qt
from core.app.application import Application
from core.frontend.ui.styles.styles import WHITE_FRAME, apply_shadow


class Frontend:
    """Сборщик главного окна.
    
    Создаёт всю иерархию виджетов и расставляет их в layout'ах.
    Не содержит логики - только композицию. Все обработчики и
    состояние - в самих виджетах.

    Attributes:
        app: Ссылка на Application (центральный контроллер).
        central: Центральный QWidget окна.
        header: Шапка окна (иконка + название + кнопки).
        input: Форма подключения (хост, порт, логин, пароль).
        file_list: Панель с двумя списками (локальные + сервер).
        progress: Прогресс-бар для передачи файлов.
        status_label: Статус-строка внизу окна.
    """

    def __init__(self, app: Optional[Application] = None):
        """Создаёт сборщик UI.
        
        Args:
            app: Экземпляр Application - даёт доступ к UI, 
                состоянию и родительскому окну (app.parent).
        """
        self.app = app
    
    def layout_container(self):
        """Создаёт контейнеры и layout'ы без виджетов.
        
        Вызывается первым - создаёт central widget, главный frame
        с тенью и пять внутренних layout'ов. Сами виджеты создаются
        отдельно в init_ui().

        Структура layout'ов:
            inner_layout_2 - header
            inner_layout_3 - форма подключения
            inner_layout_4 - панель файлов
            inner_layout_5 - прогресс-бар + статус-бар
        """
        self.central = QWidget()
        self.app.parent.setCentralWidget(self.central)

        self.main_layout = QVBoxLayout(self.central)
        self.main_layout.setContentsMargins(20, 20, 30, 30)

        self.frame = QFrame()
        self.frame.setStyleSheet(WHITE_FRAME)
        apply_shadow(
            self.frame, 
            blur=30, 
            offset_x=8, 
            offset_y=8, 
            color=(0, 0, 0, 160)
        )
        self.main_layout.addWidget(self.frame)

        self.inner_layout_1 = QVBoxLayout(self.frame)
        self.inner_layout_1.setContentsMargins(5, 5, 5, 5)

        self.inner_layout_2 = QHBoxLayout()
        self.inner_layout_2.setContentsMargins(0, 0, 0, 0)

        self.inner_layout_3 = QHBoxLayout()
        self.inner_layout_3.setContentsMargins(0, 0, 0, 0)

        self.inner_layout_4 = QHBoxLayout()
        self.inner_layout_4.setContentsMargins(0, 0, 0, 0)

        self.inner_layout_5 = QVBoxLayout()
        self.inner_layout_5.setContentsMargins(0, 0, 0, 0)

        self.inner_layout_1.addLayout(self.inner_layout_2)
        self.inner_layout_1.addLayout(self.inner_layout_3)
        self.inner_layout_1.addLayout(self.inner_layout_4)
        self.inner_layout_1.addLayout(self.inner_layout_5)
    
    def init_ui(self):
        """Создаёт все виджеты и помещает их в layout'ы.
        
        Вызывается после layout_container(). Импорты виджетов - внутри метода, 
        чтобы избежать циклических зависимостей при старте приложения.
        """
        from core.frontend.ui.header.header import HeaderFrame
        from core.frontend.ui.input.input import InputFrame
        from core.frontend.ui.filelist.file_list import FileListFrame

        self.header = HeaderFrame(app=self.app)
        self.inner_layout_2.addWidget(self.header)

        self.input = InputFrame(app=self.app)
        self.inner_layout_3.addWidget(self.input)

        self.file_list = FileListFrame(app=self.app)
        self.inner_layout_4.addWidget(self.file_list, stretch=1)

        self.progress = QProgressBar()
        self.progress.setFixedHeight(6)
        self.progress.setTextVisible(False)
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setStyleSheet("""
            QProgressBar {
                background: #E8EAED; 
                border: none; 
                border-radius: 3px;
            }
            QProgressBar::chunk {
                background: #1A73E8; 
                border-radius: 3px;
            }
        """)
        self.progress.hide()
        self.inner_layout_5.addWidget(self.progress)

        self.status_label = QLabel()
        self.status_label.setText("Не подключено")
        self.status_label.setFixedHeight(24)
        self.status_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.status_label.setStyleSheet("""
            QLabel {
                background: transparent; 
                border: none; 
                color: #5F6368; 
                font-family: Segoe UI; 
                font-size: 11pt; 
                font-weight: 500; 
                padding-left: 10px; 
                padding-right: 10px;
            }
        """)
        self.inner_layout_5.addWidget(self.status_label)
    
    def set_status(self, text: str, kind: str = "info"):
        """Обновляет статус-бар.
        
        Текст обрезается до 100 символов с '...' в конце - чтобы
        длинные пути не растягивали окно. Цвет зависит от типа сообщения.

        Args:
            text: Текст статуса.
            kind: Тип сообщения - 'info' (серый), 'success' (зелёный), 
                'error' (красный), 'working' (синий). Если значение
                неизвестно - используется 'info'.
        """
        text = textwrap.shorten(text, width=100, placeholder="...")
        colors = {
            "info": "#5F6368", 
            "success": "#188038", 
            "error": "#D93025", 
            "working": "#1A73E8"
        }
        color = colors.get(kind, "#5F6368")
        self.status_label.setText(text)
        self.status_label.setStyleSheet(f"""
            QLabel {{
                background: transparent; 
                border: none; 
                color: {color}; 
                font-family: Segoe UI; 
                font-size: 11pt; 
                font-weight: 500; 
                padding-left: 10px; 
                padding-right: 10px;
            }}
        """)
