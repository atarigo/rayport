import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from rayport.runtime_files import RUNTIME_FILENAMES, find_runtime_dir


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


if __name__ == "__main__":
    unittest.main()
