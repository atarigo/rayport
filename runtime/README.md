# Runtime

CPython interpreter compiled to WebAssembly via Emscripten. User's Python game code runs on this interpreter inside the browser.

## Files

| File | Description |
|------|-------------|
| python.wasm | CPython interpreter as a WebAssembly binary (9 MB) |
| python.js | Emscripten glue code that loads the wasm, initializes memory, and sets up the virtual filesystem (545 KB) |
| python.data | CPython standard library (.pyc files) packed into a binary blob, loaded into the in-memory virtual filesystem at startup (3 MB) |
| python.html | Emscripten default test page with a Python REPL terminal |
| python.worker.js | Web Worker script for background thread support |

## How to build

Requires Emscripten SDK and a system Python 3. CPython source code is only needed during compilation and can be deleted afterward.

```bash
git clone --depth 1 --branch v3.12.11 https://github.com/python/cpython.git cpython-src
cd cpython-src

# Build native Python (needed as a build tool for cross-compilation)
python3 Tools/wasm/wasm_build.py build

# Cross-compile to wasm (EM_CONFIG must point to emsdk's .emscripten file)
export EM_CONFIG="$EMSDK/.emscripten"
python3 Tools/wasm/wasm_build.py emscripten-browser
```

Output files are in `cpython-src/builddir/emscripten-browser/`.

## Current status

This runtime only contains the CPython interpreter. The final version needs raylib and raylib-python-cffi bindings statically linked into python.wasm so that Python code can call raylib's graphics, input, and audio functions.
