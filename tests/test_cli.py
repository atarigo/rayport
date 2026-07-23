import contextlib
import io
from importlib.metadata import version as package_version
import unittest
from unittest.mock import patch

from rayport.cli import main


class CliTests(unittest.TestCase):
    def test_version_matches_package_metadata(self):
        output = io.StringIO()
        with patch("sys.argv", ["rayport", "--version"]), contextlib.redirect_stdout(output):
            with self.assertRaises(SystemExit) as raised:
                main()

        self.assertEqual(raised.exception.code, 0)
        self.assertEqual(output.getvalue(), f"rayport {package_version('rayport')}\n")


if __name__ == "__main__":
    unittest.main()
