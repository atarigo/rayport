import tarfile
import os
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
    size: int = 0


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


def inspect_game(
    game_dir: str,
    exclude: tuple[str, ...] = (),
    include: tuple[str, ...] = (),
    ignore_paths: tuple[str | Path, ...] = (),
) -> list[FileDecision]:
    game_path = Path(game_dir).resolve()
    if not game_path.is_dir():
        raise FileNotFoundError(f"Game directory not found: {game_dir}")

    ignored = tuple(Path(path).resolve() for path in ignore_paths)
    decisions = []
    for root, dirs, files in os.walk(game_path):
        dirs[:] = sorted(
            directory
            for directory in dirs
            if not any((Path(root) / directory).resolve() == path for path in ignored)
        )
        for filename in sorted(files):
            filepath = Path(root) / filename
            if any(filepath.resolve() == path for path in ignored):
                continue
            relative = filepath.relative_to(game_path).as_posix()
            decision = decide_file(relative, exclude=exclude, include=include)
            decisions.append(
                FileDecision(decision.path, decision.included, decision.reason, filepath.stat().st_size)
            )
    return decisions


def pack_game(
    game_dir: str,
    output_path: str,
    exclude: tuple[str, ...] = (),
    include: tuple[str, ...] = (),
    ignore_paths: tuple[str | Path, ...] = (),
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

    with tarfile.open(output_path, "w:gz") as tar:
        for decision in inspect_game(
            str(game_path),
            exclude=exclude,
            include=include,
            ignore_paths=ignore_paths,
        ):
            source_file = game_path / decision.path
            if decision.included and source_file.resolve() != output_file:
                tar.add(source_file, arcname=decision.path)
