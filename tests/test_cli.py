"""Интеграционные проверки CLI и стартового скрипта."""

from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from src.main import parse_config


PROJECT = Path(__file__).resolve().parents[1]


def invoke(*arguments, input_text=""):
    """Запустить CLI отдельным процессом, ограниченным по времени."""
    return subprocess.run(
        [sys.executable, "-m", "src.main", *arguments],
        cwd=PROJECT, input=input_text, text=True, capture_output=True,
        timeout=10,
    )


class CliTests(unittest.TestCase):
    """Проверить параметры, восстановление после ошибок и коды выхода."""

    def test_all_settings(self):
        """Три настройки разбираются без потери пробелов в prompt."""
        config = parse_config([
            "--vfs", "data path", "--prompt", "student> ",
            "--script", "start.txt",
        ])
        self.assertEqual(vars(config), {
            "vfs": "data path", "prompt": "student> ",
            "script": "start.txt",
        })

    def test_script_continues_then_exit_stops(self):
        """Ошибка получает номер строки, exit прекращает скрипт."""
        with tempfile.TemporaryDirectory() as directory:
            script = Path(directory) / "start.txt"
            script.write_text("unknown\nls\nexit\nnever\n", encoding="utf-8")
            result = invoke("--prompt", "demo> ", "--script", str(script))
        self.assertEqual(result.returncode, 1)
        self.assertIn("demo> ls", result.stdout)
        self.assertIn(":1: unknown:", result.stderr)
        self.assertNotIn("never", result.stdout)
        self.assertIn('prompt="demo> "', result.stdout)

    def test_cli_errors_and_eof(self):
        """Отсутствующий скрипт и неверные опции дают ненулевой код."""
        self.assertEqual(invoke("--script", "/missing/script").returncode, 1)
        self.assertEqual(invoke("--unknown").returncode, 2)
        self.assertEqual(invoke("--prompt").returncode, 2)
        self.assertEqual(invoke(input_text="exit\n").returncode, 0)
        self.assertEqual(invoke().returncode, 0)

    def test_invalid_vfs_and_script_encoding(self):
        """Ошибки источников обрабатываются без traceback."""
        with tempfile.TemporaryDirectory() as directory:
            file = Path(directory) / "file"
            file.write_bytes(b"\xff\xfe")
            bad_vfs = invoke("--vfs", str(file))
            bad_script = invoke("--script", str(file))
        for result in [bad_vfs, bad_script]:
            self.assertEqual(result.returncode, 1)
            self.assertIn("Ошибка", result.stderr)
            self.assertNotIn("Traceback", result.stderr)

    def test_script_returns_to_interactive_input(self):
        """Скрипт без exit передаёт управление REPL с той же VFS."""
        with tempfile.TemporaryDirectory() as directory:
            script = Path(directory) / "start.txt"
            script.write_text("cd /docs\n", encoding="utf-8")
            result = invoke(
                "--script", str(script), input_text="ls\nexit\n",
            )
        self.assertEqual(result.returncode, 0)
        self.assertIn("russian.txt", result.stdout)
        self.assertIn(":/docs$ ", result.stdout)


if __name__ == "__main__":
    unittest.main()
