from __future__ import annotations

import os
from pathlib import Path
import shutil
import sysconfig


RUNTIME_FILENAMES = ("main.wasm", "main.js", "main.data")
NOTICE_FILENAMES = ("LICENSE", "THIRD_PARTY_NOTICES.md")
THIRD_PARTY_LICENSE_DIRNAME = "third_party_licenses"


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


def find_notice_dir(runtime_dir: Path) -> Path:
    package_dir = Path(__file__).resolve().parent
    candidates = (runtime_dir, package_dir.parent.parent)
    for candidate in candidates:
        if (
            all((candidate / filename).is_file() for filename in NOTICE_FILENAMES)
            and (candidate / THIRD_PARTY_LICENSE_DIRNAME).is_dir()
        ):
            return candidate

    checked = "\n  ".join(str(path) for path in candidates)
    raise FileNotFoundError(
        "Rayport license files were not found. Checked:\n"
        f"  {checked}\n"
        "Reinstall Rayport from a complete distribution."
    )


def copy_runtime_distribution(runtime_dir: Path, output_dir: Path) -> None:
    for filename in RUNTIME_FILENAMES:
        shutil.copy2(runtime_dir / filename, output_dir / filename)

    notice_dir = find_notice_dir(runtime_dir)
    output_notice_dir = output_dir / "rayport-licenses"
    output_notice_dir.mkdir(exist_ok=True)
    for filename in NOTICE_FILENAMES:
        shutil.copy2(notice_dir / filename, output_notice_dir / filename)
    shutil.copytree(
        notice_dir / THIRD_PARTY_LICENSE_DIRNAME,
        output_notice_dir / THIRD_PARTY_LICENSE_DIRNAME,
        dirs_exist_ok=True,
    )
