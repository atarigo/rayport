# Module 05: Development Server

## Purpose

Provide a local HTTP server for testing games in a browser, with file watching
and automatic reloading.

Start it with `rayport dev ./my-game/`.

## Why an HTTP Server Is Required

Browsers do not allow `.wasm` files to load from `file://`, and the Fetch API
is unavailable there. Some WebAssembly features, including
`SharedArrayBuffer`, also require specific HTTP headers.

## How It Works

After `run_dev()` starts:

1. Perform a complete build: package the game, generate the HTML, and copy the
   runtime files to the output directory.
2. Start `FileWatcher`, which checks file modification times once per second.
3. Start the HTTP server and open the browser.
4. Repackage `game.tar.gz` and increment the reload version when an included
   file changes.
5. Poll the `/__reload` endpoint from browser JavaScript once per second and
   reload the page when the version changes.

## HTTP Server Behavior

- Add `Cross-Origin-Opener-Policy: same-origin` and
  `Cross-Origin-Embedder-Policy: require-corp` to every response.
- Serve `.wasm` files as `Content-Type: application/wasm`.
- Inject the live-reload script into the `index.html` response.
- Return `{"v": <reload_version>}` from the `/__reload` endpoint.
- Omit `/__reload` requests from the server log.

## FileWatcher

The polling-based watcher checks `st_mtime` for all files in the game
directory once per second and detects additions, modifications, and deletions.
Only changes accepted by the `rayport.toml` package rules trigger repackaging.
If the output is inside the game project, `FileWatcher` skips that complete
subtree to prevent generated files from causing a reload loop. Changes to the
configuration file itself require restarting the development server.

The watcher runs in a daemon thread and stops automatically when the main
thread exits.

## CLI Options

- `game_dir`: game project directory.
- `--output` / `-o`: output directory, defaulting to `build`.
- `--title` / `-t`: override the game title.
- `--presentation`: override the canvas presentation mode.
- `--background`: override the page background color.
- `--width` / `-W` and `--height` / `-H`: legacy initial canvas size; both
  options must be provided together.
- `--port` / `-p`: server port, defaulting to 8080.
- `--force-output`: explicitly allow replacement of a non-empty output without
  a `.rayport-output` marker.

## Related Files

- `src/rayport/dev_server.py`: server, `FileWatcher`, and live-reload logic.
- `src/rayport/cli.py`: CLI entry point for `rayport dev`.
