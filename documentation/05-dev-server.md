# 模組 05：開發伺服器

## 功能

提供本地 HTTP server 讓使用者在瀏覽器中測試遊戲，附帶檔案監控和自動重載。

透過 `rayport dev ./my-game/` 啟動。

## 為什麼需要 HTTP server

瀏覽器不允許從 `file://` 載入 `.wasm` 檔，也不允許 `file://` 使用 fetch API。wasm 的某些功能（SharedArrayBuffer）需要特定的 HTTP headers 才能啟用。

## 運作方式

`run_dev()` 啟動後：

1. 執行一次完整建置（打包遊戲、產生 HTML、複製 runtime 檔案到 output 目錄）
2. 啟動 `FileWatcher`，每秒掃描遊戲目錄的檔案修改時間
3. 啟動 HTTP server，開啟瀏覽器
4. 被納入 package 的檔案變動時自動重新打包 `game.tar.gz`，遞增 reload version
5. 瀏覽器端的 JS 每秒輪詢 `/__reload` endpoint，偵測到 version 變化時重新載入頁面

## HTTP server 的特殊處理

- 所有回應加上 `Cross-Origin-Opener-Policy: same-origin` 和 `Cross-Origin-Embedder-Policy: require-corp` headers
- `.wasm` 檔案回應 `Content-Type: application/wasm`
- `index.html` 回應時注入 livereload script（輪詢 `/__reload` 的 JS 片段）
- `/__reload` endpoint 回傳 `{"v": <reload_version>}` JSON
- `/__reload` 的請求不記錄到 server log

## FileWatcher

基於輪詢的檔案監控，每秒掃描一次遊戲目錄所有檔案的 `st_mtime`，偵測新增、修改、刪除三種變化。只有通過 `rayport.toml` package 規則的變更會觸發重新打包；若 output 位於 game project 內，FileWatcher 會直接略過該 subtree，避免生成檔造成 reload loop。修改設定檔本身後需重啟 dev server。

以 daemon thread 執行，主執行緒結束時自動停止。

## CLI 參數

- `game_dir`：遊戲專案目錄路徑
- `--output` / `-o`：輸出目錄（預設 `build`）
- `--title` / `-t`：覆寫遊戲標題
- `--presentation`：覆寫 canvas presentation mode
- `--background`：覆寫頁面背景色
- `--width` / `-W`、`--height` / `-H`：相容舊版的初始 canvas 尺寸，必須一起使用
- `--port` / `-p`：server port（預設 8080）
- `--force-output`：明確允許取代沒有 `.rayport-output` marker 的非空 output

## 相關檔案

- `src/rayport/dev_server.py`：server、FileWatcher、livereload 邏輯
- `src/rayport/cli.py`：CLI 入口（`rayport dev`）
