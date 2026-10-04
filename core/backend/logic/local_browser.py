# SPDX-FileCopyrightText: 2026 YaroslavIshkov
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""Модуль локального файлового браузера.

Содержит класс LocalBrowser, который отображает содержимое локальной
файловой системы в QListWidget и позволяет переходить между каталогами.
"""

from pathlib import Path
from typing import Optional
from PyQt5.QtWidgets import QListWidget, QListWidgetItem
from PyQt5.QtCore import Qt
from core.app.application import Application


class LocalBrowser:
    """Браузер локальной файловой системы.
    
    Отвечает за отображение содержимого текущего каталога в QListWidget, 
    навигацию по каталогам и обработку ошибок доступа.

    Attributes:
        list_widget: Виджет списка, в котором отображаются элементы каталога.
        app: Экземпляр Application.
    """

    def __init__(self, 
                    list_widget: Optional[QListWidget] = None, 
                    app: Optional[Application] = None):
        """Инициализирует экземпляр LocalBrowser.
        
        Args:
            list_widget: QListWidget для отображения содержимого каталога.
                Может быть None, если виджет будет установлен похже.
            app: Ссылка на Application.
        """
        self.list_widget = list_widget
        self.app = app
        self.current_path = Path.home()
    
    def refresh(self):
        """Обновляет содержимое виджета списка для текущего каталога.
        
        Очищает список, добавляет пункт перехода в родительский каталог
        (если текущий каталог не является корнем), затем добавляет
        подкаталоги и файлы, отсортированные по имени без учёта регистра.

        Для каждого элемента сохраняет:
            Qt.UserRole: Path - полный путь к элементу;
            Qt.UserRole + 1: str - тип элемента ("dir" или "file").
        
        При ошибках доступа к каталогу выводит сообщение через
        self.app.frontend.set_status и завершает обновление.

        Note:
            Если self.list_widget равен None, при вызове метода возникнет
            AttributeError. Если self.app равен None, при ошибке доступа
            также возникает AttributeError при обращении к frontend.
        """
        self.list_widget.clear()
        if self.current_path.parent != self.current_path:
            parent_item = QListWidgetItem("[Dir]..")
            parent_item.setData(Qt.UserRole, self.current_path.parent)
            parent_item.setData(Qt.UserRole + 1, "dir")
            self.list_widget.addItem(parent_item)
        
        try:
            entries = list(self.current_path.iterdir())
        except PermissionError:
            self.app.frontend.set_status(
                text=f"[LOCAL] Нет доступа: {self.current_path}", 
                kind="error"
            )
            return
        except OSError as e:
            self.app.frontend.set_status(
                text=f"[LOCAL] Ошибка: {e}", 
                kind="error"
            )
            return
        
        dirs = sorted(
            (p for p in entries if p.is_dir()), 
            key=lambda p: p.name.lower()
        )
        files = sorted(
            (p for p in entries if p.is_file()), 
            key=lambda p: p.name.lower()
        )

        for d in dirs:
            item = QListWidgetItem(f"[Dir] {d.name}")
            item.setData(Qt.UserRole, d)
            item.setData(Qt.UserRole + 1, "dir")
            item.setToolTip(str(d))
            self.list_widget.addItem(item)
        
        for f in files:
            item = QListWidgetItem(f"[File] {f.name}")
            item.setData(Qt.UserRole, f)
            item.setData(Qt.UserRole + 1, "file")
            item.setToolTip(str(f))
            self.list_widget.addItem(item)
    
    def navigate_to(self, path: Path):
        """Переходит в указанный каталог и обновляет список.
        
        Если path существует и является каталогом, обновляет current_path
        и вызывает refresh(). В противном случае ничего не делает.

        Args:
            path: Путь к каталогу, в который нужно перейти.
        """
        if path.exists() and path.is_dir():
            self.current_path = path
            self.refresh()
