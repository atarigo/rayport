# Runtime

CPython interpreter compiled to WebAssembly via Emscripten. User's Python game code runs on this interpreter inside the browser.

## Files

| File | Description |
|------|-------------|
| main.wasm | CPython interpreter + raylib engine as a WebAssembly binary |
| main.js | Emscripten glue code that loads the wasm, initializes memory, and sets up the virtual filesystem |
| main.data | CPython standard library and raylib Python package packed into a binary blob, loaded into the in-memory virtual filesystem at startup |

## How to build

Run this command from the project root:

```bash
make runtime
```

The Emscripten SDK and all source dependencies are downloaded automatically.
By default, emsdk is stored in `/tmp/rayport-emsdk`, while CPython, raylib, and
other sources are stored in `.cache/`. To customize paths or versions, create
`build.conf` using `build.conf.example` as a template.
