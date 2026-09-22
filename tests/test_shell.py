"""Проверки команд оболочки и границ виртуального сеанса."""

import unittest
from unittest.mock import patch

from src.shell import Shell
from src.vfs import VFS


class ShellTests(unittest.TestCase):
    """Проверить разбор, приглашение, ошибки и завершение сеанса."""

    def test_identity_and_whitespace(self):
        """Используются данные ОС, пустая строка ничего не делает."""
        with patch("getpass.getuser", return_value="student"):
            with patch("socket.gethostname", return_value="host"):
                shell = Shell()
        self.assertEqual(shell.prompt, "student@host:~$ ")
        self.assertEqual(shell.execute(" \t "), "")

    def test_simple_parser(self):
        """Кавычки не объединяют аргументы; ошибка не закрывает сеанс."""
        shell = Shell()
        with self.assertRaises(ValueError):
            shell.execute('cd "a b"')
        self.assertEqual(shell.execute("ls"), "")
        self.assertTrue(shell.running)

    def test_error_and_exit(self):
        """Ошибка не завершает сеанс; exit без аргументов завершает."""
        shell = Shell()
        for line in ["unknown", "exit extra"]:
            with self.assertRaises(ValueError):
                shell.execute(line)
        self.assertTrue(shell.running)
        self.assertEqual(shell.execute("exit"), "")
        self.assertFalse(shell.running)

    def test_listing_and_navigation(self):
        """Скрытые файлы, относительные пути и cd - работают в VFS."""
        vfs = VFS()
        vfs.nodes.update({"/docs": None, "/docs/a": b"text", "/.h": b""})
        shell = Shell(vfs=vfs)
        self.assertEqual(shell.execute("ls"), "docs\n")
        self.assertEqual(shell.execute("ls -a"), ".\n..\n.h\ndocs\n")
        self.assertEqual(shell.execute("cd docs"), "")
        self.assertTrue(shell.prompt.endswith(":/docs$ "))
        self.assertEqual(shell.execute("ls ./a"), "a\n")
        self.assertEqual(shell.execute("cd -"), "/\n")
        self.assertEqual(shell.execute("cd"), "")
        with self.assertRaises(ValueError):
            shell.execute("cd /docs/a")
        self.assertEqual(shell.cwd, "/")

    def test_tail_counts_and_unterminated_line(self):
        """Последние строки, нуль и +N сохраняют переводы строк."""
        vfs = VFS()
        vfs.nodes["/a"] = b"one\ntwo\nthree"
        shell = Shell(vfs=vfs)
        for command, expected in [
            ("tail a", "one\ntwo\nthree"), ("tail -n 1 a", "three"),
            ("tail -n 0 a", ""), ("tail -n +2 a", "two\nthree"),
            ("tail -n +20 a", ""), ("tail -n 20 a", "one\ntwo\nthree"),
        ]:
            with self.subTest(command=command):
                self.assertEqual(shell.execute(command), expected)
        for command in ["tail", "tail -n -1 a", "tail -n x a", "tail /"]:
            with self.assertRaises(ValueError):
                shell.execute(command)

    def test_wc_unicode_binary_and_newlines(self):
        """Байты отличаются от символов; -l считает только LF."""
        vfs = VFS()
        vfs.nodes.update({"/a": "Я ты\nон".encode(), "/b": b"\xff\n"})
        shell = Shell(vfs=vfs)
        self.assertEqual(shell.execute("wc a"), "1 3 12 a\n")
        self.assertEqual(shell.execute("wc -m a"), "7 a\n")
        self.assertEqual(shell.execute("wc -cl a"), "1 12 a\n")
        self.assertEqual(shell.execute("wc -lc b"), "1 2 b\n")
        with self.assertRaises(ValueError):
            shell.execute("wc -w b")

    def test_tail_lf_only_and_empty_file(self):
        """Разделитель строк — LF, не одиночный CR или символ Unicode."""
        vfs = VFS()
        vfs.nodes.update({"/a": b"one\ntwo\rthree", "/empty": b""})
        shell = Shell(vfs=vfs)
        self.assertEqual(shell.execute("tail -n 1 a"), "two\rthree")
        self.assertEqual(shell.execute("tail empty"), "")
        self.assertEqual(shell.execute("wc empty"), "0 0 0 empty\n")

    def test_history_includes_errors_and_itself(self):
        """История хранит только непустые строки и нумеруется с единицы."""
        shell = Shell()
        shell.execute("  ")
        shell.execute("ls")
        with self.assertRaises(ValueError):
            shell.execute("unknown")
        self.assertEqual(
            shell.execute("history 2"), "   2  unknown\n   3  history 2\n",
        )
        self.assertEqual(shell.execute("history 0"), "")

    def test_unsupported_options(self):
        """Неизвестные флаги дают ошибки вместо завершения Python."""
        shell = Shell()
        for command in ["ls -z", "cd a b", "history -2", "wc -z a"]:
            with self.subTest(command=command):
                with self.assertRaises(ValueError):
                    shell.execute(command)


if __name__ == "__main__":
    unittest.main()
