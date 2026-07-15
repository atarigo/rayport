from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
import tomllib


CONFIG_FILENAME = "rayport.toml"
PRESENTATION_MODES = {"stretch", "fit", "pixel-perfect", "native"}
CSS_COLOR = re.compile(r"^#[0-9a-fA-F]{3,8}$|^[a-zA-Z]+$")


class ConfigError(ValueError):
    """Raised when a rayport configuration file is invalid."""


@dataclass(frozen=True)
class WebConfig:
    title: str = "rayport game"
    presentation: str = "stretch"
    background: str = "#1a1a2e"


@dataclass(frozen=True)
class PackageConfig:
    exclude: tuple[str, ...] = ()
    include: tuple[str, ...] = ()


@dataclass(frozen=True)
class RayportConfig:
    web: WebConfig = WebConfig()
    package: PackageConfig = PackageConfig()
    path: Path | None = None


def _reject_unknown(table: dict, allowed: set[str], location: str) -> None:
    unknown = sorted(set(table) - allowed)
    if unknown:
        names = ", ".join(unknown)
        raise ConfigError(f"Unknown key(s) in {location}: {names}")


def _string_list(value: object, location: str) -> tuple[str, ...]:
    if not isinstance(value, list) or not all(isinstance(item, str) and item for item in value):
        raise ConfigError(f"{location} must be an array of non-empty strings")
    return tuple(value)


def validate_web_values(title: object, presentation: object, background: object) -> None:
    if not isinstance(title, str) or not title:
        raise ConfigError("web.title must be a non-empty string")
    if presentation not in PRESENTATION_MODES:
        choices = ", ".join(sorted(PRESENTATION_MODES))
        raise ConfigError(f"web.presentation must be one of: {choices}")
    if not isinstance(background, str) or not CSS_COLOR.fullmatch(background):
        raise ConfigError("web.background must be a CSS color name or hexadecimal color")


def load_config(game_dir: str | Path, config_path: str | Path | None = None) -> RayportConfig:
    game_path = Path(game_dir).resolve()
    path = Path(config_path).resolve() if config_path else game_path / CONFIG_FILENAME
    if not path.exists():
        if config_path:
            raise ConfigError(f"Configuration file not found: {path}")
        return RayportConfig()

    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError) as exc:
        raise ConfigError(f"Could not read {path}: {exc}") from exc

    if not isinstance(data, dict):
        raise ConfigError(f"Invalid configuration in {path}")
    _reject_unknown(data, {"config-version", "web", "package"}, str(path))

    version = data.get("config-version", 1)
    if version != 1:
        raise ConfigError(f"Unsupported config-version {version!r} in {path}; expected 1")

    web_data = data.get("web", {})
    package_data = data.get("package", {})
    if not isinstance(web_data, dict):
        raise ConfigError("[web] must be a TOML table")
    if not isinstance(package_data, dict):
        raise ConfigError("[package] must be a TOML table")

    _reject_unknown(web_data, {"title", "presentation", "background"}, "[web]")
    _reject_unknown(package_data, {"exclude", "include"}, "[package]")

    defaults = WebConfig()
    title = web_data.get("title", defaults.title)
    presentation = web_data.get("presentation", defaults.presentation)
    background = web_data.get("background", defaults.background)
    validate_web_values(title, presentation, background)

    exclude = _string_list(package_data.get("exclude", []), "package.exclude")
    include = _string_list(package_data.get("include", []), "package.include")
    return RayportConfig(
        web=WebConfig(title=title, presentation=presentation, background=background),
        package=PackageConfig(exclude=exclude, include=include),
        path=path,
    )
