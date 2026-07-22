import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from rayport.runtime_files import (
    NOTICE_FILENAMES,
    RUNTIME_FILENAMES,
    copy_runtime_distribution,
    find_runtime_dir,
)


class RuntimeFilesTests(unittest.TestCase):
    def test_environment_override(self):
        with tempfile.TemporaryDirectory() as tmp:
            runtime = Path(tmp)
            for filename in RUNTIME_FILENAMES:
                (runtime / filename).write_bytes(b"test")
            with patch.dict(os.environ, {"RAYPORT_RUNTIME": str(runtime)}):
                self.assertEqual(find_runtime_dir(), runtime.resolve())

    def test_incomplete_override_falls_back_to_source_runtime(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch.dict(os.environ, {"RAYPORT_RUNTIME": tmp}):
                found = find_runtime_dir()
        self.assertTrue(all((found / filename).is_file() for filename in RUNTIME_FILENAMES))

    def test_copy_runtime_distribution_includes_license_notices(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            runtime = root / "runtime"
            output = root / "output"
            runtime.mkdir()
            output.mkdir()
            for filename in (*RUNTIME_FILENAMES, *NOTICE_FILENAMES):
                (runtime / filename).write_text(filename)

            copy_runtime_distribution(runtime, output)

            self.assertEqual(
                sorted(path.name for path in output.iterdir()),
                sorted((*RUNTIME_FILENAMES, "rayport-licenses")),
            )
            self.assertEqual(
                sorted(path.name for path in (output / "rayport-licenses").iterdir()),
                sorted(NOTICE_FILENAMES),
            )


if __name__ == "__main__":
    unittest.main()
