# 模組 02：專案打包器

## 功能

收集使用者的遊戲碼和資源檔（圖片、音效、字型等），打包成瀏覽器可下載的 `game.tar.gz`。

## 運作方式

`pack_game()` 走訪遊戲專案目錄，套用預設規則與 `rayport.toml` 的規則後，把剩餘檔案打成 tar.gz。

預設跳過的目錄：`.git`、`__pycache__`、`.venv`、`venv`、`node_modules`、`build`、`.mypy_cache`、`.pytest_cache`、以 `.` 開頭的隱藏路徑。

預設跳過的檔案：`.DS_Store`、`.pyc`、`.pyo`、`rayport.toml`。

遊戲可以在 `rayport.toml` 加入 glob 規則：

```toml
[package]
exclude = ["tests/**", "debug/**", "screenshots/**"]
include = ["tests/runtime_data/**"]
```

`include` 的優先權高於預設和自訂排除規則，可用於明確取回某個檔案。CLI 提供可檢查的決策結果：

```bash
rayport inspect ./game --excluded
rayport inspect ./game --explain tests/test_game.py
```

遊戲專案目錄必須包含 `main.py` 作為進入點。

啟用 `--optimize` 時，只有通過相同 include/exclude 規則的檔案會複製到暫存目錄並交給資源優化器，再打包優化過的版本。原始檔案不受影響。

## 瀏覽器端的解壓

`game.tar.gz` 由 `index.html` 的 JS 邏輯處理。瀏覽器下載後，透過 `DecompressionStream("gzip")` 解壓，再解析 tar 格式，逐檔寫入 wasm 虛擬檔案系統的 `/usr/local/game/`。

## 相關檔案

- `src/rayport/packager.py`：打包邏輯
- `src/rayport/cli.py`：CLI 入口（`rayport build`）
