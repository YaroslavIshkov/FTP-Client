# SPDX-FileCopyrightText: 2026 YaroslavIshkov
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""Форма подключения к FTP-серверу.

Содержит поля ввода (хост, порт, логин, пароль) с валидацией:
- Хост: IPv4 или hostname, максимум 253 символа
- Порт: число 1-65535, максимум 5 цифр
- Логин: непустая строка, максимум 100 символов
- Пароль: до 100 символов, отображается точками

При некорректном вводе поле подсвечивается красным. Настройки подключения
(кроме пароля) сохраняются в QSettings.
"""

import re
from typing import Callable, Dict, Optional, Union
from PyQt5.QtWidgets import (QFrame, QLabel, QLineEdit, QPushButton, 
    QHBoxLayout, QVBoxLayout, QSizePolicy)
from PyQt5.QtGui import QRegExpValidator
from PyQt5.QtCore import Qt, QRegExp
from core.frontend.ui.styles.styles import (TRANSPARENT_FRAME, CONNECTION_BUTTON, 
    INPUT_LABEL, INPUT_LINE)
from core.app.application import Application


# Один октет IPv4 (0-255)
_OCTET = r"(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)"
_IPV4_RE = re.compile(rf"^{_OCTET}\.{_OCTET}\.{_OCTET}\.{_OCTET}$")

# Hostname: буквы, цифры, дефисы, точки
_HOSTNAME_RE = re.compile(
    r"^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?"
    r"(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$"
)

def is_valid_host(text: str) -> bool:
    """Проверяет, что строка - валидный IPv4 или hostname.
    
    Если строка состоит только из цифр и точек - проверяется как IP-адрес
    (строгая валидация: октеты < 255, без multicast и reserved).
    Иначе - как hostname.

    Args:
        text: Проверяемая строка.
    
    Returns:
        True, если можно использовать как адрес с сервера.
    """
    if not text:
        return False
    
    if all(c.isdigit() or c == "." for c in text):
        if not _IPV4_RE.match(text):
            return False
        if text in ("0.0.0.0", "255.255.255.255"):
            return False
        first = int(text.split(".")[0])
        if first >= 224: # multicast + reserved
            return False
        return True
    
    return bool(_HOSTNAME_RE.match(text))

def is_valid_port(text: str) -> bool:
    """Проверяет, что строка - валидный номер порта.
    
    Порт - число от 1 до 65535.

    Args:
        text: Проверяемая строка.
    
    Returns:
        True, если порт в допустимом диапазоне.
    """
    if not text or not text.isdigit():
        return False
    return 1 <= int(text) <= 65535

def is_valid_login(text: str) -> bool:
    """Проверяет, что логин непустой.
    
    Args:
        text: Проверяемая строка.
    
    Returns:
        True, если строка содержит хотя бы один
            непробельный символ.
    """
    return bool(text and text.strip())


class InputFrame(QFrame):
    """Форма подключения к FTP-серверу.
    
    Содержит четыре поля ввода и кнопку 'Подключить'. Каждое поле
    проверяется на лету через QRegExpValidator и функцию-валидатор.
    При успешном подключении параметры (кроме пароля) сохраняются
    в QSettings.

    Attributes:
        app: Ссылка на Application.
        host_entry: Поле для хоста.
        port_entry: Поле для порта.
        login_entry: Поле для логина.
        password_entry: Поле для пароля.
        connect_btn: Кнопка 'Подключить'.
    """

    def __init__(self, app: Optional[Application] = None):
        """Создаёт форму подключения.
        
        Args:
            app: Экземпляр Application (доступ к ftp_client и settings).
        """
        super().__init__()
        self.app = app
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setStyleSheet(TRANSPARENT_FRAME)

        self.outer_layout = QVBoxLayout(self)
        self.outer_layout.setContentsMargins(5, 5, 5, 5)
        self.outer_layout.setSpacing(8)

        self.host_entry = self._add_row(
            self.outer_layout, "Хост:", "192.168.43.1", 
            validator=is_valid_host, 
            max_length=253, 
            char_regex=r"[a-zA-Z0-9.\-]+",
        )
        self.port_entry = self._add_row(
            self.outer_layout, "Порт:", "2121", 
            validator=is_valid_port, 
            max_length=5, 
            char_regex=r"[0-9]+",
        )
        self.login_entry = self._add_row(
            self.outer_layout, "Логин:", "anonymous", 
            validator=is_valid_login, 
            max_length=100,
        )
        self.password_entry = self._add_row(
            self.outer_layout, "Пароль:", "", 
            max_length=100,
        )
        self.password_entry.setEchoMode(QLineEdit.Password)

        self.connect_btn = QPushButton()
        self.connect_btn.setText("Подключить")
        self.connect_btn.setToolTip("Подключить")
        self.connect_btn.setMinimumWidth(120)
        self.connect_btn.setCursor(Qt.PointingHandCursor)
        self.connect_btn.setStyleSheet(CONNECTION_BUTTON)
        self.connect_btn.clicked.connect(self.on_connect)

        self.button_layout = QHBoxLayout()
        self.button_layout.addStretch()
        self.button_layout.addWidget(self.connect_btn)
        self.outer_layout.addLayout(self.button_layout)
        self._load_saved_settings()
    
    def _set_invalid(self, entry: QLineEdit, invalid: bool):
        """Переключает красную подсветку поля.
        
        Через property + unpolish/polish - иначе Qt закеширует
        старое состояние QSS и цвет не изменится.

        Args:
            entry: Поле, которое надо подсветить/снять подсветку.
        """
        entry.setProperty("invalid", "true" if invalid else "false")
        entry.style().unpolish(entry)
        entry.style().polish(entry)
    
    def _add_row(self, 
                    layout: Union[QHBoxLayout, QVBoxLayout], 
                    label_text: str, 
                    default: str, 
                    validator: Optional[Callable[[str], bool]] = None, 
                    max_length: int = 0, 
                    char_regex: str = "") -> QLineEdit:
        """Создаёт строку 'метка + поле ввода' и добавляет её в layout.
        
        Args:
            layout: Куда добавить готовую строку.
            label_text: Текст метки ('Хост:', 'Порт:' и т.д).
            default: Значение по умолчанию в поле.
            validator: Функция (str) -> bool для подсветки невалидного.
            max_length: Максимальная длина строки (0 = без ограничений).
            char_regex: Regex допустимых символов (пусто = любые).
        
        Returns:
            Созданное поле QLineEdit.
        """
        row = QHBoxLayout()
        row.setSpacing(10)

        lbl = QLabel()
        lbl.setText(label_text)
        lbl.setMinimumWidth(90)
        lbl.setAlignment(Qt.AlignRight | Qt.AlignCenter)
        lbl.setStyleSheet(INPUT_LABEL)
        row.addWidget(lbl)

        entry = QLineEdit()
        entry.setText(default)
        entry.setFixedHeight(40)
        entry.setStyleSheet(INPUT_LINE)
        row.addWidget(entry, stretch=1)

        if max_length:
            entry.setMaxLength(max_length)
        
        if char_regex:
            entry.setValidator(QRegExpValidator(QRegExp(char_regex), entry))

        if validator:
            def on_change(text):
                if not text:
                    self._set_invalid(entry, False)
                else:
                    self._set_invalid(entry, not validator(text))
            entry.textChanged.connect(on_change)

        layout.addLayout(row)
        return entry
    
    def get_values(self) -> Dict[str, str]:
        """Возвращает словарь с текущими значениями всех полей.
        
        Returns:
            Словарь с ключами host, port, login, password.
        """
        return {
            "host": self.host_entry.text().strip(), 
            "port": self.port_entry.text().strip(), 
            "login": self.login_entry.text().strip(), 
            "password": self.password_entry.text().strip()
        }
    
    def on_connect(self):
        """Обрабатывает нажатие 'Подключить'.
        
        Валидирует хост и порт, подсвечивает невалидные поля.
        При успехе - подключается, сохраняет настройки, обновляет
        статус и список файлов сервера. При ошибке - показывает сообщение
        в статус-баре.
        """
        values = self.get_values()

        host_ok = is_valid_host(values["host"])
        port_ok = is_valid_port(values["port"])

        self._set_invalid(self.host_entry, not host_ok)
        self._set_invalid(self.port_entry, not port_ok)

        if not host_ok or not port_ok:
            self.app.frontend.set_status(
                text="[INPUT] Неверные данные - подключение отменено", 
                kind="error"
            )
            return
        
        try:
            welcome = self.app.ftp_client.connect(
                host=values["host"], 
                port=int(values["port"]), 
                login=values["login"] or "anonymous", 
                password=values["password"],
            )
            self._save_settings(values)
            self.app.frontend.set_status(
                text=f"[FTP] Подключение: {welcome}", 
                kind="success"
            )
            self.app.frontend.file_list.on_connected()
        except Exception as e:
            self.app.frontend.set_status(
                text=f"[FTP] Ошибка подключения: {e}", 
                kind="error"
            )
    
    def _load_saved_settings(self):
        """Загружает сохранённые параметры подключения из QSettings.
        
        Пароль не загружается (хранится только на время сессии).
        """
        s = self.app.settings
        host = s.value("connection/host", "192.168.43.1")
        port = s.value("connection/port", "2121")
        login = s.value("connection/login", "anonymous")

        self.host_entry.setText(host)
        self.port_entry.setText(port)
        self.login_entry.setText(login)
    
    def _save_settings(self, values: Dict[str, str]):
        """Сохраняет параметры подключения в QSettings.
        
        Пароль не сохраняется - из соображений безопасности.

        Args:
            values: Словарь с ключами host, port, login, password. 
                Пароль игнорируется.
        """
        s = self.app.settings
        s.setValue("connection/host", values["host"])
        s.setValue("connection/port", values["port"])
        s.setValue("connection/login", values["login"])
