#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 YaroslavIshkov
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""Скрипт для добавления SPDX-заголовков в исходные файлы проекта.

Проходит по указанной директории, находит файлы с нужными расширениями
и добавляет в их начало SPDX-блок (копирайт + идентификатор лицензии),
если в файле его ещё нет. Позволяет избежать проблем с лицензированием
при публикации проекта (см. спецификацию REUSE).

Особенности:
    - Пропускает файлы, где уже есть ``SPDX-License-Identifier``.
    - Сохраняет shebang (``#!...``) и декларацию кодировки (PEP 263)
      в самом начале файла — заголовок вставляется после них.
    - Не трогает строки файла, включая их переводы строк (LF/CRLF).
    - Пропускает типичные мусорные директории (``.git``, ``__pycache__``,
      ``venv`` и т.п.).
    - Поддерживает режим ``--dry-run`` — показать, что было бы изменено,
      без записи.

Примеры запуска::

    # Обработать текущий проект (все .py)
    python add_spdx.py

    # Обработать конкретную папку, только .py и .pyi
    python add_spdx.py --root ./src --extensions .py .pyi

    # Посмотреть, что будет изменено, без записи
    python add_spdx.py --dry-run

    # Свои копирайт и лицензия
    python add_spdx.py --author "Ivan Ivanov" --year 2025 --license MIT
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Iterable, Iterator

# --- Настройки по умолчанию ------------------------------------------------

DEFAULT_AUTHOR = "YaroslavIshkov"
DEFAULT_YEAR = "2026"
DEFAULT_LICENSE = "GPL-3.0-or-later"
DEFAULT_EXTENSIONS = (".py",)

DEFAULT_EXCLUDES = {
    ".git", ".hg", ".svn",
    ".venv", "venv", "env", ".env",
    "__pycache__", "build", "dist",
    ".idea", ".vscode",
    "node_modules",
    ".mypy_cache", ".pytest_cache", ".ruff_cache", ".tox",
}

# PEP 263: `# -*- coding: utf-8 -*-`, `# coding: utf-8`, `# vim: ... coding=...`
CODING_RE = re.compile(r"^[ \t\f]*#.*?coding[:=][ \t]*([-\w.]+)")

# Маркер уже вставленного заголовка
SPDX_MARKER = "SPDX-License-Identifier"

# --- Ядро ------------------------------------------------------------------

def build_header(comment: str, author: str, year: str, license_id: str,
                 newline: str = "\n") -> str:
    """Собирает текст SPDX-заголовка.

    Args:
        comment: Префикс комментария для данного типа файла (например, ``"# "``).
        author: Имя автора/организации для строки копирайта.
        year: Год копирайта (строка, чтобы можно было писать ``"2024-2026"``).
        license_id: Идентификатор лицензии в формате SPDX.
        newline: Разделитель строк (``"\\n"`` или ``"\\r\\n"``).

    Returns:
        Готовый текст заголовка, заканчивающийся одним переводом строки.
    """
    empty = comment.rstrip()
    lines = [
        f"{comment}SPDX-FileCopyrightText: {year} {author}",
        empty,
        f"{comment}SPDX-License-Identifier: {license_id}",
    ]
    return newline.join(lines) + newline


def has_spdx(text: str) -> bool:
    """Проверяет, есть ли в начале файла SPDX-идентификатор.

    Смотрим только первые ~2 КБ, чтобы не искать по всему файлу.

    Args:
        text: Содержимое файла.

    Returns:
        True, если маркер уже найден.
    """
    return SPDX_MARKER in text[:2048]


def insert_position(lines: list[str]) -> int:
    """Определяет индекс строки, ПЕРЕД которой нужно вставить заголовок.

    Пропускает shebang и декларацию кодировки (PEP 263), чтобы они остались
    самыми первыми строками файла.

    Args:
        lines: Список строк файла (с сохранёнными переводами строк).

    Returns:
        Индекс для вставки.
    """
    i = 0
    if i < len(lines) and lines[i].startswith("#!"):
        i += 1
    if i < len(lines) and CODING_RE.match(lines[i]):
        i += 1
    return i


def detect_newline(text: str) -> str:
    """Определяет доминирующий перевод строки в файле.

    Args:
        text: Содержимое файла.

    Returns:
        ``"\\r\\n"``, если в начале файла есть CRLF, иначе ``"\\n"``.
    """
    head = text[:4096]
    return "\r\n" if "\r\n" in head else "\n"


def process_file(path: Path, *, author: str, year: str, license_id: str,
                 comment: str, dry_run: bool) -> str:
    """Обрабатывает один файл: вставляет SPDX-заголовок, если нужно.

    Args:
        path: Путь к файлу.
        author: Автор для копирайта.
        year: Год копирайта.
        license_id: SPDX-идентификатор лицензии.
        comment: Префикс комментария (``"# "`` для Python).
        dry_run: Если True — не пишем на диск, только сообщаем.

    Returns:
        Одно из значений: ``"added"``, ``"would-add"``, ``"already"``,
        ``"skip-encoding"`` (файл не в UTF-8).
    """
    try:
        raw = path.read_bytes()
    except OSError as e:
        return f"error: {e}"

    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        return "skip-encoding"

    if has_spdx(text):
        return "already"

    newline = detect_newline(text)
    header = build_header(comment, author, year, license_id, newline)

    lines = text.splitlines(keepends=True)
    pos = insert_position(lines)

    new_text = "".join(lines[:pos]) + header + newline + "".join(lines[pos:])

    if dry_run:
        return "would-add"

    try:
        path.write_bytes(new_text.encode("utf-8"))
    except OSError as e:
        return f"error: {e}"

    return "added"


def iter_files(root: Path, extensions: Iterable[str],
               excludes: set[str]) -> Iterator[Path]:
    """Генерирует файлы с нужными расширениями, пропуская exclude-папки.

    Args:
        root: Корневая директория обхода.
        extensions: Кортеж расширений (например, ``(".py",)``).
        excludes: Множество имён директорий, которые нужно пропустить.

    Yields:
        Пути к подходящим файлам.
    """
    exts = tuple(ext.lower() for ext in extensions)
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        if any(part in excludes for part in p.parts):
            continue
        if p.suffix.lower() in exts:
            yield p


# --- CLI -------------------------------------------------------------------

def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Разбирает аргументы командной строки."""
    parser = argparse.ArgumentParser(
        description="Добавляет SPDX-заголовки в исходные файлы проекта.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--root", type=Path, default=Path(__file__).resolve().parent,
        help="Корневая директория для обхода.",
    )
    parser.add_argument(
        "--extensions", nargs="+", default=list(DEFAULT_EXTENSIONS),
        help="Расширения файлов для обработки (например, .py .pyi .qss).",
    )
    parser.add_argument(
        "--author", default=DEFAULT_AUTHOR,
        help="Имя автора для строки SPDX-FileCopyrightText.",
    )
    parser.add_argument(
        "--year", default=DEFAULT_YEAR,
        help="Год для копирайта (можно диапазон: 2024-2026).",
    )
    parser.add_argument(
        "--license", dest="license_id", default=DEFAULT_LICENSE,
        help="SPDX-идентификатор лицензии (например, MIT, Apache-2.0).",
    )
    parser.add_argument(
        "--comment", default="# ",
        help="Префикс комментария (для Python и большинства скриптов — '# ').",
    )
    parser.add_argument(
        "--exclude", nargs="*", default=sorted(DEFAULT_EXCLUDES),
        help="Имена директорий, которые нужно пропустить.",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Не изменять файлы, только показать, что было бы сделано.",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true",
        help="Печатать каждый файл, включая те, что уже имеют SPDX.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Точка входа CLI.

    Args:
        argv: Список аргументов (без имени программы). Если None — берётся
            из ``sys.argv[1:]``.

    Returns:
        Код возврата: 0 — успех, 1 — нечего обрабатывать.
    """
    args = parse_args(argv)

    root: Path = args.root.resolve()
    if not root.exists() or not root.is_dir():
        print(f"[ERROR] Директория не найдена: {root}", file=sys.stderr)
        return 1

    excludes = set(args.exclude)
    counters = {
        "added": 0, "would-add": 0, "already": 0,
        "skip-encoding": 0, "error": 0,
    }
    errors: list[str] = []

    print(f"[INFO] Корень: {root}")
    print(f"[INFO] Расширения: {', '.join(args.extensions)}")
    print(f"[INFO] Лицензия: {args.license_id}, автор: {args.author} {args.year}")
    if args.dry_run:
        print("[INFO] Режим dry-run — файлы не изменяются")
    print()

    files = list(iter_files(root, args.extensions, excludes))
    for path in files:
        result = process_file(
            path,
            author=args.author,
            year=args.year,
            license_id=args.license_id,
            comment=args.comment,
            dry_run=args.dry_run,
        )

        # Разбираем результат: либо известный статус, либо строка с error
        status = result if result in counters else "error"
        counters[status] += 1
        if status == "error":
            errors.append(f"{path}: {result}")

        rel = path.relative_to(root)
        if status == "added":
            print(f"[ADD]     {rel}")
        elif status == "would-add":
            print(f"[WOULD]   {rel}")
        elif status == "already":
            if args.verbose:
                print(f"[SKIP]    {rel} (SPDX уже есть)")
        elif status == "skip-encoding":
            print(f"[ENCODING]{rel} (не UTF-8 — пропущено)")
        elif status == "error":
            print(f"[ERROR]   {rel}: {result}")

    print()
    print("Итого:")
    print(f"  добавлено:        {counters['added']}")
    if args.dry_run:
        print(f"  было бы добавлено:{counters['would-add']}")
    print(f"  уже с SPDX:       {counters['already']}")
    print(f"  не UTF-8:         {counters['skip-encoding']}")
    print(f"  ошибок:           {counters['error']}")
    print(f"  всего файлов:     {len(files)}")

    if errors:
        print()
        print("Ошибки:")
        for e in errors:
            print(f"  {e}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())