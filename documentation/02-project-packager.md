# 模組 02：專案打包器

## 功能

收集使用者的遊戲碼和資源檔（圖片、音效、字型等），打包成瀏覽器可下載的 `game.tar.gz`。

## 運作方式

`pack_game()` 走訪遊戲專案目錄，跳過不需要的檔案後，把剩餘檔案打成 tar.gz。

跳過的目錄：`.git`、`__pycache__`、`.venv`、`venv`、`node_modules`、`build`、`.mypy_cache`、`.pytest_cache`、以 `.` 開頭的隱藏目錄。

跳過的檔案：`.DS_Store`、`.pyc`、`.pyo`。

遊戲專案目錄必須包含 `main.py` 作為進入點。

啟用 `--optimize` 時，`pack_game()` 先把遊戲目錄複製到暫存目錄，呼叫資源優化器處理後，再打包優化過的版本。原始檔案不受影響。

## 瀏覽器端的解壓

`game.tar.gz` 由 `index.html` 的 JS 邏輯處理。瀏覽器下載後，透過 `DecompressionStream("gzip")` 解壓，再解析 tar 格式，逐檔寫入 wasm 虛擬檔案系統的 `/usr/local/game/`。

## 相關檔案

- `src/rayport/packager.py`：打包邏輯
- `src/rayport/cli.py`：CLI 入口（`rayport build`）
