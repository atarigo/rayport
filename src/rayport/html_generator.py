import html
import json
from string import Template
from pathlib import Path

from rayport.config import validate_web_values

TEMPLATE_DIR = Path(__file__).parent / "templates"


def generate_html(
    output_path: str,
    title: str = "rayport game",
    width: int | None = None,
    height: int | None = None,
    presentation: str = "stretch",
    background: str = "#1a1a2e",
) -> None:
    validate_web_values(title, presentation, background)
    template_path = TEMPLATE_DIR / "index.html"
    if (width is None) != (height is None):
        raise ValueError("width and height must be provided together")
    if width is not None and (width <= 0 or height <= 0):
        raise ValueError("width and height must be positive")
    canvas_size = "" if width is None else f' width="{width}" height="{height}"'
    template = Template(template_path.read_text(encoding="utf-8"))
    output = template.substitute(
        title=html.escape(title),
        background=background,
        canvas_size=canvas_size,
        presentation=json.dumps(presentation),
    )
    Path(output_path).write_text(output, encoding="utf-8")
