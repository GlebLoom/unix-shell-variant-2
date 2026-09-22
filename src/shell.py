"""Разбор команд и состояние сеанса эмулятора."""

import getpass
import io
import posixpath
import socket

from src.options import CommandParser, nonnegative
from src.vfs import MissingPath, VFS


DEFAULT_TAIL_LINES = 10


class Shell:
    """Хранит состояние одного сеанса и исполняет встроенные команды."""

    def __init__(self, prompt=None, vfs=None):
        """Получить реальное имя пользователя и имя компьютера."""
        self.identity = f"{getpass.getuser()}@{socket.gethostname()}"
        self.running = True
        self.custom_prompt = prompt
        self.vfs = vfs if vfs is not None else VFS()
        self.cwd = "/"
        self.previous = "/"
        self.history = []

    @property
    def prompt(self):
        """Вернуть приглашение консольного интерфейса."""
        if self.custom_prompt is not None:
            return self.custom_prompt
        return f"{self.identity}:{self.cwd if self.cwd != '/' else '~'}$ "

    def execute(self, line):
        """Разделить ввод по пробельным символам и выполнить команду."""
        words = line.split()
        if not words:
            return ""
        self.history.append(line.strip())
        command, *arguments = words
        commands = {
            "ls": self.ls, "cd": self.cd, "tail": self.tail,
            "wc": self.wc, "history": self.show_history, "exit": self.exit,
            "rm": self.rm, "mv": self.mv,
        }
        if command not in commands:
            raise ValueError(f"{command}: неизвестная команда")
        return commands[command](arguments)

    def exit(self, arguments):
        """Завершить сеанс, если аргументы отсутствуют."""
        if arguments:
            raise ValueError("exit: аргументы не поддерживаются")
        self.running = False
        return ""

    def ls(self, arguments):
        """Показать файл или содержимое папки; -a включает скрытые имена."""
        parser = CommandParser("ls")
        parser.add_argument("-a", action="store_true")
        parser.add_argument("path", nargs="?", default=".")
        options = parser.parse_args(arguments)
        path = self.vfs.resolve(options.path, self.cwd)
        if self.vfs.nodes[path] is not None:
            return posixpath.basename(path) + "\n"
        names = self.vfs.children(path)
        if options.a:
            names = [".", "..", *names]
        else:
            names = [name for name in names if not name.startswith(".")]
        return "".join(name + "\n" for name in names)

    def cd(self, arguments):
        """Перейти в папку, в корень без аргумента или назад через -."""
        parser = CommandParser("cd")
        parser.add_argument("path", nargs="?", default="/")
        options = parser.parse_args(arguments)
        target = self.previous if options.path == "-" else options.path
        target = self.vfs.resolve(target, self.cwd)
        self.vfs.require_directory(target)
        self.previous, self.cwd = self.cwd, target
        return target + "\n" if options.path == "-" else ""

    def tail(self, arguments):
        """Вывести последние N строк одного UTF-8 файла; +N — с N-й."""
        parser = CommandParser("tail")
        parser.add_argument("-n", default=str(DEFAULT_TAIL_LINES))
        parser.add_argument("path")
        options = parser.parse_args(arguments)
        count = nonnegative(options.n)
        path = self.vfs.resolve(options.path, self.cwd)
        text = self.vfs.read(path).decode("utf-8")
        lines = io.StringIO(text, newline="\n").readlines()
        if options.n.startswith("+"):
            return "".join(lines[max(count - 1, 0):])
        return "".join(lines[-count:]) if count else ""

    def wc(self, arguments):
        """Посчитать переводы строк, слова, символы или байты файла."""
        parser = CommandParser("wc")
        for flag in "lwmc":
            parser.add_argument(f"-{flag}", action="store_true")
        parser.add_argument("path")
        options = parser.parse_args(arguments)
        flags = [flag for flag in "lwmc" if getattr(options, flag)]
        flags = flags or list("lwc")
        path = self.vfs.resolve(options.path, self.cwd)
        data = self.vfs.read(path)
        counts = {"l": data.count(b"\n"), "c": len(data)}
        if "w" in flags or "m" in flags:
            text = data.decode("utf-8")
            counts.update(w=len(text.split()), m=len(text))
        return " ".join(str(counts[flag]) for flag in flags) + (
            f" {options.path}\n"
        )

    def show_history(self, arguments):
        """Показать историю сеанса или последние N введённых команд."""
        parser = CommandParser("history")
        parser.add_argument("count", nargs="?", type=nonnegative)
        options = parser.parse_args(arguments)
        start = 0
        if options.count is not None:
            start = max(len(self.history) - options.count, 0)
        return "".join(
            f"{number:4}  {line}\n" for number, line in
            enumerate(self.history[start:], start=start + 1)
        )

    def rm(self, arguments):
        """Удалить один файл или дерево; -f допускает отсутствие файла."""
        parser = CommandParser("rm")
        parser.add_argument("-r", "-R", action="store_true", dest="recursive")
        parser.add_argument("-f", action="store_true", dest="force")
        parser.add_argument("path", nargs="?")
        options = parser.parse_args(arguments)
        if options.path is None:
            if options.force:
                return ""
            raise ValueError("rm: требуется путь")
        if posixpath.basename(options.path.rstrip("/")) in {".", ".."}:
            raise ValueError("rm: имена . и .. защищены")
        try:
            path = self.vfs.resolve(options.path, self.cwd, missing_leaf=True)
        except MissingPath:
            if options.force:
                return ""
            raise
        self.vfs.remove(path, self.cwd, options.recursive, options.force)
        return ""

    def mv(self, arguments):
        """Переименовать или перенести один объект; -n запрещает замену."""
        parser = CommandParser("mv")
        mode = parser.add_mutually_exclusive_group()
        mode.add_argument("-n", action="store_true", dest="no_clobber")
        mode.add_argument("-f", action="store_true")
        parser.add_argument("source")
        parser.add_argument("target")
        options = parser.parse_args(arguments)
        if posixpath.basename(options.source.rstrip("/")) in {".", ".."}:
            raise ValueError("mv: имена . и .. защищены")
        source = self.vfs.resolve(options.source, self.cwd)
        target = self.vfs.resolve(options.target, self.cwd, missing_leaf=True)
        destination = self.vfs.move(source, target, options.no_clobber)
        self.cwd = self._moved_path(self.cwd, source, destination)
        self.previous = self._moved_path(self.previous, source, destination)
        return ""

    @staticmethod
    def _moved_path(path, source, destination):
        """Обновить путь сеанса при переименовании содержащей его папки."""
        if path == source or path.startswith(source + "/"):
            return destination + path[len(source):]
        return path
