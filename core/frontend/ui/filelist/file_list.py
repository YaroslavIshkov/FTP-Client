# SPDX-FileCopyrightText: 2026 YaroslavIshkov
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""Панель файлов: локальные + сервер.

Содержит два QListWidget рядом (локальные файлы слева, 
файлы на FTP-сервере справа) и три кнопки переноса по центру.
Обработка скачивания и загрузки - через TransferWorker в
отдельном потоке.
"""

import posixpath
from pathlib import Path
from typing import Optional
from PyQt5.QtWidgets import (QFrame, QLabel, QListWidget, QPushButton, 
    QHBoxLayout, QVBoxLayout, QSizePolicy, QWidget, QListWidgetItem, QDialog)
from PyQt5.QtCore import Qt
from core.backend.logic.local_browser import LocalBrowser
from core.backend.logic.transfer_worker import TransferWorker
from core.frontend.ui.styles.styles import (LIST_WIDGET, TRANSPARENT_FRAME, 
    TITLE_LABEL, ACTION_BUTTON, CANCEL_BUTTON)
from core.app.application import Application


class FileListFrame(QFrame):
    """Панель с двумя списками файлов и кнопками переноса.
    
    Левая панель - локальная файловая система (через LocalBrowser).
    Правая - удалённый FTP-сервер (через Application.ftp_client).
    Кнопки по центру: скачать, загрузить, обновить (или отменить).

    Attributes:
        app: Ссылка на Application.
        local_panel: Словарь с элементами левой панели.
        local_browser: Логика навигации по локальной ФС.
        remote_panel: Словарь с элементами правой панели.
        remote_list: QListWidget файлов на сервере.
        remote_path: Текущая папка на сервере.
        download_path: Кнопка 'Скачать с сервера'.
        upload_btn: Кнопка 'Загрузить на север'.
        refresh_btn: Кнопка 'Обновить' (или 'Отменить' во время передачи).
        _transfer_active: True, пока идёт передача файла.
        _worker: Активный TransferWorker (или None).
    """

    def __init__(self, app: Optional[Application] = None):
        """Создаёт панель с двумя списками.
        
        Args:
            app: Экземпляр Application.
        """
        super().__init__()
        self.app = app
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setStyleSheet(TRANSPARENT_FRAME)

        self.outer_layout = QHBoxLayout(self)
        self.outer_layout.setContentsMargins(5, 10, 5, 5)
        self.outer_layout.setSpacing(10)

        self.local_panel = self._make_panel("Локальные файлы")
        self.local_list = self.local_panel["list"]
        self.outer_layout.addWidget(self.local_panel["frame"], stretch=1)

        self.local_list.setTextElideMode(Qt.ElideMiddle)
        self.local_list.setWordWrap(True)

        self.local_browser = LocalBrowser(
            list_widget=self.local_list, 
            app=self.app
        )
        self.local_browser.refresh()

        self.local_list.itemDoubleClicked.connect(self._on_local_double_click)

        self.middle_layout = QVBoxLayout()
        self.middle_layout.setContentsMargins(0, 0, 0, 0)
        self.middle_layout.setSpacing(10)
        self.middle_layout.addStretch()

        self.download_btn = self._make_action_btn("\u2190", "Скачать с сервера")
        self.upload_btn = self._make_action_btn("\u2192", "Загрузить на сервер")
        self.refresh_btn = self._make_action_btn("\u21BB", "Обновить")

        self.download_btn.clicked.connect(self.download_selected)
        self.upload_btn.clicked.connect(self.upload_selected)
        self.refresh_btn.clicked.connect(self._on_refresh_or_cancel)

        self.middle_layout.addWidget(self.download_btn, 
            alignment=Qt.AlignCenter)
        self.middle_layout.addWidget(self.upload_btn, 
            alignment=Qt.AlignCenter)
        self.middle_layout.addWidget(self.refresh_btn, 
            alignment=Qt.AlignCenter)
        self.middle_layout.addStretch()

        self.middle_widget = QWidget()
        self.middle_widget.setFixedWidth(80)
        self.middle_widget.setLayout(self.middle_layout)
        self.outer_layout.addWidget(self.middle_widget)

        self.remote_panel = self._make_panel("Файлы на сервере")
        self.remote_list = self.remote_panel["list"]
        self.outer_layout.addWidget(self.remote_panel["frame"], stretch=1)

        self.remote_list.setTextElideMode(Qt.ElideMiddle)
        self.remote_list.setWordWrap(True)

        self.remote_list.itemDoubleClicked.connect(self._on_remote_double_click)
        self.remote_path = "/"

        self._transfer_active = False
        self._worker = None
    
    def _make_panel(self, title: str) -> dict:
        """Создаёт панель со списком и заголовком.
        
        Args:
            title: Текст заголовка панели.
        
        Returns:
            Словарь с ключами frame (QFrame), title (QLabel), 
            list (QListWidget).
        """
        panel_layout = QVBoxLayout()
        panel_layout.setContentsMargins(0, 0, 0, 0)
        panel_layout.setSpacing(5)

        title_lbl = QLabel()
        title_lbl.setText(title)
        title_lbl.setFixedHeight(30)
        title_lbl.setAlignment(Qt.AlignLeft)
        title_lbl.setStyleSheet(TITLE_LABEL)
        panel_layout.addWidget(title_lbl)

        file_list = QListWidget()
        file_list.setStyleSheet(LIST_WIDGET)

        file_list.setMinimumWidth(0)
        file_list.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Expanding)
        file_list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        panel_layout.addWidget(file_list)

        panel = QFrame()
        panel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        panel.setLayout(panel_layout)

        return {"frame": panel, "title": title_lbl, "list": file_list}
    
    def _make_action_btn(self, text: str, tip: str) -> QPushButton:
        """Создаёт круглую кнопку действия.
        
        Args:
            text: Символ/иконка (юникод или буква).
            tip: Текст подсказки при наведении.
        
        Returns:
            Готовая кнопка QPushButton (50x50, синяя, круглая).
        """
        btn = QPushButton()
        btn.setText(text)
        btn.setToolTip(tip)
        btn.setFixedSize(50, 50)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet(ACTION_BUTTON)
        return btn
    
    def on_connected(self):
        """Обработчик успешного подключения к FTP.
        
        Устанавливает remote_path на начальную папку сервера
        и загружает список файйлов.
        """
        self.remote_path = self.app.ftp_client.initial_dir
        self.refresh_remote()
    
    def refresh_remote(self):
        """Обновляет список файлов на сервере.
        
        Читает содержимое self.remote_path через FTP, добавляет
        в начало '..', заполняет QlistWidget. При ошибке выводит
        её в статус-бар.
        """
        try:
            entries = self.app.ftp_client.list_dir(self.remote_path)
        except Exception as e:
            self.app.frontend.set_status(
                text=f"[FTP] Ошибка листинга: {e}", 
                kind="error"
            )
            return
        
        self.remote_list.clear()

        parent_item = QListWidgetItem("[Dir] ..")
        parent_item.setData(Qt.UserRole, "..")
        parent_item.setData(Qt.UserRole + 1, "dir")
        self.remote_list.addItem(parent_item)
        
        for name, kind in entries:
            prefix = "[Dir] " if kind == "dir" else "[File] "
            item = QListWidgetItem(f"{prefix}{name}")
            item.setData(Qt.UserRole, name)
            item.setData(Qt.UserRole + 1, kind)
            item.setToolTip(name)
            self.remote_list.addItem(item)
    
    def _on_remote_double_click(self, item: QListWidgetItem):
        """Обработчик двойного клика в правом списке.
        
        Файл - скачивает. Папка - переходит внутрь. '..' - 
        поднимается на уровень выше (не выше initial_dir).

        Args:
            item: Элемент списка, по которому кликнули.
        """
        name = item.data(Qt.UserRole)
        kind = item.data(Qt.UserRole + 1)

        if kind == "file":
            self.download_selected()
            return

        if kind != "dir":
            return
        
        if name == "..":
            if self.remote_path == self.app.ftp_client.initial_dir:
                return
            parent = posixpath.dirname(self.remote_path.rstrip("/"))
            if not parent:
                parent = "/"
            self.remote_path = parent
        else:
            self.remote_path = posixpath.join(self.remote_path, name)
        
        self.refresh_remote()
    
    def _on_local_double_click(self, item: QListWidgetItem):
        """Обработчик двойного клика в левом списке.
        
        Файл - загружает на сервер. Папка - открывает её
        через LocalBrowser.

        Args:
            item: Элемент списка, по которому кликнули.
        """
        path = item.data(Qt.UserRole)
        kind = item.data(Qt.UserRole + 1)

        if kind == "file":
            self.upload_selected()
            return
        
        if kind == "dir" and path:
            self.local_browser.navigate_to(path)
    
    def download_selected(self):
        """Скачивает выбранный файл с сервера.
        
        Проверяет: выбран ли файл, есть ли подключение, не занят ли
        канал. Спрашивает подтверждение перезаписи локального файла.
        Запускает TransferWorker в режиме download.
        """
        item = self.remote_list.currentItem()
        if item is None:
            self.app.frontend.set_status(
                text="[FTP] Не выбран файл на сервере", 
                kind="error"
            )
            return
        
        kind = item.data(Qt.UserRole + 1)
        if kind != "file":
            self.app.frontend.set_status(
                text="[FTP] Можно скачивать только файлы", 
                kind="error"
            )
            return
        
        if not self.app.ftp_client.connected:
            self.app.frontend.set_status(
                text="[FTP] Нет подключения к серверу", 
                kind="error"
            )
            return
        
        if self._transfer_active:
            self.app.frontend.set_status(
                text="Идёт передача файла", 
                kind="working"
            )
            return
        
        name = item.data(Qt.UserRole)
        remote_path = posixpath.join(self.remote_path, name)
        local_path = self.local_browser.current_path / name

        if not self._check_overwrite_local(local_path):
            self.app.frontend.set_status(text="Отменено", kind="info")
            return

        self._set_transfer_active(True)
        progress = self.app.frontend.progress
        progress.setValue(0)
        progress.show()
        self.app.frontend.set_status(
            text=f"[FTP] Скачивание {remote_path} \u2192 {local_path}", 
            kind="working"
        )

        worker = TransferWorker(
            ftp_client=self.app.ftp_client, 
            mode="download", 
            local_path=local_path, 
            remote_path=remote_path,
        )
        worker.progress.connect(
            lambda done, total: self._on_transfer_progress(done, total, name)
        )
        worker.finished_ok.connect(
            lambda n: self._on_download_done(n)
        )
        worker.failed.connect(
            lambda err: self._on_transfer_failed(err)
        )
        worker.cancelled.connect(
            lambda n: self._on_transfer_cancelled(n)
        )
        worker.finished.connect(worker.deleteLater)

        self._worker = worker
        worker.start()
    
    def upload_selected(self):
        """Загружает выбранный файл на сервер.
        
        Проверяет: выбран ли файл, есть ли подключение, не занят ли
        канал. Спрашивает подтверждение перезаписи файла на сервере.
        Запускает TransferWorker в режиме upload.
        """
        item = self.local_list.currentItem()
        if item is None:
            self.app.frontend.set_status(
                text="[FTP] Не выбран локальный файл", 
                kind="error"
            )
            return
        
        kind = item.data(Qt.UserRole + 1)
        if kind != "file":
            self.app.frontend.set_status(
                text="[FTP] Можно загружать только файлы", 
                kind="error"
            )
            return
        
        if not self.app.ftp_client.connected:
            self.app.frontend.set_status(
                text="[FTP] Нет подключения к серверу", 
                kind="error"
            )
            return
        
        if self._transfer_active:
            self.app.frontend.set_status(
                text="Идёт передача файла", 
                kind="working"
            )
            return
        
        local_path = item.data(Qt.UserRole)
        name = local_path.name
        remote_path = posixpath.join(self.remote_path, name)

        if not self._check_overwrite_remote(local_path):
            self.app.frontend.set_status(text="Отменено", kind="info")
            return

        self._set_transfer_active(True)
        progress = self.app.frontend.progress
        progress.setValue(0)
        progress.show()
        self.app.frontend.set_status(
            text=f"[FTP] Загрузка {local_path} \u2190 {remote_path}", 
            kind="working"
        )

        worker = TransferWorker(
            ftp_client=self.app.ftp_client, 
            mode="upload", 
            local_path=local_path, 
            remote_path=remote_path,
        )
        worker.progress.connect(
            lambda done, total: self._on_transfer_progress(done, total, name)
        )
        worker.finished_ok.connect(
            lambda n: self._on_upload_done(n)
        )
        worker.failed.connect(
            lambda err: self._on_transfer_failed(err)
        )
        worker.cancelled.connect(
            lambda n: self._on_transfer_cancelled(n)
        )
        worker.finished.connect(worker.deleteLater)

        self._worker = worker
        worker.start()
    
    def _set_transfer_active(self, active: bool):
        """Переключает режим 'идёт передача'.
        
        Во время передачи кнопки скачивания и загрузки блокируются, 
        а refresh превращается в красную кнопку 'X' для отмены.

        Args:
            active: True - началась передача, False - завершилась.
        """
        self._transfer_active = active
        self.download_btn.setEnabled(not active)
        self.upload_btn.setEnabled(not active)

        if active:
            self.refresh_btn.setText("X")
            self.refresh_btn.setToolTip("Отменить передачу")
            self.refresh_btn.setStyleSheet(CANCEL_BUTTON)
        else:
            self.refresh_btn.setText("\u21BB")
            self.refresh_btn.setToolTip("Обновить")
            self.refresh_btn.setStyleSheet(ACTION_BUTTON)
    
    def _on_transfer_progress(self, done: int, total: int, name: str):
        """Обновляет прогресс-бар во время передачи.
        
        Args:
            done: Сколько байт передано.
            total: Общий размер файла в байтах.
            name: Имя передаваемого файла.
        """
        if total > 0:
            percent = int(done * 100 / total)
            self.app.frontend.progress.setValue(percent)
            self.app.frontend.set_status(
                text=f"Передача: {name} - {percent}%", 
                kind="working"
            )
    
    def _on_download_done(self, name: str):
        """Обработчик успешного скачивания.
        
        Скрывает прогресс, показывает успех, обновляет локальный
        список файлов.

        Args:
            name: Имя скачанного файла.
        """
        self.app.frontend.progress.hide()
        self.app.frontend.progress.setValue(0)
        self.app.frontend.set_status(text=f"Скачано: {name}", kind="success")
        self._set_transfer_active(False)
        self.local_browser.refresh()
    
    def _on_upload_done(self, name: str):
        """Обработчик успешной загрузки.
        
        Скрывает прогресс, показывает успех, обновляет список файлов
        на сервере.

        Args:
            name: Имя загруженного файла.
        """
        self.app.frontend.progress.hide()
        self.app.frontend.progress.setValue(0)
        self.app.frontend.set_status(text=f"Загружено: {name}", kind="success")
        self._set_transfer_active(False)
        self.refresh_remote()
    
    def _on_transfer_failed(self, error: str):
        """Обработчик ошибки при передаче.
        
        Скрывает прогресс, показывает ошибку, разблокирует кнопки.

        Args:
            error: Текст ошибки.
        """
        self.app.frontend.progress.hide()
        self.app.frontend.progress.setValue(0)
        self.app.frontend.set_status(text=f"Ошибка: {error}", kind="error")
        self._set_transfer_active(False)
    
    def _on_transfer_cancelled(self, name: str):
        """Обработчик отмены передачи.
        
        Скрывает прогресс, разблокирует кнопки. Проверяет, живо ли
        FTP-соединение после abort - если нет, разрывает его и просит
        переподключаться.

        Args:
            name: Имя файла, передача которого была отменена.
        """
        self.app.frontend.progress.hide()
        self.app.frontend.progress.setValue(0)
        self._set_transfer_active(False)

        try:
            self.app.ftp_client.ftp.pwd()
            self.app.frontend.set_status(
                text=f"Отменено: {name}", 
                kind="error"
            )
        except Exception:
            try:
                self.app.ftp_client.disconnect()
            except Exception:
                pass
            self.app.frontend.set_status(
                text=f"Отменено: {name}. Переподключитесь.", 
                kind="error"
            )
    
    def _check_overwrite_local(self, local_path: Path) -> bool:
        """Спрашивает подтверждение перезаписи локального файла.
        
        Args:
            local_path: Путь к файлу, который может быть перезаписан.
        
        Returns:
            True, если можно перезаписать (файла нет или пользователь разрешил).
            False - если отменил.
        """
        from core.frontend.ui.dialogs.overwrite_dialog import OverwriteDialog

        local_path = Path(local_path)
        if not local_path.exists():
            return True
        
        dialog = OverwriteDialog(
            parent=self.window(), 
            filename=local_path.name,
        )
        result = dialog.exec_()
        return result == QDialog.Accepted
    
    def _check_overwrite_remote(self, remote_path: str) -> bool:
        """Спрашивает подтверждение перезаписи файла на сервере.
        
        Проверяет наличие файла через FTP.size(). Если размер
        получен - файл есть, спрашивает подтверждение.

        Args:
            remote_path: Путь к файлу на сервере.
        
        Returns:
            True, если можно перезаписать. False - если отменил.
        """
        from core.frontend.ui.dialogs.overwrite_dialog import OverwriteDialog

        try:
            size = self.app.ftp_client.ftp.size(remote_path)
            if size is None:
                return True
        except Exception:
            return True
        
        dialog = OverwriteDialog(
            parent=self.window(), 
            filename=remote_path.split("/")[-1],
        )
        result = dialog.exec_()
        return result == QDialog.Accepted
    
    def _on_refresh_or_cancel(self):
        """Единый обработчик кнопки refresh/cancel.
        
        Если передача активна - отменяет. Иначе - обновляет список
        файлов на сервере.
        """
        if self._transfer_active:
            self._cancel_transfer()
        else:
            self.refresh_remote()
    
    def _cancel_transfer(self):
        """Запрашивает отмену активной передачи через воркер."""
        if self._worker and self._worker.isRunning():
            self._worker.cancel()
            self.app.frontend.set_status(
                text="Отмена передачи...", 
                kind="working"
            )
