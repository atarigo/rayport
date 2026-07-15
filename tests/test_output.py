import tempfile
import tarfile
import unittest
from pathlib import Path

from rayport.dev_server import FileWatcher
from rayport.output import (
    OUTPUT_MARKER,
    OutputPathError,
    output_ignore_paths,
    prepare_output_dir,
    validate_output_path,
)
from rayport.packager import pack_game


class OutputTests(unittest.TestCase):
    def test_rejects_game_directory_and_its_parent(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            game = root / "game"
            game.mkdir()
            with self.assertRaises(OutputPathError):
                validate_output_path(game, game)
            with self.assertRaises(OutputPathError):
                validate_output_path(game, root)

    def test_refuses_non_rayport_directory_without_force(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            game = root / "game"
            output = root / "output"
            game.mkdir()
            output.mkdir()
            sentinel = output / "keep.txt"
            sentinel.write_text("keep\n")
            with self.assertRaisesRegex(OutputPathError, "Refusing to delete"):
                prepare_output_dir(game, output)
            self.assertTrue(sentinel.exists())

    def test_marker_allows_rebuild_and_force_requires_explicit_choice(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            game = root / "game"
            output = root / "output"
            game.mkdir()
            output.mkdir()
            (output / "old.txt").write_text("old\n")
            prepare_output_dir(game, output, force=True)
            self.assertTrue((output / OUTPUT_MARKER).is_file())
            (output / "generated.txt").write_text("generated\n")
            prepare_output_dir(game, output)
            self.assertFalse((output / "generated.txt").exists())

    def test_output_inside_game_is_excluded_from_package_and_watcher(self):
        with tempfile.TemporaryDirectory() as tmp:
            game = Path(tmp) / "game"
            output = game / "dist"
            game.mkdir()
            (game / "main.py").write_text("pass\n")
            ignored = output_ignore_paths(game, output)
            self.assertEqual(ignored, (output.resolve(),))
            prepare_output_dir(game, output)
            (output / "old.js").write_text("generated\n")
            pack_game(
                str(game),
                str(output / "game.tar.gz"),
                include=("dist/**",),
                ignore_paths=ignored,
            )
            with tarfile.open(output / "game.tar.gz") as archive:
                self.assertEqual(archive.getnames(), ["main.py"])
            watcher = FileWatcher(game, lambda changed: None, ignore_paths=(output,))
            self.assertFalse(any("/dist/" in path for path in watcher._mtimes))


if __name__ == "__main__":
    unittest.main()
