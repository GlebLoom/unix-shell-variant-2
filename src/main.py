"""Точка входа консольного эмулятора."""

import argparse
import json
from pathlib import Path
import sys

from src.shell import Shell
from src.vfs import VFS


DEFAULT_VFS = Path(__file__).resolve().parents[1] / "examples/vfs/deep"


def run_line(shell, line, location=""):
    """Вывести результат команды; вернуть 1 при ошибке, иначе 0."""
    try:
        print(shell.execute(line), end="", flush=True)
        return 0
    except ValueError as error:
        print(f"Ошибка: {location}{error}", file=sys.stderr, flush=True)
        return 1


def repl(shell):
    """Читать команды до exit или конца ввода; Ctrl+C отменяет ввод."""
    status = 0
    while shell.running:
        try:
            line = input(shell.prompt)
        except EOFError:
            break
        except KeyboardInterrupt:
            print()
            continue
        status = max(status, run_line(shell, line))
    return status


def parse_config(arguments=None):
    """Разобрать три параметра настройки средствами argparse."""
    parser = argparse.ArgumentParser(
        description="Эмулятор UNIX-оболочки. Вариант 2.",
        allow_abbrev=False,
    )
    parser.add_argument(
        "--vfs", default=str(DEFAULT_VFS),
        help="Директория-источник VFS (по умолчанию examples/vfs/deep)",
    )
    parser.add_argument("--prompt", help="Точное приглашение к вводу")
    parser.add_argument("--script", help="Стартовый скрипт UTF-8")
    return parser.parse_args(arguments)


def run_script(shell, path):
    """Показать диалог; пропустить ошибки команд и вернуть их статус."""
    lines = Path(path).read_text(encoding="utf-8-sig").splitlines()
    status = 0
    for number, line in enumerate(lines, start=1):
        if not shell.running:
            break
        print(f"{shell.prompt}{line}", flush=True)
        location = f"{path}:{number}: "
        status = max(status, run_line(shell, line, location))
    return status


def main(arguments=None):
    """Применить настройки, выполнить скрипт и перейти к REPL."""
    config = parse_config(arguments)
    print("Конфигурация:", flush=True)
    for key, value in vars(config).items():
        print(f"{key}={json.dumps(value, ensure_ascii=False)}", flush=True)
    try:
        vfs = VFS.from_directory(config.vfs)
    except (OSError, ValueError) as error:
        print(f"Ошибка загрузки VFS: {error}", file=sys.stderr)
        return 1
    shell = Shell(prompt=config.prompt, vfs=vfs)
    status = 0
    if config.script:
        try:
            status = run_script(shell, config.script)
        except (OSError, UnicodeError) as error:
            print(f"Ошибка стартового скрипта: {error}", file=sys.stderr)
            return 1
    return max(status, repl(shell))


if __name__ == "__main__":
    sys.exit(main())
