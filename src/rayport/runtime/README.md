# Runtime

CPython interpreter compiled to WebAssembly via Emscripten. User's Python game code runs on this interpreter inside the browser.

## Files

| File | Description |
|------|-------------|
| main.wasm | CPython interpreter + raylib engine as a WebAssembly binary |
| main.js | Emscripten glue code that loads the wasm, initializes memory, and sets up the virtual filesystem |
| main.data | CPython standard library and raylib Python package packed into a binary blob, loaded into the in-memory virtual filesystem at startup |

## How to build

在專案根目錄執行：

```bash
make runtime
```

Emscripten SDK 和所有原始碼依賴會自動下載。預設下載到 `/tmp/rayport-emsdk`（emsdk）和 `.cache/`（CPython、raylib 等原始碼）。如需自訂路徑或版本，建立 `build.conf`（參考 `build.conf.example`）。
