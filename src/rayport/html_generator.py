from string import Template
from pathlib import Path

TEMPLATE_DIR = Path(__file__).parent / "templates"


def generate_html(output_path: str, title: str = "rayport game", width: int = 800, height: int = 450) -> None:
    template_path = TEMPLATE_DIR / "index.html"
    template = Template(template_path.read_text())
    html = template.substitute(title=title, width=str(width), height=str(height))
    Path(output_path).write_text(html)
