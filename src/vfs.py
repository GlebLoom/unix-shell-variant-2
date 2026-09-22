"""Снимок директории: абсолютный путь -> байты файла или None для папки."""

from pathlib import Path
import posixpath


class MissingPath(ValueError):
    """Запрошенный виртуальный путь отсутствует."""


class VFS:
    """Хранит дерево целиком в оперативной памяти без записи на диск."""

    def __init__(self):
        """Создать пустой виртуальный корень."""
        self.nodes = {"/": None}

    @classmethod
    def from_directory(cls, directory):
        """Прочитать обычные файлы; отклонить ссылки и особые файлы."""
        root = Path(directory)
        if not root.exists():
            raise ValueError(f"VFS: путь не найден: {root}")
        if root.is_symlink() or not root.is_dir():
            raise ValueError(f"VFS: требуется обычная директория: {root}")
        result = cls()
        result._load(root)
        return result

    def _load(self, root):
        """Скопировать содержимое итеративно, не переходя по ссылкам."""
        pending = [(root, "/")]
        while pending:
            physical, virtual = pending.pop()
            for child in sorted(physical.iterdir()):
                target = posixpath.join(virtual, child.name)
                if child.is_symlink():
                    raise ValueError(f"VFS: ссылка не поддерживается: {child}")
                if child.is_dir():
                    self.nodes[target] = None
                    pending.append((child, target))
                elif child.is_file():
                    self.nodes[target] = child.read_bytes()
                else:
                    raise ValueError(f"VFS: особый файл: {child}")

    def require_directory(self, path):
        """Проверить существование директории по каноническому пути."""
        if path not in self.nodes:
            raise MissingPath(f"{path}: путь не найден")
        if self.nodes[path] is not None:
            raise ValueError(f"{path}: не является директорией")

    def resolve(self, path, cwd="/", missing_leaf=False):
        """Разрешить /, ., ..; разрешать отсутствие лишь последнего имени."""
        current = "/" if path.startswith("/") else cwd
        parts = path.split("/")
        for index, part in enumerate(parts):
            self.require_directory(current)
            if part in {"", "."}:
                continue
            if part == "..":
                current = posixpath.dirname(current) or "/"
                continue
            current = posixpath.join(current, part)
            last = index == len(parts) - 1
            if current not in self.nodes and not (missing_leaf and last):
                raise MissingPath(f"{current}: путь не найден")
        return current

    def children(self, directory):
        """Вернуть отсортированные имена непосредственных потомков."""
        self.require_directory(directory)
        return sorted(
            posixpath.basename(path) for path in self.nodes
            if path != "/" and posixpath.dirname(path) == directory
        )

    def read(self, path):
        """Вернуть байты файла по каноническому пути."""
        if path not in self.nodes:
            raise MissingPath(f"{path}: путь не найден")
        data = self.nodes[path]
        if data is None:
            raise ValueError(f"{path}: является директорией")
        return data

    def subtree(self, path):
        """Найти узел и его потомков по границе компонента пути."""
        return [
            name for name in self.nodes
            if name == path or name.startswith(path + "/")
        ]

    def remove(self, path, cwd, recursive=False, force=False):
        """Удалить узел в памяти; защитить корень и текущую папку."""
        if path == "/" or cwd == path or cwd.startswith(path + "/"):
            raise ValueError("rm: нельзя удалить корень или текущую папку")
        if path not in self.nodes:
            if force:
                return
            raise ValueError(f"rm: {path}: путь не найден")
        if self.nodes[path] is None and not recursive:
            raise ValueError(f"rm: {path}: для директории требуется -r")
        for name in self.subtree(path):
            del self.nodes[name]

    def move(self, source, target, no_clobber=False):
        """Перенести поддерево после полной проверки; вернуть новый путь."""
        target = self._move_target(source, target)
        if target in self.nodes:
            if no_clobber:
                return source
            self._check_replacement(source, target)
        moving = self.subtree(source)
        replacements = {
            target + name[len(source):]: self.nodes[name] for name in moving
        }
        for name in moving:
            del self.nodes[name]
        self.nodes.update(replacements)
        return target

    def _move_target(self, source, target):
        """Разрешить назначение переноса и запретить циклы в дереве."""
        if source == "/":
            raise ValueError("mv: нельзя переместить корень VFS")
        if source not in self.nodes:
            raise ValueError(f"mv: {source}: путь не найден")
        if target in self.nodes and self.nodes[target] is None:
            target = posixpath.join(target, posixpath.basename(source))
        if target == source or target.startswith(source + "/"):
            raise ValueError("mv: перенос в себя или собственный подкаталог")
        self.require_directory(posixpath.dirname(target))
        return target

    def _check_replacement(self, source, target):
        """Разрешить замену файла файлом или пустой папки папкой."""
        source_directory = self.nodes[source] is None
        target_directory = self.nodes[target] is None
        if source_directory != target_directory:
            raise ValueError("mv: несовместимые типы источника и назначения")
        if target_directory and self.children(target):
            raise ValueError(f"mv: {target}: директория не пуста")
