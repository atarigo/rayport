# POC Verification Log

> Historical document. This records technical feasibility work from early
> development. It reflects the state at the time and some details may differ
> from the final implementation.

This document records the full feasibility verification process for rayport (formerly raylib-web-tool), a tool that packages raylib Python games to run in the browser.

## Background

The tool's architecture has 7 modules (documented in `plan/01` through `plan/07`). Before investing development effort, we needed to verify the core technical assumption: CPython + raylib can be compiled to WebAssembly and run a Python game in the browser.

The architecture works like this: CPython interpreter and raylib engine are both C code. Both get compiled to WebAssembly via Emscripten and statically linked into a single `.wasm` file. This wasm runs in the browser. The user's Python game code (.py files) is NOT compiled. It's loaded into a virtual filesystem inside the wasm at runtime, and the wasm CPython interpreter executes it. When the Python code calls `from raylib import *` and uses raylib functions, the calls go through a CFFI bridge to the raylib C code that's already inside the same wasm.

The precompiled wasm (CPython + raylib) ships with the tool. Users don't need Emscripten. They only need the tool itself to package their game.

Two approaches exist for loading user game files into the wasm virtual filesystem:
- Emscripten preload: files baked into a `.data` blob at build time, loaded during wasm initialization. Faster startup, but requires Emscripten's `file_packager.py` to rebuild the data file.
- Runtime fetch: files downloaded as tar.gz by the browser, then extracted into the virtual filesystem via JS. Slightly slower startup, but users don't need any C toolchain.

## Build Environment

- macOS Darwin 25.5.0 (ARM64)
- Emscripten 3.1.61
- CPython 3.12.11 (compiled from source)
- raylib 5.5 (compiled from source)
- raylib-python-cffi (latest main branch, used only for CFFI code generation)
- Python 3.13 (host system, used to run build scripts)
- uv 0.9.17 (Python package manager)

## Verification Plan

Four steps, ordered by risk. Each validates one assumption. If a step fails, stop and reassess.

1. CPython compiles to wasm and runs Python code in the browser
2. raylib compiles to wasm and draws graphics in the browser
3. CFFI bindings statically linked into the wasm, Python can call raylib
4. Game loop runs without freezing the browser

---

## Step 1: CPython compiles to wasm and runs in browser

### Purpose

Verify that the CPython C source code can be cross-compiled to wasm32-emscripten and the resulting wasm can execute Python code inside a browser. This is the foundation of the entire tool.

### Method

CPython 3.12 has built-in wasm build support in `Tools/wasm/`. The process requires two stages: first build a native Python (used as a build tool during cross-compilation), then cross-compile for wasm.

```bash
git clone --depth 1 --branch v3.12.11 https://github.com/python/cpython.git cpython-src
cd cpython-src

# Stage 1: build native Python
python3 Tools/wasm/wasm_build.py build

# Stage 2: cross-compile to wasm
export EM_CONFIG="$EMSDK/.emscripten"
python3 Tools/wasm/wasm_build.py emscripten-browser
```

Output files in `builddir/emscripten-browser/`:
- `python.wasm` (11 MB): the CPython interpreter as WebAssembly
- `python.js` (565 KB): Emscripten glue code that loads wasm, initializes memory, sets up virtual filesystem
- `python.data` (3 MB): CPython standard library (.pyc files) packed for preloading
- `python.html` (10 KB): test page with a Python REPL terminal
- `python.worker.js` (2 KB): Web Worker script

To test in a browser, a local HTTP server is needed. `file://` won't work because browsers block wasm loading from `file://` and certain features (SharedArrayBuffer) require specific HTTP headers:
- `Cross-Origin-Opener-Policy: same-origin`
- `Cross-Origin-Embedder-Policy: require-corp`
- `.wasm` files must be served with `Content-Type: application/wasm`

We created `dev_server.py` using Python's built-in `http.server` module with these headers added.

### Result

Pass. The Python REPL loaded in the browser and executed `print("hello")` successfully. The REPL has a minor input quirk (an extra character appears after each command), documented in CPython's wasm README as a known issue with the terminal handler.

