import gzip
import os
import tarfile
import tempfile
import unittest
from pathlib import Path

from rayport.packager import decide_file, inspect_game, pack_game


class PackagerTests(unittest.TestCase):
    def _write_distribution(
        self,
        site_packages: Path,
        directory_name: str,
        distribution_name: str,
        version: str,
        top_levels: tuple[str, ...],
    ) -> None:
        dist_info = site_packages / f"{directory_name}.dist-info"
        (dist_info / "licenses").mkdir(parents=True)
        (dist_info / "top_level.txt").write_text("\n".join(top_levels) + "\n")
        (dist_info / "METADATA").write_text(
            f"Metadata-Version: 2.4\nName: {distribution_name}\nVersion: {version}\n"
        )
        (dist_info / "licenses" / "LICENSE").write_text(f"{distribution_name} license\n")

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

    def test_pack_bundles_only_reachable_pure_python_dependencies(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            game = root / "game"
            game.mkdir()
            (game / "main.py").write_text("from app.game import run\nrun()\n")
            (game / "app").mkdir()
            (game / "app" / "__init__.py").write_text("")
            (game / "app" / "game.py").write_text(
                "import yaml\nfrom pyray import init_window\n\ndef run(): pass\n"
            )
            (game / "scripts").mkdir()
            (game / "scripts" / "unused.py").write_text("import numpy\n")

            site_packages = game / ".venv" / "lib" / "python3.13" / "site-packages"
            (site_packages / "yaml").mkdir(parents=True)
            (site_packages / "yaml" / "__init__.py").write_text("value = 1\n")
            (site_packages / "yaml" / "loader.py").write_text("pass\n")
            (site_packages / "yaml" / "_yaml.cpython-313.so").write_bytes(b"native")
            (site_packages / "pyray").mkdir()
            (site_packages / "pyray" / "__init__.py").write_text("init_window = object()\n")
            (site_packages / "numpy").mkdir()
            (site_packages / "numpy" / "__init__.py").write_text("unused = True\n")
            self._write_distribution(
                site_packages,
                "pyyaml-6.0.3",
                "PyYAML",
                "6.0.3",
                ("_yaml", "yaml"),
            )
            self._write_distribution(
                site_packages,
                "raylib-6.0.1.0",
                "raylib",
                "6.0.1.0",
                ("pyray", "raylib"),
            )

            output = root / "game.tar.gz"
            dependencies = pack_game(str(game), str(output))
            with tarfile.open(output) as archive:
                names = set(archive.getnames())

        self.assertEqual(
            [(dependency.import_name, dependency.distribution_name) for dependency in dependencies],
            [("pyray", "raylib"), ("yaml", "PyYAML")],
        )
        self.assertIn("pyray/__init__.py", names)
        self.assertIn("yaml/__init__.py", names)
        self.assertIn("yaml/loader.py", names)
        self.assertNotIn("yaml/_yaml.cpython-313.so", names)
        self.assertNotIn("numpy/__init__.py", names)
        self.assertIn(".rayport/dependencies/raylib/licenses/LICENSE", names)
        self.assertIn(".rayport/dependencies/PyYAML/licenses/LICENSE", names)
        self.assertIn(".rayport/dependencies.json", names)
        self.assertEqual(
            dependencies[1].skipped_native_files,
            ("yaml/_yaml.cpython-313.so",),
        )

    def test_pack_reports_missing_project_dependency_before_browser_startup(self):
        with tempfile.TemporaryDirectory() as tmp:
            game = Path(tmp)
            (game / "main.py").write_text("import missing_package\n")
            with self.assertRaisesRegex(
                ValueError,
                "missing_package.*project environment",
            ):
                pack_game(str(game), str(game / "game.tar.gz"))

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

    def test_rejects_included_symbolic_links_and_lists_the_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            game = root / "game"
            game.mkdir()
            (game / "main.py").write_text("pass\n")
            target = root / "outside.txt"
            target.write_text("outside\n")
            link = game / "assets" / "outside.txt"
            link.parent.mkdir()
            try:
                link.symlink_to(target)
            except OSError as exc:
                self.skipTest(f"symbolic links are unavailable: {exc}")

            output = root / "game.tar.gz"
            with self.assertRaisesRegex(
                ValueError,
                r"assets/outside\.txt: symbolic link",
            ):
                pack_game(str(game), str(output))
            self.assertFalse(output.exists())

    def test_rejects_symbolic_links_to_directories(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            game = root / "game"
            game.mkdir()
            (game / "main.py").write_text("pass\n")
            target = root / "outside-assets"
            target.mkdir()
            link = game / "linked-assets"
            try:
                link.symlink_to(target, target_is_directory=True)
            except OSError as exc:
                self.skipTest(f"symbolic links are unavailable: {exc}")

            with self.assertRaisesRegex(ValueError, r"linked-assets: symbolic link"):
                inspect_game(str(game))

    def test_rejects_included_non_regular_files_and_lists_the_type(self):
        if not hasattr(os, "mkfifo"):
            self.skipTest("FIFOs are unavailable")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            game = root / "game"
            game.mkdir()
            (game / "main.py").write_text("pass\n")
            os.mkfifo(game / "events.pipe")

            with self.assertRaisesRegex(ValueError, r"events\.pipe: FIFO"):
                inspect_game(str(game))

    def test_ignores_unsupported_entries_excluded_from_the_package(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            game = root / "game"
            game.mkdir()
            (game / "main.py").write_text("pass\n")
            target = root / "outside.txt"
            target.write_text("outside\n")
            excluded_dir = game / ".venv"
            excluded_dir.mkdir()
            link = excluded_dir / "python"
            try:
                link.symlink_to(target)
            except OSError as exc:
                self.skipTest(f"symbolic links are unavailable: {exc}")

            decisions = inspect_game(str(game))

        by_path = {item.path: item for item in decisions}
        self.assertFalse(by_path[".venv/python"].included)


if __name__ == "__main__":
    unittest.main()
