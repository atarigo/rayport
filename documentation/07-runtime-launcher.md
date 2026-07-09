# 模組 07：Runtime 啟動器

## 功能

wasm 內的 CPython 直譯器啟動後，設定好環境並執行使用者的遊戲。

## 運作方式

`launcher.py` 做三件事：

1. 把工作目錄切換到 `/usr/local/game/`（遊戲檔案解壓後的位置）
2. 把 `/usr/local/game/` 加入 `sys.path`（讓遊戲碼能 import 同目錄的其他模組）
3. 用 `runpy.run_path("main.py", run_name="__main__")` 執行遊戲進入點

`launcher.py` 在建置時被複製到 preload 目錄 `/usr/local/lib/python3.12/`，嵌入 `main.data`。HTML 殼層的 Emscripten `Module.arguments` 設為 `["/usr/local/lib/python3.12/launcher.py"]`，讓 CPython 啟動後直接執行這個腳本而非進入 REPL。

## 相關檔案

- `stubs/launcher.py`：啟動腳本原始碼
- `Makefile`（install-raylib-py 目標）：把 `launcher.py` 複製到 preload 目錄
- `src/rayport/templates/index.html`：`Module.arguments` 設定
