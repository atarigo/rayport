import tarfile
import os
import shutil
import tempfile
from pathlib import Path
from io import BytesIO

SKIP_DIRS = {".git", "__pycache__", ".venv", "venv", "node_modules", "build", ".mypy_cache", ".pytest_cache"}
SKIP_FILES = {".DS_Store"}
SKIP_EXTENSIONS = {".pyc", ".pyo"}


def pack_game(game_dir: str, output_path: str, optimize: bool = False) -> None:
    game_path = Path(game_dir).resolve()
    if not game_path.is_dir():
        raise FileNotFoundError(f"Game directory not found: {game_dir}")
    if not (game_path / "main.py").exists():
        raise FileNotFoundError(f"main.py not found in {game_dir}")

    pack_source = game_path
    tmp_dir = None

    if optimize:
        from rayport.optimizer import optimize_assets
        tmp_dir = tempfile.mkdtemp(prefix="rayport_opt_")
        print("Optimizing assets...")
        optimize_assets(str(game_path), tmp_dir)
        pack_source = Path(tmp_dir)

    try:
        with tarfile.open(output_path, "w:gz") as tar:
            for root, dirs, files in os.walk(pack_source):
                dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith(".")]
                for filename in sorted(files):
                    if filename in SKIP_FILES:
                        continue
                    if Path(filename).suffix in SKIP_EXTENSIONS:
                        continue
                    filepath = Path(root) / filename
                    arcname = str(filepath.relative_to(pack_source))
                    tar.add(filepath, arcname=arcname)
    finally:
        if tmp_dir:
            shutil.rmtree(tmp_dir, ignore_errors=True)
