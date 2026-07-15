# rayport 文件

rayport 把 raylib Python 遊戲打包到瀏覽器上跑。

CPython 直譯器和 raylib 引擎被編譯成一個 WebAssembly binary，使用者的 Python 遊戲碼透過虛擬檔案系統載入，由 wasm 內的 CPython 直譯器執行。使用者不需要安裝 Emscripten 或任何 C 工具鏈。

## 模組

| 模組 | 說明 |
|------|------|
| [01-wasm-base](01-wasm-base.md) | wasm 基礎建設：CPython + raylib + CFFI 綁定，編譯成一個 wasm binary |
| [02-project-packager](02-project-packager.md) | 專案打包器：收集遊戲檔案和資源，打包成 tar.gz |
| [03-game-loop](03-game-loop.md) | 遊戲迴圈：透過 ASYNCIFY 讓遊戲迴圈在瀏覽器中持續執行 |
| [04-html-shell](04-html-shell.md) | HTML 殼層產生器：產出承載遊戲的 HTML 頁面 |
| [05-dev-server](05-dev-server.md) | 開發伺服器：本地測試用 HTTP server，附檔案監控與自動重載 |
| [07-runtime-launcher](07-runtime-launcher.md) | Runtime 啟動器：wasm 啟動後自動執行使用者的遊戲 |
| [08-project-config](08-project-config.md) | 遊戲專案設定：Web presentation 與 package include/exclude 規則 |

## 其他文件

| 文件 | 說明 |
|------|------|
| [architecture](architecture.md) | 整體技術架構與建置流程 |
| [history/poc-log](history/poc-log.md) | POC 驗證記錄（歷史文件） |