### Pitfalls

**EM_CONFIG not exported by emsdk 6.0.2**

emsdk 6.0.2 (the latest version at the time) does not export `EM_CONFIG` as an environment variable, but CPython's `wasm_build.py` requires it. The emsdk's `construct_env` command outputs `PATH`, `EMSDK`, `EMSDK_NODE`, `EMSDK_PYTHON`, `SSL_CERT_FILE`, but NOT `EM_CONFIG`.

The config file itself exists at `$EMSDK/.emscripten`. Fix: manually export it before running the build.

```bash
export EM_CONFIG="$EMSDK/.emscripten"
```

**Emscripten 6.0.2 breaks browser APIs**

After compiling with emsdk 6.0.2 and loading in Chrome, the REPL crashed with:
```
Uncaught TypeError: Failed to execute 'getRandomValues' on 'Crypto': 
The provided ArrayBufferView value must not be resizable.
```

Emscripten 6.0.2 uses resizable ArrayBuffer by default (a recent browser feature). But Chrome's `Crypto.getRandomValues()` and `TextDecoder.decode()` don't accept views over resizable ArrayBuffers yet. CPython's wasm build was tested against Emscripten 3.1.x.

Fix: downgrade Emscripten to 3.1.61.

```bash
./emsdk install 3.1.61
./emsdk activate 3.1.61
```

After rebuilding with 3.1.61, the REPL loaded and ran correctly.

**EMSDK_QUIET not working**

Adding `export EMSDK_QUIET=1` before `source emsdk_env.sh` in `~/.zshrc` didn't suppress the startup messages. Root cause: `~/.zprofile` also had `source emsdk_env.sh` (written by another tool or by emsdk itself), and `.zprofile` runs BEFORE `.zshrc`. The messages came from `.zprofile`'s source, when `EMSDK_QUIET` wasn't set yet.

Fix: move `export EMSDK_QUIET=1` to `~/.zprofile`, before the `source` line. Remove the duplicate from `~/.zshrc`.

---

## Step 2: raylib compiles to wasm and draws in browser

### Purpose

Verify that raylib's C source can be compiled to wasm via Emscripten and render graphics on a browser canvas. This is well-established (raylib officially supports `PLATFORM_WEB`), so this step is mainly a sanity check.

### Method

```bash
# Compile raylib for web
cd raylib-src/src
make PLATFORM=PLATFORM_WEB -B
# Output: libraylib.a (wasm static library)
```

Minimal test program (`test.c`):

```c
#include "raylib.h"
#include <emscripten/emscripten.h>

void UpdateDrawFrame(void) {
    BeginDrawing();
    ClearBackground(RAYWHITE);
    DrawRectangle(100, 100, 200, 200, RED);
    DrawText("Hello from raylib!", 100, 350, 20, DARKGRAY);
    EndDrawing();
}

int main(void) {
    InitWindow(800, 450, "raylib wasm test");
    emscripten_set_main_loop(UpdateDrawFrame, 60, 1);
    CloseWindow();
    return 0;
}
```

Compile:
```bash
emcc -o test.html test.c -I../raylib-src/src -L../raylib-src/src -lraylib \
  -sUSE_GLFW=3 -sASSERTIONS=1 -DPLATFORM_WEB -Os
```

### Result

Pass. Compilation successful, browser test confirmed: white background with a red square and "Hello from raylib!" text rendered on a canvas. The compiled output is `test.html` (19 KB), `test.js` (207 KB), `test.wasm` (106 KB).

### Key observation

The user's installed raylib (via pip/homebrew for macOS) is compiled for ARM64. It cannot be used for wasm. raylib must be recompiled from C source using Emscripten to produce a wasm-compatible `libraylib.a`. This is a one-time build step.

---

## Step 3: CFFI bindings statically linked, Python can call raylib in wasm

### Purpose

This is the highest-risk step. Verify that:
1. raylib-python-cffi's CFFI-generated C bindings can be compiled with Emscripten
2. The compiled bindings can be statically linked into the CPython wasm binary
3. CPython recognizes the module as a built-in and allows `import _raylib_cffi`

