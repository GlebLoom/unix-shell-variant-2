"""Проверки прототипа оболочки."""

import unittest
from unittest.mock import patch

from src.shell import Shell


class ShellTests(unittest.TestCase):
    """Проверить разбор, приглашение, ошибки и завершение сеанса."""

    def test_identity_and_whitespace(self):
        """Используются данные ОС, пустая строка ничего не делает."""
        with patch("getpass.getuser", return_value="student"):
            with patch("socket.gethostname", return_value="host"):
                shell = Shell()
        self.assertEqual(shell.prompt, "student@host:~$ ")
        self.assertEqual(shell.execute(" \t "), "")

    def test_stub_arguments(self):
        """Парсер делит строку по пробелам без обработки кавычек."""
        shell = Shell()
        self.assertEqual(shell.execute("ls  a b"), "ls: ['a', 'b']\n")
        self.assertEqual(shell.execute('cd "a b"'), 'cd: [\'"a\', \'b"\']\n')

    def test_error_and_exit(self):
        """Ошибка не завершает сеанс; exit без аргументов завершает."""
        shell = Shell()
        for line in ["unknown", "exit extra"]:
            with self.assertRaises(ValueError):
                shell.execute(line)
        self.assertTrue(shell.running)
        self.assertEqual(shell.execute("exit"), "")
        self.assertFalse(shell.running)


if __name__ == "__main__":
    unittest.main()
