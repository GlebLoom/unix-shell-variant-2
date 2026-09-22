"""Точка входа консольного эмулятора."""

import sys

from src.shell import Shell


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


def main():
    """Запустить интерактивный сеанс."""
    return repl(Shell())


if __name__ == "__main__":
    sys.exit(main())
