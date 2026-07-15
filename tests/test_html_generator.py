import tempfile
import unittest
from pathlib import Path

from rayport.html_generator import generate_html


class HtmlGeneratorTests(unittest.TestCase):
    def test_stretch_uses_viewport_css_without_resizing_render_target(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp, "index.html")
            generate_html(str(output), title="A & B", presentation="stretch")
            content = output.read_text(encoding="utf-8")
        self.assertIn("<title>A &amp; B</title>", content)
        self.assertIn('presentationMode = "stretch"', content)
        self.assertIn('canvasEl.style.width = "100vw"', content)
        self.assertNotIn("canvasEl.width =", content)
        self.assertNotIn("canvasEl.height =", content)

    def test_mouse_coordinates_are_mapped_to_raylib_window(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp, "index.html")
            generate_html(str(output), presentation="stretch")
            content = output.read_text(encoding="utf-8")
        self.assertIn("Browser.calculateMouseCoords = function(pageX, pageY)", content)
        self.assertIn("GLFW.active.width || canvasEl.width", content)
        self.assertIn("logicalWidth / rect.width", content)

    def test_fit_and_pixel_perfect_logic_is_emitted(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp, "index.html")
            generate_html(str(output), presentation="fit")
            content = output.read_text(encoding="utf-8")
        self.assertIn('presentationMode === "pixel-perfect"', content)
        self.assertIn("Math.min(window.innerWidth", content)

    def test_pax_paths_and_unsafe_paths_are_handled(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp, "index.html")
            generate_html(str(output))
            content = output.read_text(encoding="utf-8")
        self.assertIn("function parsePaxRecords(bytes)", content)
        self.assertIn("if (metadata.path) name = metadata.path", content)
        self.assertIn('parts.includes("..")', content)
        self.assertIn("Unsupported tar entry type", content)

    def test_width_and_height_must_be_paired(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError, "provided together"):
                generate_html(str(Path(tmp, "index.html")), width=800)


if __name__ == "__main__":
    unittest.main()
