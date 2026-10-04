# SPDX-FileCopyrightText: 2026 YaroslavIshkov
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""Генератор иконок для хедера FTP-Client.

Запускается один раз. Создаёт PNG с прозрачным фоном:
  - minimize.png
  - maximize.png  (один квадрат)
  - restore.png   (два квадрата, для развёрнутого окна)
  - close.png

Сохраняет в icons/sprites/header/ рядом с проектом.
"""

from pathlib import Path
from PIL import Image, ImageDraw


# === Настройки ===
SIZE = 128            # размер холста (потом масштабируется до 50x50)
STROKE = 8            # толщина линий
MARGIN = 28           # отступ от края холста
COLOR = (0, 0, 0, 255)  # чёрный непрозрачный


def new_canvas():
    """Создаёт прозрачный холст."""
    return Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))


def make_minimize():
    """Горизонтальная черта."""
    img = new_canvas()
    draw = ImageDraw.Draw(img)
    y = SIZE // 2
    draw.line(
        [(MARGIN, y), (SIZE - MARGIN, y)],
        fill=COLOR,
        width=STROKE,
    )
    return img


def make_maximize():
    """Один квадрат."""
    img = new_canvas()
    draw = ImageDraw.Draw(img)
    draw.rectangle(
        [MARGIN, MARGIN, SIZE - MARGIN, SIZE - MARGIN],
        outline=COLOR,
        width=STROKE,
    )
    return img


def make_restore():
    """Два квадрата (для состояния «развёрнуто»)."""
    img = new_canvas()
    draw = ImageDraw.Draw(img)
    
    # Задний квадрат (чуть больше и со сдвигом)
    offset = 20
    draw.rectangle(
        [MARGIN, MARGIN, SIZE - MARGIN - offset, SIZE - MARGIN - offset],
        outline=COLOR,
        width=STROKE,
    )
    
    # Передний квадрат (перекрывает задний, но рисуем с фоном)
    front_box = [
        MARGIN + offset,
        MARGIN + offset,
        SIZE - MARGIN,
        SIZE - MARGIN,
    ]
    # Заливаем фоном (прозрачным), чтобы передний перекрыл задний
    draw.rectangle(front_box, fill=(0, 0, 0, 0), outline=None)
    # Обводка переднего
    draw.rectangle(front_box, outline=COLOR, width=STROKE)
    
    return img


def make_close():
    """Крестик."""
    img = new_canvas()
    draw = ImageDraw.Draw(img)
    
    draw.line(
        [(MARGIN, MARGIN), (SIZE - MARGIN, SIZE - MARGIN)],
        fill=COLOR,
        width=STROKE,
    )
    draw.line(
        [(MARGIN, SIZE - MARGIN), (SIZE - MARGIN, MARGIN)],
        fill=COLOR,
        width=STROKE,
    )
    return img


def main():
    # Куда сохранять
    project_root = Path(__file__).resolve().parent.parent
    output_dir = project_root / "icons" / "sprites" / "header"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    icons = {
        "minimize": make_minimize,
        "maximize": make_maximize,
        "restore":  make_restore,
        "close":    make_close,
    }
    
    for name, generator in icons.items():
        img = generator()
        path = output_dir / f"{name}.png"
        img.save(path, "PNG")
        print(f"✓ {path}")
    
    print(f"\nГотово! Иконки в: {output_dir}")


if __name__ == "__main__":
    main()