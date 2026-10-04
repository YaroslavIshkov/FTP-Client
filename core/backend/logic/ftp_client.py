# SPDX-FileCopyrightText: 2026 YaroslavIshkov
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""Обёртка над ftplib для работы с FTP-сервером.

Класс FTPClient инкапсулирует подключение, навигацию по каталогом, 
скачивание и загрузку файлов. Все методы бросают ConnectionError
при ошибках сети, чтобы UI мог показать понятное сообщение.
Передача поддерживает отмену через cancel_check.
"""

import ftplib
from pathlib import Path
from typing import Callable, List, Optional, Tuple


class TransferCancelled(Exception):
    """Передача отменена пользователем.
    
    Бросается из callback-функций внутри download_file/upload_file, 
    когда cancel_check возвращает True.
    """
    pass


class FTPClient:
    """Обёртка над ftplib с упрощённым API.
    
    Хранит состояние подключения (host, port, initial_dir), 
    предоставляет методы для листинга, скачивания и загрузки.
    Кодировка - UTF-8, чтобы корректно работали русские имена.

    Attributes:
        ftp: Объект ftplib.FTP (None, если нет подключения).
        connect: True, если подключение активно.
        host: Адрес сервера.
        port: Порт сервера.
        initial_dir: Папка, в которую сервер пускает после логина.
    """

    def __init__(self):
        """Создаёт клиент без подключения."""
        self.ftp: Optional[ftplib.FTP] = None
        self.connected = False
        self.host = ""
        self.port = 0
        self.initial_dir = "/"
    
    def connect(self, 
                    host: str, 
                    port: int, 
                    login: str, 
                    password: str, 
                    timeout: int = 10) -> str:
        """Подключается к FTP-серверу и логинится.
        
        Включает UTF-8 (если сервер поддерживает OPTS UTF8 ON), сохраняет
        initial_dir - папку, в которую сервер пускает после логина
        (у разных серверов она разная).

        Args:
            host: Адрес сервера (IP или hostname).
            port: Порт (обычно 21 или 2121).
            login: Логин ('anonymous' для анонимного доступа).
            password: Пароль (для анонимного любой).
            timeout: Таймаут подключения в секундах.
        
        Returns:
            Приветственное сообщение сервера (get welcome).
        
        Raises:
            ConnectionError: При таймауте, отказе подключения, 
                неверных учётных данных или сетевой ошибке.
        """
        self.ftp = ftplib.FTP()
        self.ftp.encoding = "utf-8"

        try:
            self.ftp.connect(host, port, timeout=timeout)
        except TimeoutError:
            raise ConnectionError(
                f"Сервер {host}:{port} не отвечает. "
                f"Проверьте, что ноутбук или компьютер подключён к точке доступа смартфона."
            )
        except ConnectionRefusedError:
            raise ConnectionError(
                f"Сервер {host}:{port} отклонил соединение. "
                f"Возможно, FTP не запущен или порт не соответствует."
            )
        except OSError as e:
            raise ConnectionError(f"Сетевая ошибка: {e}")
        
        try:
            self.ftp.login(login, password)
        except ftplib.error_perm as e:
            raise ConnectionError(f"Ошибка авторизации: {e}")

        try:
            self.ftp.sendcmd("OPTS UTF8 ON")
        except ftplib.all_errors:
            pass

        self.initial_dir = self.ftp.pwd() or "/"

        self.connected = True
        self.host = host
        self.port = port
        return self.ftp.getwelcome()
    
    def disconnect(self):
        """Закрывает соединение.
        
        Пытается вежливо попрощаться через quit(), при ошибке - 
        закрывает сокет напрямую. Сбрасывает флаг connected.
        """
        if self.ftp:
            try:
                self.ftp.quit()
            except Exception:
                try:
                    self.ftp.close()
                except Exception:
                    pass
        self.ftp = None
        self.connected = False
    
    def list_dir(self, path: Optional[str] = None) -> List[Tuple[str, str]]:
        """Возвращает содержимое папки на сервере.
        
        Сначала пробует современный формат MLSD (машиночитаемый), 
        если сервер его не поддерживает - откатывается на LIST
        (парсит права доступа как в Unix).

        Args:
            path: Путь к папке. Если None - используется текущая.
        
        Returns:
            Список кортежей (имя, тип), где тип - 'dir' или 'file'.
        
        Raises:
            ConnectionError: Если нет подключения или не удалось перейти
                в указанную папку.
        """
        if not self.connected:
            raise ConnectionError("Нет подключения к FTP")
        
        if path is not None:
            try:
                self.ftp.cwd(path)
            except ftplib.all_errors as e:
                raise ConnectionError(f"Не удалось перейти в {path}: {e}")
        
        entries: List[Tuple[str, str]] = []

        # 1. Пробуем MLSD (современный формат)
        try:
            for name, facts in self.ftp.mlsd():
                if name in (".", ".."):
                    continue
                kind = "dir" if facts.get("type") == "dir" else "file"
                entries.append((name, kind))
            return entries
        except ftplib.all_errors:
            pass

        # 2. Fallback: LIST (старый формат, парсим вручную)
        lines: List[str] = []
        self.ftp.retrlines("LIST", lines.append)
        for line in lines:
            parts = line.split(maxsplit=8)
            if len(parts) < 9:
                continue
            permissions = parts[0]
            name = parts[8]
            if name in (".", ".."):
                continue
            kind = "dir" if permissions.startswith("d") else "file"
            entries.append((name, kind))
        
        return entries
    
    def current_dir(self) -> str:
        """Возвращает путь к текущей папке на сервере.
        
        Returns:
            Путь в формате POSIX ('/sdcard/Music'). При ошибке - '/'
        """
        if not self.connected:
            return "/"
        try:
            return self.ftp.pwd()
        except ftplib.all_errors:
            return "/"
    
    def download_file(self, 
                            remote_path: str, 
                            local_path: Path, 
                            progress_callback: Optional[Callable[[int, int], None]] = None, 
                            cancel_check: Optional[Callable[[], bool]] = None) -> Optional[Path]:
        """Скачивает файл с FTP-сервера.
        
        При отмене или ошибке удаляет недокачанный локальный файл.
        Прогресс передаётся через callback на каждый чанк (8 КБ).

        Args:
            remote_path: Путь к файлу на сервере.
            local_path: Куда сохранить локально.
            progress_callback: Функция (downloaded, total) для
                отображения прогресса. Может быть None.
            cancel_check: Функция () -> bool, возвращающая True, 
                если передачу надо прервать. Может быть None.
        
        Returns:
            Путь к скачанному файлу или None.
        
        Raises:
            ConnectionError: Если нет подключения или ошибка сети.
            TransferCancelled: Если cancel_check вернул True.
        """
        if not self.connected:
            raise ConnectionError("Нет подключения к FTP")
        
        local_path = Path(local_path)
        local_path.parent.mkdir(parents=True, exist_ok=True)

        total_size = 0
        try:
            total_size = self.ftp.size(remote_path) or 0
        except ftplib.all_errors:
            pass

        downloaded = 0

        def handle_chunk(chunk: bytes):
            nonlocal downloaded
            if cancel_check and cancel_check():
                raise TransferCancelled()
            f.write(chunk)
            downloaded += len(chunk)
            if progress_callback and total_size:
                progress_callback(downloaded, total_size)
        
        try:
            with open(local_path, "wb") as f:
                self.ftp.retrbinary(f"RETR {remote_path}", handle_chunk)
        except TransferCancelled:
            # Отмена - удаляем недокачанный файл
            if local_path.exists():
                try:
                    local_path.unlink()
                except OSError:
                    pass
            raise
        except ftplib.all_errors as e:
            # Ошибка сети - тоже чистим
            if local_path.exists():
                try:
                    local_path.unlink()
                except OSError:
                    pass
            raise ConnectionError(f"Ошибка скачивания: {e}")
        
        return local_path
    
    def upload_file(self, 
                        local_path: Path, 
                        remote_path: str, 
                        progress_callback: Optional[Callable[[int, int], None]] = None, 
                        cancel_check: Optional[Callable[[], bool]] = None) -> str:
        """Загружает файл на FTP-сервер.
        
        Оборачивает файл в CancelReader - чтобы можно было прервать
        передачу при отмене. При отмене пытается удалить частично
        загруженный файл на сервере.

        Args:
            local_path: Путь к локальному файлу.
            remote_path: Куда положить на сервере.
            progress_callback: Функция (uploaded, total). Может быть None.
            cancel_check: Функция () -> bool для отмены. Может быть None.
        
        Returns:
            Путь к загруженному файлу на сервере (remote_path).
        
        Raises:
            ConnectionError: Если нет подключения или ошибка сети.
            FileNotFoundError: Если локальный файл не найден.
            TransferCancelled: Если cancel_check вернул True.
        """
        if not self.connected:
            raise ConnectionError("Нет подключения к FTP")
        
        local_path = Path(local_path)
        if not local_path.exists() or not local_path.is_file():
            raise FileNotFoundError(f"Файл не найден: {local_path}")
        
        total_size = local_path.stat().st_size
        uploaded = 0

        class CancelReader:
            """Обёртка над файлом - проверяет отмену при каждом read().
            
            ftplib.storbinary сам читает из файла, поэтому
            единственный способ прервать передачу - бросить
            исключение из read().
            """
            def __init__(self, f, check):
                self._f = f
                self._check = check

            def read(self, size=-1):
                if self._check and self._check():
                    raise TransferCancelled()
                chunk = self._f.read(size)
                nonlocal uploaded
                uploaded += len(chunk)
                if progress_callback and total_size:
                    progress_callback(uploaded, total_size)
                return chunk
            
            def __getattr__(self, name):
                return getattr(self._f, name)
        
        try:
            with open(local_path, "rb") as f:
                reader = CancelReader(f, cancel_check)
                self.ftp.storbinary(f"STOR {remote_path}", reader)
        except TransferCancelled:
            # Пытаемся убрать частично загруженный файл с сервера
            try:
                self.ftp.delete(remote_path)
            except ftplib.all_errors:
                pass
            raise
        except ftplib.all_errors as e:
            raise ConnectionError(f"Ошибка загрузки: {e}")
        
        return remote_path
