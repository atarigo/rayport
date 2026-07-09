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

Start a dev server with live reload:

```bash
rayport dev ./my-game/
```

## Documentation

See [documentation/](documentation/README.md) for architecture details and module descriptions.
