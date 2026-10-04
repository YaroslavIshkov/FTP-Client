# SPDX-FileCopyrightText: 2026 YaroslavIshkov
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""Стили и вспомогательные функции для оформления интерфейса.

Содержит QSS-строки для различных виджетов (фреймы, кнопки, списки, поля ввода)
и функцию apply_shadow для наложения тени.
"""

from typing import Tuple
from PyQt5.QtWidgets import QGraphicsDropShadowEffect, QWidget
from PyQt5.QtGui import QColor

WHITE_FRAME = """
    QFrame {
        background: white; 
        border: none; 
        border-radius: 4px;
    }
"""

TRANSPARENT_LABEL = """
    QLabel {
        background: transparent; 
        border: none; 
        color: black; 
        font-family: Segoe UI; 
        font-size: 14pt; 
        font-weight: 500;
    }
"""

TRANSPARENT_BUTTON = """
    QPushButton {
        background: transparent; 
        border: none; 
        border-radius: 5px; 
        color: black; 
        font-family: Segoe UI; 
        font-size: 14pt; 
        font-weight: 400;
    }
    QPushButton::hover {
        background: #DADADA;
    }
"""

LIST_WIDGET = """
    QListWidget {
        background: white; 
        border: 2px solid #DADCE0; 
        border-radius: 4px; 
        color: #202124; 
        font-family: Segoe UI Emoji; 
        font-size: 10pt; 
        font-weight: 500; 
        outline: 0; 
        padding: 4px 4px 4px 4px;
    }
    QListWidget::item {
        padding: 4px 8px; 
        margin-right: 4px; 
        border-radius: 4px;
    }
    QListWidget::item:hover {
        background: #1765CC; 
        color: white;
    }
    QListWidget::item:selected {
        background: #D2E3FC; 
        color: #0D47A1;
    }
    QListWidget QScrollBar:vertical {
        background: transparent; 
        width: 8px; 
        margin: 0;
    }
    QListWidget QScrollBar::handle:vertical {
        background: #DADCE0; 
        border-radius: 4px; 
        min-height: 30px;
    }
    QListWidget QScrollBar::handle:vertical:hover {
        background: #BDC1C6;
    }
    QListWidget QScrollBar::add-line:vertical, 
    QListWidget QScrollBar::sub-line:vertical {
        height: 0;
    }
    QListWidget QScrollBar::add-page:vertical, 
    QListWidget QScrollBar::sub-page:vertical {
        background: transparent;
    }
    QListWidget QScrollBar:horizontal {
        background: transparent; 
        height: 8px; 
        margin: 0;
    }
    QListWidget QScrollBar::handle:horizontal {
        background: #DADCE0; 
        border-radius: 4px; 
        min-height: 30px;
    }
    QListWidget QScrollBar::handle:horizontal:hover {
        background: #BDC1C6;
    }
    QListWidget QScrollBar::add-line:horizontal, 
    QListWidget QScrollBar::sub-line:horizontal {
        height: 0;
    }
    QListWidget QScrollBar::add-page:horizontal, 
    QListWidget QScrollBar::sub-page:horizontal {
        background: transparent;
    }
"""

TRANSPARENT_FRAME = """
    FileListFrame {
        background: transparent; 
        border: none;
    }
"""

TITLE_LABEL = """
    QLabel {
        background: #F8F9FA; 
        border: none; 
        border-left: 3px solid #1A73E8; 
        border-radius: 0px; 
        color: #202124; 
        font-family: Segoe UI; 
        font-size: 11pt; 
        font-weight: 600; 
        padding-left: 10px;
    }
"""

ACTION_BUTTON = """
    QPushButton {
        background: #1A73E8; 
        border: none; 
        border-radius: 25px; 
        color: white; 
        font-family: Segoe UI; 
        font-size: 18pt; 
        font-weight: 700;
    }
    QPushButton:hover {
        background: #1765CC;
    }
    QPushButton:pressed {
        background: #0D47A1;
    }
    QPushButton:disabled {
        background: #E8EAED; 
        color: #9AA0A6;
    }
"""

HEADER_LABEL = """
    QLabel {
        background: #DADADA; 
        border: none; 
        border-radius: 5px; 
        color: black; 
        font-family: Segoe UI; 
        font-size: 25px; 
        padding-left: 10px; 
        padding-right: 10px;
    }
"""

HEADER_BUTTON = """
    QPushButton {
        background: transparent; 
        border: none; 
        border-radius: 4px;
    }

    QPushButton::hover {
        background: #DADADA;
    }
"""

CONNECTION_BUTTON = """
    QPushButton {
        background: #1A73E8; 
        border: none; 
        border-radius: 4px; 
        color: white; 
        font-family: Segoe UI; 
        font-size: 11pt; 
        font-weight: 500; 
        padding: 6px 20px;
    }

    QPushButton::hover {
        background: #1765CC;
    }

    QPushButton::pressed {
        background: #0D47A1;
    }

    QPushButton:disabled {
        background: #E8EAED; 
        color: #9AA0A6;
    }
"""

CANCEL_BUTTON = """
    QPushButton {
        background: #D93025; 
        border: none; 
        border-radius: 25px; 
        color: white; 
        font-family: Segoe UI; 
        font-size: 18pt; 
        font-weight: 700;
    }

    QPushButton::hover {
        background: #B3261E;
    }

    QPushButton::pressed {
        background: #8A1C14;
    }
"""

INPUT_LABEL = """
    QLabel {
        background: transparent; 
        border: none; 
        border-radius: 5px; 
        color: #202124; 
        font-family: Segoe UI; 
        font-size: 11pt; 
        font-weight: 500; 
        padding-left: 10px; 
        padding-right: 10px;
    }
"""

INPUT_LINE = """
    QLineEdit {
        background: #E8EAED; 
        border: none; 
        border-bottom: 2px solid #C0C4C8; 
        border-radius: 6px 6px 0 0; 
        color: #202124; 
        font-family: Segoe UI; 
        font-size: 11pt; 
        font-weight: 500; 
        padding: 6px 10px;
    }
    QLineEdit:focus {
        border-bottom: 2px solid #1A73E8; 
        background: #E8F0FE;
    }
    QLineEdit[invalid="true"] {
        background: #FCE8E6; 
        border-bottom: 2px solid #D93025;
    }
    QLineEdit[invalid="true"]:focus {
        background: #FAD2CF; 
        border-bottom: 2px solid #D93025;
    }
    QLineEdit::placeholder {
        color: #5F6368;
    }
"""

SHADOW_MARGIN = 25

def apply_shadow(
                widget: QWidget, 
                blur: int = 30, 
                offset_x: int = 0, 
                offset_y: int = 0, 
                color: Tuple[int, int, int, int] = (0, 0, 0, 120), 
                margin: int = SHADOW_MARGIN) -> int:
    """Накладывает мягкую тень на виджет через QGraphicsDropShadowEffect.
    
    Args:
        widget: Виджет (обычно QFrame), на который накладывается тень.
        blur: Радиус размытия в пикселях (больше - мягче).
        offset_x: Смещение тени по x.
        offset_y: Смещение тени по y.
        color: RGBA-кортеж цвета тени.
        margin: Отступ под тень (для setContentsMargins у родителя).
    
    Returns:
        margin - чтобы использовать в setContentsMargins без повторного ввода.
    """
    shadow = QGraphicsDropShadowEffect()
    shadow.setBlurRadius(blur)
    shadow.setOffset(offset_x, offset_y)
    shadow.setColor(QColor(*color))
    widget.setGraphicsEffect(shadow)

    return margin