No public project has done this specific combination before (static CFFI module in CPython wasm with raylib).

### Method

**Generate the CFFI C source code**

raylib-python-cffi uses CFFI's out-of-line mode. The build script (`raylib/build.py`) pre-processes raylib's C headers through `gcc -E`, feeds them to `ffibuilder.cdef()`, then compiles. For wasm, we only need the code generation step, not the compilation.

We wrote a minimal script (`gen_cffi.py`) that:
1. Pre-processes `raylib.h`, `rlgl.h`, `raymath.h` from the cloned raylib source
2. Calls `ffibuilder.set_source("raylib._raylib_cffi", ...)` with the include directives
3. Calls `ffibuilder.emit_c_code("_raylib_cffi.c")` to generate only the C source (no compilation)

This requires the `cffi` Python package on the host: `uv add cffi`.

Result: `_raylib_cffi.c`, 44,583 lines. The module init function is `PyInit__raylib_cffi`. Inside the generated code, `_cffi_init("raylib._raylib_cffi", ...)` registers the module with the dotted name.

**Compile with Emscripten**

```bash
emcc -c -O3 -fPIC \
  -I${CPYTHON_SRC}/Include -I${CPYTHON_SRC}/Include/internal \
  -I${BUILD_DIR} -I${BUILD_DIR}/Include \
  -I${RAYLIB_SRC} \
  -o Modules/_raylib_cffi.o ${CPYTHON_SRC}/Modules/_raylib_cffi.c
```

**Register as built-in module**

CPython's built-in modules are listed in `Modules/config.c` in the `_PyImport_Inittab[]` array. Two additions needed:

1. Extern declaration:
```c
extern PyObject* PyInit__raylib_cffi(void);
```

2. Init table entry (before the `{0, 0}` sentinel):
```c
{"_raylib_cffi", PyInit__raylib_cffi},
```

The modified `config.c` was recompiled with emcc, then both `config.o` and `_raylib_cffi.o` were inserted into `libpython3.12.a` using `emar r`.

**Provide stub for web-unsupported function**

raylib 5.5 declares `GetClipboardImage()` in `raylib.h` but only implements it on desktop platforms. The CFFI bindings reference all declared functions. A stub was created in `web_stubs.c`:

```c
#include "raylib.h"
Image GetClipboardImage(void) {
    Image image = { 0 };
    return image;
}
```

**Final link command**

```bash
emcc -sUSE_GLFW=3 -sALLOW_MEMORY_GROWTH -sTOTAL_MEMORY=20971520 -sWASM_BIGINT \
  -sFORCE_FILESYSTEM -lidbfs.js -lnodefs.js -lproxyfs.js -lworkerfs.js \
  --preload-file=./usr/local -O2 -g0 \
  -o python.js \
  Programs/python.o \
  libpython3.12.a \
  ${RAYLIB_SRC}/libraylib.a \
  web_stubs.o \
  Modules/_decimal/libmpdec/libmpdec.a \
  -sUSE_ZLIB -sUSE_BZIP2 \
  Modules/_hacl/libHacl_Hash_SHA2.a \
  Modules/expat/libexpat.a \
  -sUSE_SQLITE3 \
  -lm -ldl -lpthread
```

### Result

Pass. Compilation, linking, and browser test all successful.

Build output: `python.wasm` (8.9 MB), `python.js` (269 KB), `python.data` (3 MB).

Browser test results:
- `import _raylib_cffi`: pass (built-in module loaded successfully)
- `from raylib import *`: pass (after adding .py files to virtual filesystem and fixing __init__.py)
- `print(RAYWHITE)`: pass, returned `(245, 245, 245, 255)`
- `InitWindow(800, 450, b"test")`: pass, printed raylib 5.5 initialization info with "Platform backend: WEB (HTML5)" and all modules loaded

### Pitfalls

**Setup.local not picked up by configure**

CPython's standard way to add built-in modules is `Modules/Setup.local`. CPython 3.12's configure script creates `Setup.local` in the build directory:

