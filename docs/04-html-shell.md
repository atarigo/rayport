# Module 04: HTML Shell Generator

## Purpose

Generate the `index.html` page that users open in a browser. It loads the
WebAssembly runtime, displays progress, downloads and extracts game files, and
starts the game.

## How It Works

`generate_html()` reads the `src/rayport/templates/index.html` template and
uses Python's `string.Template` to fill in parameters.

Parameters configurable through `rayport.toml`:

- `title`: page title, defaulting to `rayport game`.
- `presentation`: CSS canvas presentation mode, defaulting to `stretch`.
- `background`: background color where the canvas does not cover the viewport.

The game's render resolution is controlled only by
`InitWindow(width, height, ...)` in the Python game code. The HTML does not
rewrite `canvas.width` or `canvas.height`; it changes only the CSS presentation
size. This prevents raylib, the WebGL render target, and the page from
competing over the resolution.

Emscripten GLFW returns CSS-pixel coordinates by default. Rayport maps mouse
coordinates back to the raylib resolution using the ratio between the GLFW
logical window and the canvas display rectangle. `GetMouseX()` and
`GetMouseY()` therefore stay within the correct range when the viewport is
stretched, scaled proportionally, or letterboxed.

Presentation modes:

- `stretch`: sets the CSS size to `100vw × 100dvh`, filling the browser
  viewport and stretching when aspect ratios differ.
- `fit`: preserves the game's aspect ratio and fills as much of the viewport
  as possible, using the background color for remaining space.
- `pixel-perfect`: uses integer scaling when space permits and scales down when
  necessary to keep the complete canvas visible.
- `native`: does not scale the canvas.

The legacy `--width` and `--height` options may still be used together for
compatibility, but new projects should declare their render resolution through
`InitWindow()`.

## HTML Template Contents

The template contains:

- A loading screen with a progress bar and status text on a black background,
  hidden after WebAssembly initialization.
- A canvas where raylib renders the game.
- Game-loading logic that uses Emscripten's `addRunDependency` and
  `removeRunDependency` mechanisms to download and extract `game.tar.gz`
  before the runtime starts.
- A pure JavaScript tar.gz extractor that uses
  `DecompressionStream("gzip")`, parses the tar archive, and writes files to
  `/usr/local/game/` in the virtual filesystem.
- Emscripten `Module` configuration for the canvas, startup arguments
  (`launcher.py`), and the `preRun` hook.

The WebAssembly startup argument is
`/usr/local/lib/python3.12/launcher.py`, so CPython runs the launcher directly
instead of entering the REPL.

## Related Files

- `src/rayport/html_generator.py`: template rendering logic.
- `src/rayport/templates/index.html`: full-screen HTML template.
