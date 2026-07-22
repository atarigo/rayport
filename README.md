# rayport

Package raylib Python games to run in the browser.

## How it works

The tool bundles a CPython interpreter and raylib engine compiled to WebAssembly. User game code (.py files and assets) is loaded into a virtual filesystem at runtime and executed by the wasm Python interpreter.

## Prerequisites

- Python 3.13+
- git

## Building the runtime

The runtime contains the CPython wasm interpreter. Build it once; rebuild only when upgrading CPython or raylib.

Emscripten SDK 和其他依賴會自動下載到 `/tmp/rayport-emsdk`，不需要預先安裝，也不會修改 shell 環境。

```bash
make runtime
```

如需自訂路徑或版本，建立 `build.conf`（參考 `build.conf.example`）。

## Usage

Build a game for web deployment:

```bash
rayport build ./my-game/
```

Generated directories contain a `.rayport-output` marker. Rayport refuses to
delete a non-empty directory without that marker unless `--force-output` is
passed explicitly. An output inside the game project (such as `dist/`) is
automatically excluded from packaging and live reload. The output may never
equal or contain the game source directory.

Start a dev server with live reload:

```bash
rayport dev ./my-game/
```

Inspect exactly which files will be packaged:

```bash
rayport inspect ./my-game/
rayport inspect ./my-game/ --excluded
rayport inspect ./my-game/ --explain tests/test_game.py
rayport inspect ./my-game/ --sizes
```

## Project configuration

Place `rayport.toml` in the game project root:

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

- `stretch` (default): display the canvas at `100vw` by `100dvh` without changing raylib's render resolution.
- `fit`: fill as much of the browser viewport as possible while preserving aspect ratio.
- `pixel-perfect`: use integer scaling when the viewport is large enough.
- `native`: display one CSS pixel per render pixel.

The game owns its render resolution through `InitWindow()`. Rayport only controls
the canvas's CSS presentation size. Command-line options override `rayport.toml`,
which overrides Rayport defaults.

`rayport.toml` is packaging metadata and is not included in `game.tar.gz`.

Rayport packages assets exactly as provided. It never converts image or audio
formats implicitly. Use `rayport inspect GAME --sizes` for a read-only report of
the largest packaged files. This report is opt-in and is not run automatically
after `rayport build` or during `rayport dev`. Optimize source assets explicitly
in your own asset pipeline when needed.

Installed distributions include the prebuilt runtime under
`share/rayport/runtime`. For a custom runtime, set the `RAYPORT_RUNTIME`
environment variable to a directory containing `main.wasm`, `main.js`, and
`main.data`.

## Documentation

See [documentation/](documentation/README.md) for architecture details and module descriptions.

## License

Rayport is licensed under the Eclipse Public License 2.0. Generated web builds
include `rayport-licenses/LICENSE` and
`rayport-licenses/THIRD_PARTY_NOTICES.md` for the bundled runtime.
Rayport's license does not apply to an independent game merely packaged by the
tool. See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) for the raylib and
raylib-python-cffi notices and source locations.
