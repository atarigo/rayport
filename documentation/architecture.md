# 技術架構

## 整體結構

rayport 由兩個部分組成：

- wasm runtime：預編譯的 WebAssembly binary，包含 CPython 直譯器、raylib 引擎、CFFI 綁定。這是一次性建置的產物，跟使用者的遊戲碼無關。
- Python CLI 工具：負責收集使用者的遊戲檔案、產生 HTML 頁面、啟動開發伺服器。

使用者執行 `rayport build ./my-game/` 後，產出一個 `build/` 目錄，包含：

- `index.html`：承載遊戲的 HTML 頁面
- `main.wasm`（8.8 MB）：CPython + raylib wasm binary
- `main.js`（269 KB）：Emscripten 膠水碼，負責載入 wasm、初始化記憶體、設定 canvas
- `main.data`（3 MB）：Python 標準函式庫（.pyc），啟動時載入虛擬檔案系統
- `game.tar.gz`：使用者的遊戲碼和資源檔

把 `build/` 上傳到任何靜態網頁伺服器就能玩。

## 執行流程

瀏覽器載入 `index.html` 後的執行順序：

1. 瀏覽器下載 `main.js`、`main.wasm`、`main.data`
2. Emscripten 初始化 wasm，把 `main.data`（Python 標準函式庫）載入虛擬檔案系統
3. `index.html` 的 JS 邏輯下載 `game.tar.gz`，解壓後寫入虛擬檔案系統的 `/usr/local/game/`
4. wasm 內的 CPython 直譯器啟動，執行 `/usr/local/lib/python3.12/launcher.py`
5. `launcher.py` 把 `/usr/local/game/` 加入 `sys.path`，然後執行 `main.py`
6. 遊戲碼呼叫 `from raylib import *` 載入 raylib 綁定（內建模組，不需檔案系統）
7. 遊戲迴圈開始，每次 `WindowShouldClose()` 呼叫時，ASYNCIFY 暫停 wasm 讓瀏覽器更新畫面

## 靜態連結架構

所有 C 程式碼靜態連結成一個 wasm binary，沒有動態載入：

- CPython 3.12.11（`libpython3.12.a`）
- raylib 5.5（`libraylib.a`）
- CFFI 綁定（`_raylib_cffi.o`，由 `gen_cffi.py` 產生 C 原始碼後用 Emscripten 編譯）
- CFFI backend（`_cffi_backend.o`，從 cffi 套件的 C 原始碼編譯）
- libffi type stubs（`ffi_type_stubs.o`，提供 libffi 的型別描述符和 stub 函數）
- web stubs（`web_stubs.o`，提供 Web 平台未實作的 raylib 函數）

`_raylib_cffi` 和 `_cffi_backend` 透過修改 CPython 的 `Modules/config.c`，在 `_PyImport_Inittab` 陣列中註冊為內建模組。Python 碼 `import _raylib_cffi` 時直接取得內建模組，不經過檔案系統。

不使用 Emscripten 的 `-sMAIN_MODULE` 動態連結模式。這個決策解決了 raylib RLGL 全域變數的 PIC relocation 問題，同時把 wasm 體積從 18 MB 降到 8.8 MB。代價是 Python 無法在 runtime 載入 `.so` 擴充模組，但所有需要的模組都已經靜態編譯進去了。

## ASYNCIFY 遊戲迴圈

瀏覽器的 JS 是單執行緒的。如果 Python 的 `while not WindowShouldClose()` 迴圈持續執行，瀏覽器會凍結。

raylib 的 C 碼在 `WindowShouldClose()` 內呼叫 `emscripten_sleep(12)`，暫停 12 毫秒把控制權交回瀏覽器。Emscripten 的 ASYNCIFY 功能在暫停時保存整個 C 呼叫堆疊（包括 CPython 的 ceval.c 主迴圈），12 毫秒後恢復。

連結時加上 `-sASYNCIFY -sASYNCIFY_STACK_SIZE=65536` 啟用此功能。使用者的 Python 遊戲碼不需要任何修改。

## 虛擬檔案系統

wasm 內的 CPython 使用 Emscripten 的 MEMFS（記憶體內檔案系統）。檔案來自兩個來源：

- `main.data`（preload）：Python 標準函式庫和 raylib Python package（`__init__.py`、`colors.py`、`defines.py`、`enums.py`、`version.py`），在 wasm 初始化時自動載入到 `/usr/local/lib/python3.12/`
- `game.tar.gz`（runtime fetch）：使用者的遊戲碼和資源檔，由 `index.html` 的 JS 下載並解壓到 `/usr/local/game/`

## raylib Python package 的 import 機制

原版 raylib-python-cffi 的 `__init__.py` 使用相對 import `from ._raylib_cffi import ffi, lib`，期望 `_raylib_cffi` 是 `raylib` package 的子模組。但在 wasm 中，`_raylib_cffi` 是頂層內建模組。

wasm 用的 `__init__.py` 改為：

1. `import _raylib_cffi`（頂層內建模組）
2. `sys.modules['raylib._raylib_cffi'] = _raylib_cffi`（讓 Python 的 import 系統認為它是 raylib 的子模組）
3. 遍歷 `_raylib_cffi.lib` 的所有符號，注入 `globals()`（讓 `from raylib import *` 能取得所有 C 函數名稱）

## 建置環境

- macOS Darwin（ARM64）
- Emscripten 3.1.61（6.0.2 的 resizable ArrayBuffer 與瀏覽器 Crypto API 不相容）
- CPython 3.12.11
- raylib 5.5
- Python 3.13+（host，執行建置腳本和 CLI 工具）

建置流程由 `Makefile` 自動化，設定項放在 `build.conf`（gitignored），範本見 `build.conf.example`。

## 目錄結構

- `src/rayport/`：Python CLI 工具原始碼
- `rayport.toml`：每個遊戲可選用的 Web presentation 與 package 規則設定檔
- `src/rayport/runtime/`：預編譯的 wasm 檔案（`main.wasm`、`main.js`、`main.data`），作為 Python package data 隨工具發佈
- `stubs/`：建置用的 C stub 和輔助腳本（`gen_cffi.py`、`web_stubs.c`、`ffi_type_stubs.c`、`launcher.py`）
- `.cache/`：建置中間產物（gitignored）

source checkout 與 wheel 安裝都透過 `importlib.resources` 尋找 `rayport` package 內的三個 runtime artifacts；也可用 `RAYPORT_RUNTIME` environment variable 指向自訂 runtime。

## 已知限制

wasm 內的 Python 直譯器不支援：

- 網路連線（socket、urllib、requests）
- 子行程（fork、exec、subprocess）
- 實體執行緒（SharedArrayBuffer 限制）
- 實體檔案系統存取（只有記憶體內 MEMFS）
- ctypes、ssl、動態載入 .so 模組

這些限制不影響 raylib 遊戲，因為 raylib 的圖形、輸入、音訊都透過已編譯進 wasm 的 C 引擎運作。

遊戲碼只能使用 C 風格的函數名稱（`InitWindow`、`BeginDrawing`），Python 風格名稱（`init_window`、`begin_drawing`）來自 `pyray` 模組，目前未包含在 wasm 中。
