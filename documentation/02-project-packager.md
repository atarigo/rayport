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
rayport inspect ./game --sizes
```

`--sizes` 依未壓縮大小列出將被打包的檔案，並標示超過 5 MiB 的資源供開發者檢查。Rayport 不會隱藏地壓縮、轉檔或更改任何遊戲資源；圖片與音訊最佳化由遊戲自己的 asset pipeline 明確處理。

遊戲專案目錄必須包含 `main.py` 作為進入點。

## Output 安全

Rayport 在清理 output 前會先檢查 canonical path：output 不可等於遊戲目錄，也不可是遊戲目錄的上層。非空 output 必須含有 Rayport 建立的 `.rayport-output` marker，否則拒絕刪除；只有使用者明確傳入 `--force-output` 才能取代其他目錄。

output 可以位於遊戲目錄內，例如 `dist/`。Rayport 會依實際相對路徑自動排除整個 output subtree，不依賴目錄名稱，也不會讓生成檔重新進入 `game.tar.gz`。

## 瀏覽器端的解壓

`game.tar.gz` 由 `index.html` 的 JS 邏輯處理。瀏覽器下載後，透過 `DecompressionStream("gzip")` 解壓，再解析 tar 格式，逐檔寫入 wasm 虛擬檔案系統的 `/usr/local/game/`。

解析器支援 POSIX PAX extended headers 與 ustar prefix，因此超過傳統 100-byte 欄位的 UTF-8 路徑仍可還原。解壓前會拒絕 absolute path、反斜線與 `..` path segment，並拒絕不支援的 tar entry type。

## 相關檔案

- `src/rayport/packager.py`：打包邏輯
- `src/rayport/cli.py`：CLI 入口（`rayport build`）