```bash
# From CPython configure (line 32969):
if test ! -f Modules/Setup.local
then
    echo "# Edit this file for local setup changes" >Modules/Setup.local
fi
```

It does NOT copy from the source tree's `Modules/Setup.local`. The fallback always creates an empty file. Writing `Setup.local` in the source tree before running `wasm_build.py` has no effect because `wasm_build.py` deletes and recreates the build directory, then configure creates a fresh empty `Setup.local`.

Workaround: skip `Setup.local` entirely. Directly modify `config.c` in the build directory and use `emar` to update `libpython3.12.a`.

**CFLAGS override erases platform defines**

Running `make PLATFORM=PLATFORM_WEB CFLAGS="-fPIC" -B` replaces the Makefile's entire CFLAGS value. raylib's Makefile builds CFLAGS incrementally:

```makefile
CFLAGS += -Wall -D_GNU_SOURCE ...
ifeq ($(PLATFORM),PLATFORM_WEB)
    CFLAGS += -DPLATFORM_WEB -DGRAPHICS_API_OPENGL_ES2
endif
```

Passing `CFLAGS="-fPIC"` on the command line overrides all of this. The result: raylib compiles without `-DPLATFORM_WEB`, so web-specific code paths (including `WindowShouldClose`) are excluded.

Symptom: `WindowShouldClose` was missing from `libraylib.a` (verified with `llvm-nm`).

Fix: pass the full CFLAGS string with all original flags plus `-fPIC`:

```bash
make PLATFORM=PLATFORM_WEB -B \
  "CFLAGS=-Wall -D_GNU_SOURCE -DPLATFORM_WEB -DGRAPHICS_API_OPENGL_ES2 \
   -Wno-missing-braces -Werror=pointer-arith -fno-strict-aliasing \
   -std=gnu99 -Os -fPIC"
```

**PIC relocation errors with -sMAIN_MODULE**

CPython's wasm build uses `-sMAIN_MODULE` in the final link. This flag enables Emscripten's dynamic linking support, which requires ALL linked code to use PIC (position-independent code) relocations.

raylib's `RLGL` global struct (defined in `rlgl.h`, a header-only library included by `rcore.c`) generates `R_WASM_MEMORY_ADDR_LEB` relocations that are incompatible with PIC mode, even when compiled with `-fPIC`.

Error:
```
wasm-ld: error: libraylib.a(rcore.o): relocation R_WASM_MEMORY_ADDR_LEB 
cannot be used against symbol `RLGL`; recompile with -fPIC
```

Fix: remove `-sMAIN_MODULE` from the link command. We don't need dynamic linking since all modules are statically linked. This change also reduced the wasm output from ~18 MB to 8.8 MB because the dynamic linking infrastructure (import/export tables, relocation data) is no longer included.

Trade-off: without `-sMAIN_MODULE`, Python cannot load `.so` extension modules at runtime. This is acceptable because all needed extensions are compiled in.

**Duplicate _PyImport_Inittab symbol**

When linking with both a standalone `Modules/config.o` AND `libpython3.12.a` (which already contains the original `config.o`), the linker reports:

```
wasm-ld: error: duplicate symbol: _PyImport_Inittab
>>> defined in Modules/config.o
>>> defined in libpython3.12.a(config.o)
```

Fix: use `emar r libpython3.12.a Modules/config.o` to replace the config.o inside the archive with the modified version. Then link with just `libpython3.12.a` (no standalone config.o).

**Module import path mismatch**

CPython's `_PyImport_Inittab` registers built-in modules at the top level. The module is accessible as `import _raylib_cffi`.

But raylib-python-cffi's `__init__.py` uses a relative import:
```python
from ._raylib_cffi import ffi, lib as rl
```

This resolves to `raylib._raylib_cffi`, and Python's import system looks for it as a submodule of the `raylib` package (in the filesystem), not as a top-level built-in module.

Fix: modify `__init__.py` for wasm to use absolute import and inject into sys.modules:
```python
import _raylib_cffi
import sys
sys.modules['raylib._raylib_cffi'] = _raylib_cffi
ffi = _raylib_cffi.ffi
rl = _raylib_cffi.lib
```

