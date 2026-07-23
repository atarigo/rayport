# Module 02: Project Packager

## Purpose

Collect a user's game code and assets, such as images, audio, and fonts, and
package them as a browser-downloadable `game.tar.gz`.

## How It Works

`pack_game()` walks the game project directory, applies the default rules and
the rules in `rayport.toml`, and writes the remaining files to a tar archive.

Directories excluded by default include `.git`, `__pycache__`, `.venv`, `venv`,
`node_modules`, `build`, `.mypy_cache`, `.pytest_cache`, and hidden paths that
start with `.`.

Files excluded by default include `.DS_Store`, `.pyc`, `.pyo`, and
`rayport.toml`.

A game can add glob rules in `rayport.toml`:

```toml
[package]
exclude = ["tests/**", "debug/**", "screenshots/**"]
include = ["tests/runtime_data/**"]
```

`include` takes precedence over default and custom exclusion rules, allowing a
file to be explicitly restored. The CLI exposes each packaging decision:

```bash
rayport inspect ./game --excluded
rayport inspect ./game --explain tests/test_game.py
rayport inspect ./game --sizes
```

`--sizes` lists files by uncompressed size and flags assets larger than 5 MiB
for review. Rayport does not silently compress, convert, or modify game assets.
Image and audio optimization belongs in the game's own asset pipeline.

The game project directory must contain `main.py` as its entry point.

## Output Safety

Before cleaning an output directory, Rayport checks its canonical path. The
output cannot be the game directory or one of its parents. A non-empty output
must contain the `.rayport-output` marker created by Rayport or deletion is
refused. Only an explicit `--force-output` option allows another directory to
be replaced.

The output may be inside the game directory, such as `dist/`. Rayport excludes
the complete output subtree by its actual relative path, without relying on
the directory name, so generated files cannot re-enter `game.tar.gz`.

## Browser Extraction

The JavaScript in `index.html` processes `game.tar.gz`. After downloading it,
the browser uses `DecompressionStream("gzip")`, parses the tar archive, and
writes each file to `/usr/local/game/` in the WebAssembly virtual filesystem.

The parser supports POSIX PAX extended headers and ustar prefixes, so UTF-8
paths longer than the traditional 100-byte field can be restored. Before
extraction, it rejects absolute paths, backslashes, `..` path segments, and
unsupported tar entry types.

## Related Files

- `src/rayport/packager.py`: packaging logic.
- `src/rayport/cli.py`: CLI entry point for `rayport build`.
