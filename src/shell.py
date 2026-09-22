"""Разбор команд и состояние сеанса эмулятора."""

import getpass
import socket


class Shell:
    """Хранит состояние одного сеанса и исполняет встроенные команды."""

    def __init__(self):
        """Получить реальное имя пользователя и имя компьютера."""
        self.identity = f"{getpass.getuser()}@{socket.gethostname()}"
        self.running = True

    @property
    def prompt(self):
        """Вернуть приглашение консольного интерфейса."""
        return f"{self.identity}:~$ "

    def execute(self, line):
        """Разделить ввод по пробельным символам и выполнить команду."""
        words = line.split()
        if not words:
            return ""
        command, *arguments = words
        if command == "exit":
            if arguments:
                raise ValueError("exit: аргументы не поддерживаются")
            self.running = False
            return ""
        if command in {"ls", "cd"}:
            return f"{command}: {arguments!r}\n"
        raise ValueError(f"{command}: неизвестная команда")
