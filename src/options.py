"""Общий разбор опций встроенных команд без завершения REPL."""

import argparse


class CommandParser(argparse.ArgumentParser):
    """Обычный argparse с восстанавливаемыми ошибками команд."""

    def __init__(self, command):
        """Создать парсер точных опций без автоматической команды help."""
        super().__init__(prog=command, add_help=False, allow_abbrev=False)

    def error(self, message):
        """Передать ошибку вызывающему REPL вместо sys.exit."""
        raise ValueError(f"{self.prog}: {message}")


def nonnegative(value):
    """Прочитать неотрицательное число строк или записей истории."""
    try:
        number = int(value)
    except ValueError as error:
        raise ValueError("требуется целое число") from error
    if number < 0:
        raise ValueError("число не может быть отрицательным")
    return number
