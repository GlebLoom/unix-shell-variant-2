"""Снимок директории: абсолютный путь -> байты файла или None для папки."""

from pathlib import Path
import posixpath


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
            raise ValueError(f"{path}: путь не найден")
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
                raise ValueError(f"{current}: путь не найден")
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
            raise ValueError(f"{path}: путь не найден")
        data = self.nodes[path]
        if data is None:
            raise ValueError(f"{path}: является директорией")
        return data
