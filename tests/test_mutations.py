"""Проверки rm и mv, включая целостность дерева и диска."""

from pathlib import Path
import tempfile
import unittest

from src.shell import Shell
from src.vfs import VFS


def example_shell():
    """Создать небольшое дерево для сценариев переноса и удаления."""
    vfs = VFS()
    vfs.nodes.update({
        "/docs": None, "/docs/a": b"alpha", "/docs/sub": None,
        "/docs/sub/b": b"beta", "/docs2": None, "/empty": None,
        "/first": b"first", "/second": b"second", "/-file": b"dash",
    })
    return Shell(vfs=vfs)


class MutationTests(unittest.TestCase):
    """Проверить изменения состояния, ошибки и сохранность источника."""

    def test_rm_modes_and_component_boundary(self):
        """Удаление файла, -r, -f и -- не затрагивает соседние имена."""
        shell = example_shell()
        shell.execute("rm -- -file")
        shell.execute("rm first")
        shell.execute("rm -f missing")
        shell.execute("rm -f /missing/child")
        shell.execute("rm -f")
        shell.execute("rm -R docs")
        self.assertNotIn("/docs/sub/b", shell.vfs.nodes)
        self.assertIn("/docs2", shell.vfs.nodes)
        self.assertNotIn("/-file", shell.vfs.nodes)

    def test_rm_protection_is_atomic(self):
        """Недопустимое удаление не меняет ни одного узла дерева."""
        shell = example_shell()
        shell.execute("cd /docs/sub")
        before = shell.vfs.nodes.copy()
        for command in [
            "rm", "rm /missing", "rm /docs", "rm -r /",
            "rm -rf /docs", "rm -r .", "rm -r ..", "rm -z /first",
            "rm -f /first/child",
        ]:
            with self.subTest(command=command):
                with self.assertRaises(ValueError):
                    shell.execute(command)
                self.assertEqual(shell.vfs.nodes, before)

    def test_move_rename_overwrite_and_no_clobber(self):
        """Файлы переименовываются, переносятся и заменяются по режиму."""
        shell = example_shell()
        shell.execute("mv -n first second")
        self.assertEqual(shell.vfs.read("/second"), b"second")
        self.assertIn("/first", shell.vfs.nodes)
        shell.execute("mv -f first second")
        self.assertEqual(shell.vfs.read("/second"), b"first")
        self.assertNotIn("/first", shell.vfs.nodes)
        shell.execute("mv second renamed")
        shell.execute("mv renamed empty/")
        self.assertEqual(shell.vfs.read("/empty/renamed"), b"first")

    def test_move_directory_updates_session_paths(self):
        """При переносе предка cwd и cd - продолжают работать."""
        shell = example_shell()
        shell.execute("cd /docs")
        shell.execute("cd sub")
        shell.execute("mv /docs /moved")
        self.assertEqual(shell.cwd, "/moved/sub")
        self.assertEqual(shell.previous, "/moved")
        self.assertEqual(shell.execute("tail b"), "beta")
        self.assertEqual(shell.execute("cd -"), "/moved\n")
        self.assertIn("/docs2", shell.vfs.nodes)

    def test_invalid_moves_leave_tree_unchanged(self):
        """Цикл, совпадающий путь, типы и отсутствующие пути запрещены."""
        shell = example_shell()
        before = shell.vfs.nodes.copy()
        for command in [
            "mv / /root", "mv docs docs/sub/new", "mv first first",
            "mv docs first", "mv first missing/new", "mv absent new",
            "mv first nowhere/", "mv . elsewhere", "mv -n -f first second",
        ]:
            with self.subTest(command=command):
                with self.assertRaises(ValueError):
                    shell.execute(command)
                self.assertEqual(shell.vfs.nodes, before)

    def test_directory_replacement(self):
        """Разрешена только замена пустого каталога каталогом."""
        shell = example_shell()
        shell.vfs.nodes["/empty/docs"] = None
        shell.vfs.nodes["/empty/docs/keep"] = b"keep"
        before = shell.vfs.nodes.copy()
        with self.assertRaises(ValueError):
            shell.execute("mv docs empty")
        self.assertEqual(shell.vfs.nodes, before)
        shell.execute("rm /empty/docs/keep")
        shell.execute("mv docs empty")
        self.assertEqual(shell.vfs.read("/empty/docs/a"), b"alpha")
        self.assertNotIn("/docs", shell.vfs.nodes)

    def test_source_directory_is_unchanged(self):
        """После rm/mv байты и структура исходной папки не меняются."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "sub").mkdir()
            (root / "sub/a").write_bytes(b"alpha")
            (root / "b").write_bytes(b"beta")
            shell = Shell(vfs=VFS.from_directory(root))
            shell.execute("mv /sub /renamed")
            shell.execute("rm -r /renamed")
            shell.execute("rm /b")
            self.assertEqual(shell.vfs.nodes, {"/": None})
            self.assertEqual((root / "sub/a").read_bytes(), b"alpha")
            self.assertEqual((root / "b").read_bytes(), b"beta")
            names = sorted(p.name for p in root.iterdir())
            self.assertEqual(names, ["b", "sub"])
            fresh = VFS.from_directory(root)
            self.assertEqual(fresh.read("/sub/a"), b"alpha")


if __name__ == "__main__":
    unittest.main()
