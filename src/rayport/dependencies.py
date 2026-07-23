from __future__ import annotations

import ast
from dataclasses import dataclass
from email.parser import Parser
import importlib.util
from pathlib import Path
import re
import stat
import sys


RUNTIME_MODULES = frozenset({"_cffi_backend", "_raylib_cffi", "raylib"})
NATIVE_SUFFIXES = frozenset({".dll", ".dylib", ".pyd", ".so"})


@dataclass(frozen=True)
class DependencyFile:
    source: Path
    archive_path: str


@dataclass(frozen=True)
class BundledDependency:
    import_name: str
    distribution_name: str
    version: str
    files: tuple[DependencyFile, ...]
    license_files: tuple[DependencyFile, ...]
    skipped_native_files: tuple[str, ...]


def _module_name(relative_path: str) -> str | None:
    path = Path(relative_path)
    if path.suffix != ".py":
        return None
    parts = list(path.with_suffix("").parts)
    if parts[-1] == "__init__":
        parts.pop()
    return ".".join(parts)


def _queue_local_module(name: str, modules: dict[str, Path], queue: list[str]) -> bool:
    found = False
    parts = name.split(".")
    for length in range(1, len(parts) + 1):
        candidate = ".".join(parts[:length])
        if candidate in modules:
            queue.append(candidate)
            found = True
    return found


def discover_external_imports(
    game_path: Path,
    included_paths: tuple[str, ...],
) -> tuple[str, ...]:
    modules = {}
    package_modules = set()
    for relative in included_paths:
        name = _module_name(relative)
        if name is None:
            continue
        modules[name] = game_path / relative
        if Path(relative).name == "__init__.py":
            package_modules.add(name)

    if "main" not in modules:
        raise ValueError("main.py is not available for dependency analysis")

    local_roots = {name.partition(".")[0] for name in modules}
    external = set()
    queue = ["main"]
    visited = set()

    while queue:
        module = queue.pop()
        if module in visited:
            continue
        visited.add(module)
        path = modules[module]
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except (OSError, UnicodeError, SyntaxError) as exc:
            raise ValueError(f"Could not analyze Python imports in {path}: {exc}") from exc

        package = module if module in package_modules else module.rpartition(".")[0]
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                if node.level:
                    if not package:
                        continue
                    relative_name = "." * node.level + (node.module or "")
                    try:
                        base = importlib.util.resolve_name(relative_name, package)
                    except (ImportError, ValueError):
                        continue
                else:
                    base = node.module or ""
                imported_names = [base] if base else []
                imported_names.extend(
                    f"{base}.{alias.name}" if base else alias.name
                    for alias in node.names
                    if alias.name != "*"
                )
            else:
                continue

            for imported in imported_names:
                root = imported.partition(".")[0]
                if root in local_roots:
                    _queue_local_module(imported, modules, queue)
                elif root not in sys.stdlib_module_names and root not in RUNTIME_MODULES:
                    external.add(root)

    return tuple(sorted(external))


def find_project_site_packages(game_path: Path) -> tuple[Path, ...]:
    candidates = []
    for environment_name in (".venv", "venv"):
        environment = game_path / environment_name
        candidates.extend(sorted(environment.glob("lib/python*/site-packages")))
        candidates.append(environment / "Lib" / "site-packages")
        candidates.append(environment / "site-packages")
    return tuple(
        candidate.resolve()
        for candidate in candidates
        if candidate.is_dir()
    )


def _find_module_source(import_name: str, site_packages: tuple[Path, ...]) -> tuple[Path, Path]:
    for site in site_packages:
        package = site / import_name
        module = site / f"{import_name}.py"
        if package.is_dir():
            return site, package
        if module.is_file():
            return site, module
    searched = ", ".join(str(path) for path in site_packages) or "no project virtual environment"
    raise ValueError(
        f"Third-party Python module {import_name!r} is required but was not found "
        f"in the project environment ({searched}). Run the project's dependency "
        "installation first."
    )


def _distribution_for_import(site: Path, import_name: str) -> tuple[str, str, Path | None]:
    for dist_info in sorted(site.glob("*.dist-info")):
        top_level = dist_info / "top_level.txt"
        if not top_level.is_file():
            continue
        names = {
            line.strip()
            for line in top_level.read_text(encoding="utf-8", errors="replace").splitlines()
            if line.strip()
        }
        if import_name not in names:
            continue
        metadata_path = dist_info / "METADATA"
        if metadata_path.is_file():
            metadata = Parser().parsestr(
                metadata_path.read_text(encoding="utf-8", errors="replace")
            )
            distribution_name = metadata.get("Name") or dist_info.name
            version = metadata.get("Version") or "unknown"
        else:
            distribution_name = dist_info.name
            version = "unknown"
        return distribution_name, version, dist_info
    return import_name, "unknown", None


def _safe_distribution_name(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "-", name).strip("-") or "dependency"


def _regular_file(path: Path) -> bool:
    return stat.S_ISREG(path.lstat().st_mode)


def _collect_module_files(site: Path, source: Path) -> tuple[tuple[DependencyFile, ...], tuple[str, ...]]:
    if source.is_symlink():
        raise ValueError(
            f"Unsupported symbolic link for Python dependency {source.name!r}: {source}"
        )
    paths = [source] if source.is_file() else sorted(source.rglob("*"))
    files = []
    skipped_native = []
    for path in paths:
        if path.is_dir():
            continue
        relative = path.relative_to(site).as_posix()
        if "__pycache__" in path.parts or path.suffix == ".pyc":
            continue
        if path.suffix.lower() in NATIVE_SUFFIXES:
            skipped_native.append(relative)
            continue
        if path.is_symlink() or not _regular_file(path):
            raise ValueError(
                f"Unsupported file in Python dependency {source.name!r}: {relative}"
            )
        files.append(DependencyFile(path, relative))

    if not any(file.source.suffix == ".py" for file in files):
        raise ValueError(
            f"Third-party module {source.name!r} has no pure Python implementation. "
            "Native extension modules cannot run in the WebAssembly runtime."
        )
    return tuple(files), tuple(skipped_native)


def _collect_license_files(
    dist_info: Path | None,
    distribution_name: str,
) -> tuple[DependencyFile, ...]:
    if dist_info is None:
        return ()
    candidates = []
    for path in sorted(dist_info.rglob("*")):
        if not path.is_file():
            continue
        upper_name = path.name.upper()
        if "LICENSE" not in upper_name and "COPYING" not in upper_name and "NOTICE" not in upper_name:
            continue
        relative = path.relative_to(dist_info).as_posix()
        archive_path = (
            f".rayport/dependencies/{_safe_distribution_name(distribution_name)}/{relative}"
        )
        candidates.append(DependencyFile(path, archive_path))
    return tuple(candidates)


def collect_bundled_dependencies(
    game_path: Path,
    included_paths: tuple[str, ...],
) -> tuple[BundledDependency, ...]:
    imports = discover_external_imports(game_path, included_paths)
    if not imports:
        return ()

    site_packages = find_project_site_packages(game_path)
    dependencies = []
    for import_name in imports:
        site, source = _find_module_source(import_name, site_packages)
        distribution_name, version, dist_info = _distribution_for_import(site, import_name)
        files, skipped_native = _collect_module_files(site, source)
        dependencies.append(
            BundledDependency(
                import_name=import_name,
                distribution_name=distribution_name,
                version=version,
                files=files,
                license_files=_collect_license_files(dist_info, distribution_name),
                skipped_native_files=skipped_native,
            )
        )
    return tuple(dependencies)
