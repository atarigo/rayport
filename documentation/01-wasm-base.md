# 模組 01：wasm 基礎建設

## 功能

把 CPython 直譯器、raylib 引擎、CFFI 綁定編譯成一個瀏覽器可執行的 WebAssembly binary。

產出三個檔案：

- `main.wasm`（14.1 MiB）：CPython 3.12.11 + raylib 5.5 + CFFI 綁定，靜態連結成單一 wasm
- `main.js`（286.4 KiB）：Emscripten 膠水碼，負責載入 wasm、初始化記憶體、設定 canvas、連接瀏覽器事件
- `main.data`（3.0 MiB）：Python 標準函式庫（.pyc）和 raylib Python package（.py），打包成 preload 資料

這三個檔案跟使用者的遊戲碼無關。只要 CPython 和 raylib 版本不變，不需要重新建置。

## 建置流程

`Makefile` 自動化整個流程，使用者只需要執行 `make runtime`。

建置步驟：

1. Clone CPython、raylib、raylib-python-cffi、cffi 原始碼到 `.cache/`
2. 建置 native Python（交叉編譯的前置步驟）
3. 交叉編譯 CPython 為 wasm
4. 用 Emscripten 編譯 raylib（`make PLATFORM=PLATFORM_WEB`，加上 `-fPIC`）
5. 執行 `gen_cffi.py` 產生 CFFI C 綁定碼（`_raylib_cffi.c`，約 44,000 行）
6. 用 Emscripten 編譯 `_raylib_cffi.c` 和 `_cffi_backend.c`
7. 修補 CPython 的 `config.c`，把 `_raylib_cffi` 和 `_cffi_backend` 註冊為內建模組
8. 安裝 raylib Python package 到 preload 目錄
9. 靜態連結所有目標檔和函式庫，產出最終的 `main.wasm`、`main.js`、`main.data`
10. 複製產物到 `src/rayport/runtime/`

## 關鍵技術決策

**全部靜態連結**：不使用 Emscripten 的 `-sMAIN_MODULE` 動態連結模式。raylib 的 RLGL 全域結構體會產生與 PIC 模式不相容的 relocations，也不需要瀏覽器端動態載入原生模組。

**Emscripten 3.1.61**：emsdk 6.0.2 預設啟用 resizable ArrayBuffer，Chrome 的 `Crypto.getRandomValues()` 和 `TextDecoder.decode()` 不接受 resizable ArrayBuffer 上的 view。

**CFFI 內建模組**：`_raylib_cffi` 和 `_cffi_backend` 透過 `_PyImport_Inittab` 註冊為 CPython 內建模組，而非透過 `Setup.local`（CPython 的 configure 不會從 source tree 複製 `Setup.local`）。

**libffi stubs**：`_cffi_backend.c` 依賴 libffi 的型別描述符和函數呼叫 API。wasm 不支援 libffi 的動態呼叫機制，但 CFFI 的 compiled mode 不經過 `ffi_call`，所以只需提供型別描述符的正確值和 stub 函數。見 `stubs/ffi_type_stubs.c`。

**web stubs**：raylib 5.5 的 `GetClipboardImage()` 在 Web 平台未實作但有宣告，CFFI 綁定會參照它。`stubs/web_stubs.c` 提供空實作。

## 相關檔案

- `Makefile`：建置流程
- `build.conf.example`：建置組態範本（EMSDK 路徑、版本號碼、Git repo）
- `stubs/gen_cffi.py`：CFFI C 綁定碼產生器
- `stubs/ffi_type_stubs.c`：libffi 型別描述符和 stub 函數
- `stubs/web_stubs.c`：Web 平台未實作的 raylib 函數 stub
- `src/rayport/runtime/`：建置產物存放目錄，也是發布套件的 package data
