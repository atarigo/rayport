# Rayport Documentation

Rayport packages Python raylib games to run in a browser.

The CPython interpreter and raylib engine are compiled into a WebAssembly
binary. The user's Python game code is loaded through a virtual filesystem and
executed by CPython inside WebAssembly. Users do not need Emscripten or a C
toolchain.

## Modules

| Module | Description |
|---|---|
| [01-wasm-base](01-wasm-base.md) | Compile CPython, raylib, and CFFI bindings into a WebAssembly runtime. |
| [02-project-packager](02-project-packager.md) | Collect game files and assets into a tar.gz archive. |
| [03-game-loop](03-game-loop.md) | Keep the game loop responsive in the browser with ASYNCIFY. |
| [04-html-shell](04-html-shell.md) | Generate the HTML page that hosts the game. |
| [05-dev-server](05-dev-server.md) | Serve the game locally with file watching and automatic reloads. |
| [07-runtime-launcher](07-runtime-launcher.md) | Run the user's game after WebAssembly starts. |
| [08-project-config](08-project-config.md) | Configure Web presentation and package include/exclude rules. |

## Other Documents

| Document | Description |
|---|---|
| [architecture](architecture.md) | Overall architecture and build process. |
| [history/poc-log](history/poc-log.md) | Historical proof-of-concept validation log. |
