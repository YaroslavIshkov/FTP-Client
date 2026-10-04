# SPDX-FileCopyrightText: 2026 YaroslavIshkov
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""Поток для выполнения операций передачи файлов по FTP.

Содержит класс TransferWorker, который запускает скачивание или
загрузку файла в отдельном потоке QThread и сообщает о прогрессе, 
успехе, ошибке или отмене через сигналы.
"""

from pathlib import Path
from typing import Optional
from PyQt5.QtCore import QThread, pyqtSignal
from core.backend.logic.ftp_client import FTPClient
from core.backend.logic.ftp_client import TransferCancelled


class TransferWorker(QThread):
    """Поток для асинхронной передачи файла.
    
    Запускает download_file или upload_file в отдельном потоке, 
    предоставляя сигналы для обновления интерфейса.

    Signals:
        progress (int, int): Передано байт и общий размер файла.
        finished_ok (str): Имя успешно переданного файла.
        failed (str): Текст ошибки при неудаче.
        cancelled (str): Имя файла, передача которого отменена.
    
    Attributes:
        ftp_client: Экземпляр FTPClient для выполнения операции.
        mode: Режим передачи - "download" или "upload".
        local_path: Локальный путь к файлу.
        remote_path: Путь к файлу на сервере.
        _cancelled: Флаг, установленный при запросе отмены.
    """

    progress = pyqtSignal(int, int)
    finished_ok = pyqtSignal(str)
    failed = pyqtSignal(str)
    cancelled = pyqtSignal(str)

    def __init__(self, 
                    ftp_client: Optional[FTPClient] = None, 
                    mode: str = "", 
                    local_path: Optional[Path] = None, 
                    remote_path: str = ""):
        """Инициализирует поток передачи.
        
        Args:
            ftp_client: Экземпляр FTPClient.
            mode: Режим передачи ("download" или "upload").
            local_path: Локальный путь к файлу.
            remote_path: Путь к файлу на сервере.
            parent: Родительский объект QObject (обычно None).
        """
        super().__init__()
        self.ftp_client = ftp_client
        self.mode = mode
        self.local_path = Path(local_path)
        self.remote_path = remote_path
        self._cancelled = False
    
    def cancel(self):
        """Запрашивает отмену передачи.
        
        Устанавливает флаг _cancelled. Сам процесс передачи проверяет
        этот флаг через _is_cancelled и прерывается.
        """
        self._cancelled = True
    
    def _is_cancelled(self) -> bool:
        """Возвращает текущее состояние флага отмены.
        
        Returns:
            True, если передача была отменена пользователем.
        """
        return self._cancelled
    
    def run(self):
        """Запускает передачу файла в отдельном потоке.
        
        В зависимости от режима вызывает download_file или upload_file, 
        передавая callback для прогресса и cancel_check для отмены.
        По завершении испускает соответствующий сигнал.
        """
        try:
            def on_progress(done, total):
                self.progress.emit(done, total)
            
            if self.mode == "download":
                self.ftp_client.download_file(
                    local_path=self.local_path, 
                    remote_path=self.remote_path, 
                    progress_callback=on_progress, 
                    cancel_check=self._is_cancelled,
                )
            elif self.mode == "upload":
                self.ftp_client.upload_file(
                    local_path=self.local_path, 
                    remote_path=self.remote_path, 
                    progress_callback=on_progress, 
                    cancel_check=self._is_cancelled
                )
            else:
                self.failed.emit(f"Неизвестный режим: {self.mode}")
                return
            
            self.finished_ok.emit(self.local_path.name)
        except TransferCancelled:
            self.cancelled.emit(self.local_path.name)
        except Exception as e:
            self.failed.emit(str(e))