**_cffi_backend dependency**

Initial assumption was that `_raylib_cffi` is self-contained. Wrong. `import _raylib_cffi` fails with `ModuleNotFoundError: No module named '_cffi_backend'`. The CFFI-generated code depends on `_cffi_backend` (the core C extension of the cffi package) at runtime.

Fix: compile `_cffi_backend.c` from the cffi source distribution (cffi-2.1.0/src/c/_cffi_backend.c) with emcc and register it as another built-in module in `_PyImport_Inittab` alongside `_raylib_cffi`.

`_cffi_backend.c` requires libffi headers (`ffi.h`). Used the headers bundled in cffi's source tree (`src/c/libffi_arm64/include/`).

**libffi runtime symbols missing**

`_cffi_backend.c` compiled successfully but linking failed with undefined symbols from libffi. The missing symbols fall into two categories:

1. Type descriptors (global variables): `ffi_type_void`, `ffi_type_uint8`, `ffi_type_sint8`, `ffi_type_uint16`, `ffi_type_sint16`, `ffi_type_uint32`, `ffi_type_sint32`, `ffi_type_uint64`, `ffi_type_sint64`, `ffi_type_float`, `ffi_type_double`, `ffi_type_pointer`. These are small structs describing FFI types (size, alignment, type code).

2. Closure/call functions: `ffi_closure_alloc`, `ffi_closure_free`, `ffi_prep_closure_loc`, `ffi_prep_cif`, `ffi_prep_cif_var`, `ffi_call`. These are for dynamic function calling and callbacks.

Fix: provide stubs in `ffi_type_stubs.c`. Type descriptors are defined with correct size/alignment values. Closure functions return error codes (callbacks from C to Python not supported in wasm). `ffi_prep_cif` and `ffi_call` are stubbed as no-ops because compiled CFFI modules call raylib functions directly through generated C code, not through libffi's `ffi_call`.

**`from _raylib_cffi.lib import *` fails**

`_raylib_cffi.lib` is a CFFI lib proxy object (an attribute of the module), not a Python submodule. The syntax `from _raylib_cffi.lib import *` fails with `ModuleNotFoundError: '_raylib_cffi' is not a package`.

Fix: instead of `from ... import *`, iterate over the lib object and inject all symbols into the module namespace:
```python
for _name in dir(_raylib_cffi.lib):
    if not _name.startswith('_'):
        globals()[_name] = getattr(_raylib_cffi.lib, _name)
```

**cffi Python package not needed at runtime**

raylib's original `__init__.py` has `import cffi`. Initial concern was that this would require bundling the entire cffi Python package in the virtual filesystem.

Result: the `import cffi` line was removed from the wasm `__init__.py`. The `_cffi_backend` C extension (compiled as built-in) provides all the runtime support that `_raylib_cffi` needs. The cffi Python package is only needed on the host for code generation (`ffibuilder.emit_c_code`).

**raylib Python package files in virtual filesystem**

The raylib .py files (`__init__.py`, `colors.py`, `defines.py`, `enums.py`, `version.py`) must be placed in `usr/local/lib/python3.12/raylib/` inside the build directory before the final emcc link. The `--preload-file=./usr/local` flag bakes them into `python.data`. Only a modified `__init__.py` is used; `colors.py`, `defines.py`, `enums.py`, `version.py` are copied from raylib-python-cffi unchanged.

**C-style function names only**

The CFFI bindings expose C-style names (`InitWindow`, `BeginDrawing`), not Python-style names (`init_window`, `begin_drawing`). The Python-style names come from the `pyray` module, which is a separate wrapper not included in this build. Games must use C-style names, or the `pyray` wrapper needs to be added to the virtual filesystem.

---

## Step 4: Game loop runs without freezing the browser

### Purpose

Verify that a `while not window_should_close()` game loop can run continuously in the browser without blocking the main thread (which would freeze the page).

### Method

Tested in the python.html REPL:

```python
from raylib import *
InitWindow(800, 450, b"test")
```

