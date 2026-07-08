# rayport

Package raylib Python games to run in the browser.

## How it works

The tool bundles a CPython interpreter and raylib engine compiled to WebAssembly. User game code (.py files and assets) is loaded into a virtual filesystem at runtime and executed by the wasm Python interpreter.

## Prerequisites

- [Emscripten SDK](https://emscripten.org/) (3.1.61 recommended)
- Python 3.13+

## Building the runtime

The runtime contains the CPython wasm interpreter. Build it once; rebuild only when upgrading CPython or raylib.

```bash
cp build.conf.example build.conf
# Edit build.conf to set your EMSDK_PATH
make runtime
```

## Development

```bash
python3 dev_server.py
# Open http://localhost:8080/runtime/python.html
```

## Project status

Early development. Validating technical feasibility of the CPython + raylib wasm pipeline.
