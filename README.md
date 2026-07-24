# Rayport

[![CI](https://github.com/atarigo/rayport/actions/workflows/ci.yml/badge.svg)](https://github.com/atarigo/rayport/actions/workflows/ci.yml)
[![License: EPL-2.0](https://img.shields.io/badge/License-EPL--2.0-blue.svg)](LICENSE)

Package Python raylib games as static files that run in a web browser.

[Website](https://rayport.atarigo.io) · [Live demo](https://rayport.atarigo.io/#example) · [PyPI](https://pypi.org/project/rayport/)

Rayport includes the browser runtime needed to package a game. You do not need
a separate raylib installation or compiler.

## Installation

Install Rayport as an isolated command-line tool:

```bash
uv tool install rayport
```

or:

```bash
pipx install rayport
```

Rayport requires Python 3.13 or newer. Python 3.13 and 3.14 are tested.

## Quick start

Your game directory must contain `main.py`:

```text
my-game/
├── main.py
└── assets/
```

Start a local server with automatic rebuilding:

```bash
rayport dev ./my-game
```

Create a static web build:

```bash
rayport build ./my-game --output dist
```

Upload the contents of `dist/` to a static web server. The generated game must
be served over HTTP or HTTPS; opening `index.html` directly with `file://` is not
supported.

## Commands

Check the installed version:

```bash
rayport --version
```

See which files will be packaged:

```bash
rayport inspect ./my-game
rayport inspect ./my-game --excluded
rayport inspect ./my-game --explain tests/test_game.py
rayport inspect ./my-game --sizes
```

Rayport marks generated directories with `.rayport-output`. It will not replace
an unrelated non-empty directory unless you explicitly pass `--force-output`.

Run `rayport COMMAND --help` for every available option.

## Project configuration

Place `rayport.toml` in the game directory:

```toml
config-version = 1

[web]
title = "My Game"
presentation = "stretch"
background = "#1a1a2e"

[package]
exclude = [
    "tests/**",
    "debug/**",
    "demo/**",
    "screenshots/**",
]
include = []
```

Presentation modes:

- `stretch` fills the browser viewport.
- `fit` preserves the game's aspect ratio.
- `pixel-perfect` uses integer scaling when possible.
- `native` displays one CSS pixel per game pixel.

The game controls its render resolution through `InitWindow()`. Command-line
options override `rayport.toml`, which overrides Rayport defaults.

## Packaging behavior

- `main.py` is required.
- Hidden paths, virtual environments, caches, `node_modules`, `build`, and
  `rayport.toml` are excluded by default.
- Images, audio, and other assets are packaged without conversion.
- Symbolic links, FIFOs, sockets, devices, and other non-regular files are
  rejected when they would be included.
- Rayport follows imports reachable from `main.py` and copies required pure
  Python packages from the game's `.venv` or `venv`.
- Install the game's dependencies before building. Missing packages are
  reported during the build instead of failing later in the browser.
- Native extension files such as `.so` and `.pyd` are skipped because they
  cannot run in the WebAssembly runtime. Packages with a pure Python fallback,
  including PyYAML, can still work.
- Dependency versions, skipped native files, and available license files are
  recorded inside `game.tar.gz` under `.rayport/`.

## Compatibility

- Rayport CLI: Python 3.13 and 3.14 tested on Linux, macOS, and Windows.
- Browser runtime: CPython 3.12.11 and raylib 5.5.
- Browser: Chromium is tested automatically.
- Firefox and Safari have not been verified yet.

Because the browser runtime uses CPython 3.12, game code must be compatible with
Python 3.12 even when the Rayport CLI runs on a newer Python version.

## License

Rayport is licensed under the Eclipse Public License 2.0. Generated builds
include Rayport and third-party license notices. The license does not apply to
independent game code merely packaged by Rayport.

See the
[third-party notices](https://github.com/atarigo/rayport/blob/main/THIRD_PARTY_NOTICES.md)
for additional information.
