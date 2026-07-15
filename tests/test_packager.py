import gzip
import tarfile
import tempfile
import unittest
from pathlib import Path

from rayport.packager import decide_file, inspect_game, pack_game


class PackagerTests(unittest.TestCase):
    def test_default_and_custom_exclusions(self):
        self.assertFalse(decide_file("pkg/__pycache__/game.pyc").included)
        self.assertFalse(decide_file("tests/test_game.py", exclude=("tests/**",)).included)
        self.assertTrue(
            decide_file(
                "tests/runtime_data/map.json",
                exclude=("tests/**",),
                include=("tests/runtime_data/**",),
            ).included
        )
        self.assertTrue(decide_file("tests/a/b.py", exclude=("tests/*",)).included)
        self.assertFalse(decide_file("tests/a/b.py", exclude=("tests/**",)).included)
        self.assertFalse(decide_file("assets/icon.png", exclude=("assets/**/icon.png",)).included)

    def test_inspection_explains_decisions(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "main.py").write_text("pass\n")
            (root / "debug").mkdir()
            (root / "debug" / "probe.py").write_text("pass\n")
            decisions = inspect_game(tmp, exclude=("debug/**",))
        by_path = {item.path: item for item in decisions}
        self.assertTrue(by_path["main.py"].included)
        self.assertIn("exclude pattern", by_path["debug/probe.py"].reason)

    def test_pack_contains_only_included_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            game = root / "game"
            game.mkdir()
            (game / "main.py").write_text("pass\n")
            (game / "asset.txt").write_text("asset\n")
            (game / "tests").mkdir()
            (game / "tests" / "test_game.py").write_text("pass\n")
            output = root / "game.tar.gz"
            pack_game(str(game), str(output), exclude=("tests/**",))
            with tarfile.open(output) as archive:
                names = archive.getnames()
        self.assertEqual(names, ["asset.txt", "main.py"])

    def test_pack_does_not_include_its_own_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            game = Path(tmp)
            (game / "main.py").write_text("pass\n")
            output = game / "release.tar.gz"
            pack_game(str(game), str(output))
            with tarfile.open(output) as archive:
                names = archive.getnames()
        self.assertEqual(names, ["main.py"])

    def test_main_entry_point_cannot_be_excluded(self):
        with tempfile.TemporaryDirectory() as tmp:
            game = Path(tmp)
            (game / "main.py").write_text("pass\n")
            with self.assertRaisesRegex(ValueError, "main.py cannot be excluded"):
                pack_game(str(game), str(game / "game.tar.gz"), exclude=("*.py",))

    def test_long_paths_are_written_with_pax_metadata(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            game = root / "game"
            game.mkdir()
            (game / "main.py").write_text("pass\n")
            long_name = "a" * 110 + ".png"
            (game / long_name).write_bytes(b"image")
            output = root / "game.tar.gz"
            pack_game(str(game), str(output))
            raw_tar = gzip.open(output, "rb").read()
            with tarfile.open(output) as archive:
                names = archive.getnames()
        self.assertIn(long_name, names)
        self.assertIn(b"././@PaxHeader", raw_tar)


if __name__ == "__main__":
    unittest.main()
