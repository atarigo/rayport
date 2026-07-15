from __future__ import annotations

import os
from pathlib import Path
import sysconfig


RUNTIME_FILENAMES = ("main.wasm", "main.js", "main.data")


def _is_runtime_dir(path: Path) -> bool:
    return all((path / filename).is_file() for filename in RUNTIME_FILENAMES)


def find_runtime_dir() -> Path:
    candidates = []
    override = os.environ.get("RAYPORT_RUNTIME")
    if override:
        candidates.append(Path(override).expanduser().resolve())

    package_dir = Path(__file__).resolve().parent
    candidates.extend(
        (
            package_dir / "runtime",
            package_dir.parent.parent / "runtime",
            Path(sysconfig.get_path("data")) / "share" / "rayport" / "runtime",
        )
    )
    for candidate in candidates:
        if _is_runtime_dir(candidate):
            return candidate

    checked = "\n  ".join(str(path) for path in candidates)
    raise FileNotFoundError(
        "Rayport runtime files were not found. Checked:\n"
        f"  {checked}\n"
        "Run 'make runtime' for a source checkout or reinstall Rayport."
    )
