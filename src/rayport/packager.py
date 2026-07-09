import tarfile
import os
from pathlib import Path
from io import BytesIO

SKIP_DIRS = {".git", "__pycache__", ".venv", "venv", "node_modules", "build", ".mypy_cache", ".pytest_cache"}
SKIP_FILES = {".DS_Store"}
SKIP_EXTENSIONS = {".pyc", ".pyo"}


def pack_game(game_dir: str, output_path: str) -> None:
    game_path = Path(game_dir).resolve()
    if not game_path.is_dir():
        raise FileNotFoundError(f"Game directory not found: {game_dir}")
    if not (game_path / "main.py").exists():
        raise FileNotFoundError(f"main.py not found in {game_dir}")

    with tarfile.open(output_path, "w:gz") as tar:
        for root, dirs, files in os.walk(game_path):
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith(".")]
            for filename in sorted(files):
                if filename in SKIP_FILES:
                    continue
                if Path(filename).suffix in SKIP_EXTENSIONS:
                    continue
                filepath = Path(root) / filename
                arcname = str(filepath.relative_to(game_path))
                tar.add(filepath, arcname=arcname)
