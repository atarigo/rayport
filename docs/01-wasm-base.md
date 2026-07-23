# Module 01: WebAssembly Runtime

## Purpose

Compile the CPython interpreter, raylib engine, and CFFI bindings into a
WebAssembly binary that runs in a browser.

The build produces three files:

- `main.wasm` (14.1 MiB): CPython 3.12.11, raylib 5.5, and the CFFI bindings,
  statically linked into one WebAssembly module.
- `main.js` (286.4 KiB): Emscripten glue code that loads the module, initializes
  memory, configures the canvas, and connects browser events.
- `main.data` (3.0 MiB): the Python standard library (`.pyc`) and raylib Python
  package (`.py`) packed as preload data.

These files do not depend on a user's game code. They only need to be rebuilt
when the CPython or raylib version changes.

## Build Process

The `Makefile` automates the complete process. Run `make runtime` to start it.

Build steps:

1. Clone the CPython, raylib, raylib-python-cffi, and cffi sources into
   `.cache/`.
2. Build native Python as a prerequisite for cross-compilation.
3. Cross-compile CPython to WebAssembly.
4. Compile raylib with Emscripten using
   `make PLATFORM=PLATFORM_WEB` and `-fPIC`.
5. Run `gen_cffi.py` to generate the CFFI C bindings
   (`_raylib_cffi.c`, approximately 44,000 lines).
6. Compile `_raylib_cffi.c` and `_cffi_backend.c` with Emscripten.
7. Patch CPython's `config.c` to register `_raylib_cffi` and `_cffi_backend`
   as built-in modules.
8. Install the raylib Python package into the preload directory.
9. Statically link all object files and libraries into `main.wasm`, `main.js`,
   and `main.data`.
10. Copy the artifacts to `src/rayport/runtime/`.

## Key Technical Decisions

**Fully static linking:** The build does not use Emscripten's dynamic
`-sMAIN_MODULE` mode. raylib's global RLGL state creates relocations that are
incompatible with the PIC mode, and the browser does not need to load native
modules dynamically.

**Emscripten 3.1.61:** emsdk 6.0.2 enables resizable `ArrayBuffer` objects by
default. Chrome's `Crypto.getRandomValues()` and `TextDecoder.decode()` do not
accept views over resizable `ArrayBuffer` objects.

**Built-in CFFI modules:** `_raylib_cffi` and `_cffi_backend` are registered as
CPython built-in modules through `_PyImport_Inittab`, rather than through
`Setup.local`. CPython's configure process does not copy `Setup.local` from the
source tree.

**libffi stubs:** `_cffi_backend.c` depends on libffi type descriptors and call
APIs. WebAssembly does not support libffi's dynamic call mechanism, but CFFI's
compiled mode does not call `ffi_call`. Rayport therefore only provides the
correct type descriptors and stub functions. See `stubs/ffi_type_stubs.c`.

**Web stubs:** raylib 5.5 declares `GetClipboardImage()` but does not implement
it for the Web platform. The CFFI bindings reference it, so
`stubs/web_stubs.c` provides an empty implementation.

## Related Files

- `Makefile`: build process.
- `build.conf.example`: build configuration template for EMSDK paths,
  versions, and Git repositories.
- `stubs/gen_cffi.py`: CFFI C binding generator.
- `stubs/ffi_type_stubs.c`: libffi type descriptors and stub functions.
- `stubs/web_stubs.c`: stubs for raylib functions unavailable on the Web.
- `src/rayport/runtime/`: build output and published package data.
