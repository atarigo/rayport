from string import Template
from pathlib import Path

TEMPLATE_DIR = Path(__file__).parent / "templates"


def generate_html(output_path: str, title: str = "rayport game", width: int | None = None, height: int | None = None) -> None:
    template_path = TEMPLATE_DIR / "index.html"
    if width is not None and height is not None:
        template = Template((TEMPLATE_DIR / "index_fixed.html").read_text())
        html = template.substitute(title=title, width=str(width), height=str(height))
    else:
        template = Template(template_path.read_text())
        html = template.substitute(title=title)
    Path(output_path).write_text(html)
