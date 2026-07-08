# 模組 1：wasm 基礎建設

## 目的

把 Python 直譯器和 raylib 遊戲引擎編譯成瀏覽器能執行的格式。這是整個工具的地基，沒有這個，後面什麼都做不了。

## 要做什麼

產出三個檔案：

- `main.wasm` — 編譯好的 Python 直譯器 + raylib 引擎，瀏覽器的 WebAssembly 虛擬機可以執行它
- `main.js` — 一段 JS 程式碼，負責載入 wasm、初始化記憶體、設定 canvas、連接鍵盤滑鼠事件
- `main.data` — Python 的標準函式庫（.py 檔案），打包成一個二進位檔，啟動時會被載入到記憶體內的虛擬檔案系統，讓 Python 直譯器能 `import os` 之類的

## 怎麼做

用 Emscripten 這個工具鏈。Emscripten 是一個把 C/C++ 程式碼編譯成 WebAssembly 的編譯器。

1. 把 raylib 的 C 原始碼用 Emscripten 編譯成靜態函式庫（`libraylib.a`）。raylib 官方的 Makefile 已經支援，用 `make TARGET_PLATFORM=PLATFORM_WEB` 就能編譯。圖形 API 用 OpenGL ES 2.0（對應 WebGL 1.0）。
2. 把 CPython 的 C 原始碼也用 Emscripten 編譯成靜態函式庫（`libpython3.a`）。已有現成專案 python-wasm-sdk 在做這件事。需要裁剪不必要的 stdlib 模組（tkinter、test、idlelib 等）減小體積。
3. 把 raylib-python-cffi 的 C 綁定碼（CFFI 產出的 `_raylib_cffi.c`）也用 Emscripten 編譯。
4. 把以上三個靜態庫連結在一起，產出最終的 wasm。

## 這是一次性的工作

這三個檔案跟使用者的遊戲程式碼無關。只要 Python 版本和 raylib 版本不變，可以一直重複使用。使用者每次改遊戲程式碼，不需要重新編譯 wasm。