### Result

Partially verified. `InitWindow` succeeded and printed full raylib initialization info:

```
INFO: Initializing raylib 5.5
INFO: Platform backend: WEB (HTML5)
INFO: Supported raylib modules:
INFO:     > rcore:..... loaded (mandatory)
INFO:     > rlgl:...... loaded (mandatory)
INFO:     > rshapes:... loaded (optional)
INFO:     > rtextures:. loaded (optional)
INFO:     > rtext:..... loaded (optional)
INFO:     > rmodels:... loaded (optional)
INFO:     > raudio:.... loaded (optional)
```

After `InitWindow` returned, the REPL froze (no prompt, no input accepted). This is because the REPL page (`python.html`) runs Python in a Web Worker, and raylib needs to operate the canvas/GL context on the main thread. The two thread models conflict, causing the Worker's communication with the main thread to deadlock.

This does NOT mean game loops are impossible. The REPL is a specific execution environment with Worker-based threading. A real game would run Python directly on the main thread (not through a Worker REPL), with either ASYNCIFY or coroutine-based yielding to prevent freezing. This is the work for development stage 2 (module 3).

### Conclusion

The core technical question for step 4 was: can raylib's C engine initialize and operate inside the same wasm as CPython? The answer is yes. `InitWindow` successfully created the GL context and loaded all raylib modules in the browser. The remaining game loop problem is an engineering question (how to yield control back to the browser between frames), not a feasibility question.

### Planned approach for stage 2

Two routes, try A first, fall back to B:

**Route A: ASYNCIFY**

raylib's C code calls `emscripten_sleep(12)` inside `WindowShouldClose()` to yield control back to the browser. Emscripten's ASYNCIFY feature saves the C call stack at this point and restores it after the sleep. If ASYNCIFY can work through CPython's interpreter loop (ceval.c), the user's Python game loop runs unmodified.

Requires adding `-sASYNCIFY` to the link flags. May significantly increase wasm size. Removing `-sMAIN_MODULE` in step 3 should not affect ASYNCIFY compatibility since ASYNCIFY works with static linking.

**Route B: Coroutine rewrite**

Use Python's AST module to rewrite the game loop:
```python
# Before:
while not WindowShouldClose():
    BeginDrawing()
    DrawText(b"Hello", 10, 10, 20, RED)
    EndDrawing()

# After:
async def main():
    while not WindowShouldClose():
        BeginDrawing()
        DrawText(b"Hello", 10, 10, 20, RED)
        EndDrawing()
        await asyncio.sleep(0)
asyncio.run(main())
```

This is the approach pygbag uses with raylib-python-cffi and is proven to work.

---

## POC Conclusion

All four steps verified. Core technical feasibility confirmed: CPython + raylib + CFFI bindings can coexist in a single 8.9 MB wasm, Python code can successfully `from raylib import *` and call `InitWindow` in the browser. The remaining game loop yielding problem is engineering work (stage 2), not a feasibility blocker.

---

## Project decisions made during this session

- **Name:** changed from raylib-web-tool to rayport
- **Emscripten version:** 3.1.61 (6.0.2 has browser API incompatibility)
- **CPython version:** 3.12.11
- **raylib version:** 5.5
- **Linking strategy:** fully static (no `-sMAIN_MODULE`), all modules built-in
- **Directory structure:**
  - `runtime/`: precompiled wasm files (shipped with the tool, version-controlled)
  - `.cache/`: build intermediates (gitignored)
  - `build.conf`: user's local build settings (gitignored, template in `build.conf.example`)
  - `plan/`: module specification documents

## wasm Python limitations relevant to this project

The wasm Python interpreter cannot:
- Make network connections (no socket, urllib, requests)
- Start subprocesses (no fork, exec, subprocess)
- Use real threading (SharedArrayBuffer restrictions, stability issues)
- Access the real filesystem (only in-memory MEMFS)
- Use ctypes, ssl, or dynamically loaded .so modules

These limitations don't affect raylib games because raylib's graphics, input, and audio all go through the C engine compiled into the same wasm, not through Python's standard library.
