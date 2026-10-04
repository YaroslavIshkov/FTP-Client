# SPDX-FileCopyrightText: 2026 YaroslavIshkov
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""Работа с монитором: определение размера и центрирование окна.

Содержит класс Screen, который получает разрешение основного
монитора (через screeninfo или QApplication) и центрирует
переданное окно.
"""

from typing import Optional, Tuple
from screeninfo import get_monitors
from PyQt5.QtWidgets import QApplication, QMainWindow


class Screen:
    """Утилита для работы с параметрами экрана.
    
    Определяет размер монитора и центрирует окно приложения.
    """
    
    def __init__(self):
        """Создаёт экземпляр Screen."""
        pass

    def get_monitor_size(self) -> Tuple[int, int]:
        """Возвращает ширину и высоту основного монитора.
        
        Сначала пытается получить размер через screeninfo.get_monitors().
        При ошибке использует QApplication.primaryScreen().size().

        Returns:
            Кортеж (ширина, высота) в пикселях.
        """
        try:
            monitor = get_monitors()[0]
            monitor_width = monitor.width
            monitor_height = monitor.height
            return monitor_width, monitor_height
        except Exception:
            monitor = QApplication.primaryScreen().size()
            monitor_width = monitor.width
            monitor_height = monitor.height
            return monitor_width, monitor_height
    
    def center_window(self, 
                        window: Optional[QMainWindow] = None, 
                        width: int = 0, 
                        height: int = 0):
        """Центрирует окно на экране с заданными размерами.

        Вычисляет координаты так, чтобы окно оказалось в центре монитора, 
        и устанавливает их через setGeometry.
        
        Args:
            window: Окно QMainWindow, которое нужно центрировать.
            width: Ширина окна в пикселях.
            height: Высота окна в пикселях.
        """
        monitor_width, monitor_height = self.get_monitor_size()
        x = max(0, (monitor_width // 2) - (width // 2))
        y = max(0, (monitor_height // 2) - (height // 2))
        window.setGeometry(x, y, width, height)