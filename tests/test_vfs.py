"""Проверки загрузки дерева и разрешения виртуальных путей."""

from pathlib import Path
import tempfile
import unittest

from src.vfs import VFS


EXAMPLES = Path(__file__).resolve().parents[1] / "examples/vfs"


class VfsTests(unittest.TestCase):
    """Проверить формат источника, снимок и границы корня."""

    def test_three_example_trees(self):
        """Все варианты VFS загружаются; глубокий путь доступен."""
        for name in ["minimal", "several", "deep"]:
            with self.subTest(name=name):
                vfs = VFS.from_directory(EXAMPLES / name)
                self.assertTrue(vfs.children("/"))
        self.assertIn("/docs/course/topic/notes.txt", vfs.nodes)

    def test_snapshot_is_independent(self):
        """Чтение после загрузки не обращается к изменённому источнику."""
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "a"
            source.write_bytes(b"original")
            vfs = VFS.from_directory(directory)
            source.write_bytes(b"changed")
            self.assertEqual(vfs.read("/a"), b"original")
            self.assertEqual(source.read_bytes(), b"changed")

    def test_invalid_sources(self):
        """Отсутствующий путь, файл и ссылка отклоняются."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            file = root / "file"
            file.write_bytes(b"text")
            for invalid in [root / "missing", file]:
                with self.assertRaises(ValueError):
                    VFS.from_directory(invalid)
            (root / "link").symlink_to(file)
            with self.assertRaises(ValueError):
                VFS.from_directory(root)

    def test_empty_tree_and_paths(self):
        """Корень непроходим вверх, промежуточные папки проверяются."""
        with tempfile.TemporaryDirectory() as directory:
            vfs = VFS.from_directory(directory)
        self.assertEqual(vfs.children("/"), [])
        self.assertEqual(vfs.resolve("../../.."), "/")
        vfs.nodes.update({"/dir": None, "/dir/a": b"a"})
        self.assertEqual(vfs.resolve("./a", "/dir"), "/dir/a")
        for path in ["/dir/a/..", "/dir/a/", "/missing/../dir"]:
            with self.assertRaises(ValueError):
                vfs.resolve(path)
        self.assertEqual(vfs.resolve("/new", missing_leaf=True), "/new")


if __name__ == "__main__":
    unittest.main()
