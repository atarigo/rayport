import tarfile
import os
import shutil
import tempfile
from dataclasses import dataclass
from fnmatch import fnmatchcase
from pathlib import Path
import re

DEFAULT_EXCLUDE = (
    ".*",
    ".git",
    "__pycache__",
    ".venv",
    "venv",
    "node_modules",
    "build",
    ".mypy_cache",
    ".pytest_cache",
    ".DS_Store",
    "*.pyc",
    "*.pyo",
    "rayport.toml",
)


@dataclass(frozen=True)
class FileDecision:
    path: str
    included: bool
    reason: str


def _matches(path: str, pattern: str) -> bool:
    normalized = pattern.replace("\\", "/").removeprefix("./").rstrip("/")
    if not normalized:
        return False
    if "/" not in normalized:
        return any(fnmatchcase(part, normalized) for part in path.split("/"))

    expression = ""
    index = 0
    while index < len(normalized):
        if normalized[index:index + 3] == "**/":
            expression += "(?:.*/)?"
            index += 3
        elif normalized[index:index + 2] == "**":
            expression += ".*"
            index += 2
        elif normalized[index] == "*":
            expression += "[^/]*"
            index += 1
        elif normalized[index] == "?":
            expression += "[^/]"
            index += 1
        else:
            expression += re.escape(normalized[index])
            index += 1
    return re.fullmatch(expression, path) is not None


def decide_file(path: str, exclude: tuple[str, ...] = (), include: tuple[str, ...] = ()) -> FileDecision:
    path = path.replace("\\", "/").removeprefix("./")
    for pattern in include:
        if _matches(path, pattern):
            return FileDecision(path, True, f"included by pattern {pattern!r}")
    for pattern in (*DEFAULT_EXCLUDE, *exclude):
        if _matches(path, pattern):
            source = "default rule" if pattern in DEFAULT_EXCLUDE else "exclude pattern"
            return FileDecision(path, False, f"{source} {pattern!r}")
    return FileDecision(path, True, "included by default")


def inspect_game(game_dir: str, exclude: tuple[str, ...] = (), include: tuple[str, ...] = ()) -> list[FileDecision]:
    game_path = Path(game_dir).resolve()
    if not game_path.is_dir():
        raise FileNotFoundError(f"Game directory not found: {game_dir}")

    decisions = []
    for root, dirs, files in os.walk(game_path):
        dirs.sort()
        for filename in sorted(files):
            filepath = Path(root) / filename
            relative = filepath.relative_to(game_path).as_posix()
            decisions.append(decide_file(relative, exclude=exclude, include=include))
    return decisions


def pack_game(
    game_dir: str,
    output_path: str,
    optimize: bool = False,
    exclude: tuple[str, ...] = (),
    include: tuple[str, ...] = (),
) -> None:
    game_path = Path(game_dir).resolve()
    if not game_path.is_dir():
        raise FileNotFoundError(f"Game directory not found: {game_dir}")
    if not (game_path / "main.py").exists():
        raise FileNotFoundError(f"main.py not found in {game_dir}")
    main_decision = decide_file("main.py", exclude=exclude, include=include)
    if not main_decision.included:
        raise ValueError(f"main.py cannot be excluded ({main_decision.reason})")

    output_file = Path(output_path).resolve()

    pack_source = game_path
    tmp_dir = None

    if optimize:
        from rayport.optimizer import optimize_assets
        tmp_dir = tempfile.mkdtemp(prefix="rayport_opt_")
        print("Optimizing assets...")
        optimize_assets(str(game_path), tmp_dir, exclude=exclude, include=include)
        pack_source = Path(tmp_dir)

    try:
        with tarfile.open(output_path, "w:gz") as tar:
            for decision in inspect_game(str(pack_source), exclude=exclude, include=include):
                source_file = pack_source / decision.path
                if decision.included and source_file.resolve() != output_file:
                    tar.add(source_file, arcname=decision.path)
    finally:
        if tmp_dir:
            shutil.rmtree(tmp_dir, ignore_errors=True)
