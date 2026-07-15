import tempfile
import unittest
from pathlib import Path

from rayport.cli import format_size
from rayport.config import ConfigError, load_config


class ConfigTests(unittest.TestCase):
    def test_human_readable_sizes(self):
        self.assertEqual(format_size(12), "12 B")
        self.assertEqual(format_size(1536), "1.5 KiB")

    def test_defaults_when_config_is_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            config = load_config(tmp)
        self.assertEqual(config.web.presentation, "stretch")
        self.assertEqual(config.package.exclude, ())

    def test_loads_web_and_package_settings(self):
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "rayport.toml").write_text(
                """
config-version = 1
[web]
title = "Example"
presentation = "fit"
background = "black"
[package]
exclude = ["tests/**"]
include = ["tests/runtime_data/**"]
""",
                encoding="utf-8",
            )
            config = load_config(tmp)
        self.assertEqual(config.web.title, "Example")
        self.assertEqual(config.web.presentation, "fit")
        self.assertEqual(config.package.exclude, ("tests/**",))

    def test_rejects_unknown_keys(self):
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "rayport.toml").write_text("mystery = true\n", encoding="utf-8")
            with self.assertRaisesRegex(ConfigError, "Unknown key"):
                load_config(tmp)

    def test_rejects_unknown_presentation(self):
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "rayport.toml").write_text(
                '[web]\npresentation = "fullscreen"\n', encoding="utf-8"
            )
            with self.assertRaisesRegex(ConfigError, "web.presentation"):
                load_config(tmp)


if __name__ == "__main__":
    unittest.main()
