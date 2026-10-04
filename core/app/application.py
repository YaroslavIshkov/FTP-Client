# SPDX-FileCopyrightText: 2026 YaroslavIshkov
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""Центральный контроллер FTP-Client.

Класс Application связывает вместе UI (Frontend), FTP-клиент и
настройки QSettings. Предоставляет ленивую инициализацию подсистем
и методы для поиска корня проекта и загрузки кнопок хедера.
"""

import sys
from pathlib import Path
from functools import cached_property
from typing import Optional, TYPE_CHECKING

from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import QSettings

if TYPE_CHECKING:
    from core.frontend.main.frontend import Frontend
    from core.backend.logic.ftp_client import FTPClient
    from PyQt5.QtCore import QSettings


class Application:
    """Центральный контроллер приложения.
    
    Хранит пути к ресурсам, создаёт UI через Frontend, управляет
    FTP-клиентом и настройками. Всё создаётся лениво - при первом
    обращении к соответствующему свойству.

    Attributes:
        parent: Родительское окно (MainWindow).
        PROJECT_ROOT: Корень проекта (папка с main.py).
        ICONS_PATH: Папка с иконками.
        HEADER_PATH: Папка с иконками хедера.
    """

    def __init__(self, parent: Optional[QMainWindow] = None):
        """Инициализирует контроллер.
        
        Args:
            parent: Родительское окно (обычно MainWindow).
        """
        self.parent = parent

        self.PROJECT_ROOT = self._find_project_root()
        self.ICONS_PATH = self.PROJECT_ROOT / "icons"
        self.HEADER_PATH = self.ICONS_PATH / "header"
    
    @staticmethod
    def _find_project_root() -> Optional[Path]:
        """Ищет корень проекта по маркеру main.py.
        
        В обычном режиме (Python) - поднимается вверх по дереву
        директорий, пока не найдёт папку с main.py.
        В .exe (frozen) - возвращает папку рядом с 
        исполняемым файлом.

        Returns:
            Путь к корню проекта.
        """
        if getattr(sys, 'frozen', False):
            base = getattr(sys, '_MEIPASS', None)
            if base:
                return Path(base)
            
            return Path(sys.executable).resolve().parent

        current = Path(__file__).resolve()
        for parent in [current, *current.parents]:
            if (parent / "main.py").exists():
                return parent
        return Path(__file__).resolve().parents[2]
    
    def get_header_icon(self, name: str) -> QPixmap:
        """Загружает иконку хедера по имени.
        
        Доступные имена: 'minimize' | 'maximize' | 'restore' | 'close'.
        Если файл не найден - возвращает пустой QPixmap и пишет предупреждение
        в статус-бар.

        Args:
            name: Имя иконки без расширения.
        
        Returns:
            QPixmap с иконкой или пустой QPixmap при ошибке.
        """
        path = self.HEADER_PATH / f"{name}.png"
        if not path.exists():
            try:
                self.frontend.set_status(
                    text=f"[WARN] Спрайт не найден: {path}", 
                    kind="info"
                )
            except Exception:
                pass
            return QPixmap()
        return QPixmap(str(path))
    
    def start(self):
        """Запускает приложение: создаёт layout и инициализирует UI.
        
        Вызывается один раз при старте MainWindow.
        """
        self.frontend.layout_container()
        self.frontend.init_ui()
    
    @cached_property
    def frontend(self) -> "Frontend":
        """Ленивая инициализация Frontend (всё UI приложения).
        
        Импорт внутри свойства - чтобы избежать циклических зависимостей
        при старте.

        Returns:
            Экземпляр Frontend.
        """
        from core.frontend.main.frontend import Frontend
        return Frontend(app=self)
    
    @cached_property
    def ftp_client(self) -> "FTPClient":
        """Ленивая инициализация FTP-клиента.
        
        Returns:
            Экземпляр FTPClient.
        """
        from core.backend.logic.ftp_client import FTPClient
        return FTPClient()
    
    @cached_property
    def settings(self) -> "QSettings":
        """Ленивая инициализация QSettings.
        
        Путь зависит от режима запуска:
            - .py - файл config/settings.ini в корне проекта
            - .exe - файл config/settings.ini рядом с exe
        
        Returns:
            Экземпляр QSettings, привязанный к файлу на диске.
        """
        if getattr(sys, 'frozen', False):
            base = Path(sys.executable).parent
        else:
            base = self.PROJECT_ROOT
        
        settings_path = base / "config" / "settings.ini"
        settings_path.parent.mkdir(parents=True, exist_ok=True)
        return QSettings(str(settings_path), QSettings.IniFormat)
