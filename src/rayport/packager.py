import tarfile
import os
from dataclasses import dataclass
from fnmatch import fnmatchcase
import io
import json
from pathlib import Path
import re
import stat

from rayport.dependencies import BundledDependency, collect_bundled_dependencies

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


def _entry_type(path: Path) -> str:
    mode = path.lstat().st_mode
    if stat.S_ISLNK(mode):
        return "symbolic link"
    if stat.S_ISREG(mode):
        return "regular file"
    if stat.S_ISDIR(mode):
        return "directory"
    if stat.S_ISFIFO(mode):
        return "FIFO"
    if stat.S_ISSOCK(mode):
        return "socket"
    if stat.S_ISCHR(mode):
        return "character device"
    if stat.S_ISBLK(mode):
        return "block device"
    return "unknown file type"


def _raise_unsupported_entries(entries: list[tuple[str, str]]) -> None:
    if not entries:
        return
    details = "\n".join(f"  {path}: {entry_type}" for path, entry_type in entries)
    raise ValueError(
        "Unsupported filesystem entries would be packaged:\n"
        f"{details}\n"
        "Rayport only packages regular files and directories."
    )


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
    unsupported = []
    for root, dirs, files in os.walk(game_path):
        dirs[:] = sorted(
            directory
            for directory in dirs
            if not any((Path(root) / directory).resolve() == path for path in ignored)
        )
        for directory in dirs:
            directory_path = Path(root) / directory
            entry_type = _entry_type(directory_path)
            if entry_type == "directory":
                continue
            relative = directory_path.relative_to(game_path).as_posix()
            decision = decide_file(relative, exclude=exclude, include=include)
            if decision.included:
                unsupported.append((relative, entry_type))

        for filename in sorted(files):
            filepath = Path(root) / filename
            if any(filepath.resolve() == path for path in ignored):
                continue
            relative = filepath.relative_to(game_path).as_posix()
            decision = decide_file(relative, exclude=exclude, include=include)
            entry_type = _entry_type(filepath)
            if decision.included and entry_type != "regular file":
                unsupported.append((relative, entry_type))
            decisions.append(
                FileDecision(decision.path, decision.included, decision.reason, filepath.lstat().st_size)
            )
    _raise_unsupported_entries(unsupported)
    return decisions


def pack_game(
    game_dir: str,
    output_path: str,
    exclude: tuple[str, ...] = (),
    include: tuple[str, ...] = (),
    ignore_paths: tuple[str | Path, ...] = (),
) -> tuple[BundledDependency, ...]:
    game_path = Path(game_dir).resolve()
    if not game_path.is_dir():
        raise FileNotFoundError(f"Game directory not found: {game_dir}")
    if not (game_path / "main.py").is_file():
        raise FileNotFoundError(f"main.py not found in {game_dir}")
    main_decision = decide_file("main.py", exclude=exclude, include=include)
    if not main_decision.included:
        raise ValueError(f"main.py cannot be excluded ({main_decision.reason})")

    output_file = Path(output_path).resolve()

    decisions = inspect_game(
        str(game_path),
        exclude=exclude,
        include=include,
        ignore_paths=ignore_paths,
    )
    included_paths = tuple(
        decision.path
        for decision in decisions
        if decision.included
    )
    dependencies = collect_bundled_dependencies(game_path, included_paths)
    game_archive_paths = set(included_paths)

    with tarfile.open(output_path, "w:gz") as tar:
        for decision in decisions:
            source_file = game_path / decision.path
            if decision.included and source_file.resolve() != output_file:
                entry_type = _entry_type(source_file)
                if entry_type != "regular file":
                    _raise_unsupported_entries([(decision.path, entry_type)])
                tar.add(source_file, arcname=decision.path, recursive=False)
        for dependency in dependencies:
            for dependency_file in (*dependency.files, *dependency.license_files):
                if dependency_file.archive_path in game_archive_paths:
                    raise ValueError(
                        "Python dependency file conflicts with a game file: "
                        f"{dependency_file.archive_path}"
                    )
                tar.add(
                    dependency_file.source,
                    arcname=dependency_file.archive_path,
                    recursive=False,
                )
                game_archive_paths.add(dependency_file.archive_path)
        if dependencies:
            manifest = {
                "dependencies": [
                    {
                        "import": dependency.import_name,
                        "distribution": dependency.distribution_name,
                        "version": dependency.version,
                        "skipped_native_files": list(dependency.skipped_native_files),
                    }
                    for dependency in dependencies
                ]
            }
            payload = (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode()
            info = tarfile.TarInfo(".rayport/dependencies.json")
            info.size = len(payload)
            info.mode = 0o644
            tar.addfile(info, io.BytesIO(payload))
    return dependencies
