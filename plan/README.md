# raylib Python Web 打包工具

把 raylib Python 遊戲打包到瀏覽器上跑的工具。

## 開發順序

模組之間有依賴關係，每個階段能獨立交付和測試。

```
第一階段：模組 1 + 7（wasm runtime）
    ↓
第二階段：模組 3（遊戲迴圈）
    ↓
第三階段：模組 2 + 4（打包 CLI）
    ↓
第四階段：模組 5（dev server）
    ↓
第五階段：模組 6（資源優化，選做）
```

| 階段 | 模組 | 交付物 |
|------|------|--------|
| 第一階段 | 01 + 07 | wasm runtime，啟動後自動執行虛擬檔案系統中的 Python 遊戲 |
| 第二階段 | 03 | 遊戲迴圈能在瀏覽器中持續執行不凍結 |
| 第三階段 | 02 + 04 | `rayport build` 指令，一鍵打包遊戲 |
| 第四階段 | 05 | `rayport dev` 指令，改程式碼後瀏覽器自動更新 |
| 第五階段 | 06 | `rayport build --optimize` 選項（選做） |

## 模組目錄

| 模組 | 說明 |
|------|------|
| [01-wasm-base](01-wasm-base.md) | wasm 基礎建設 — 編譯 CPython + raylib 成瀏覽器可執行的格式 |
| [02-project-packager](02-project-packager.md) | 專案打包器 — 收集遊戲檔案和資源打包 |
| [03-code-transformer](03-code-transformer.md) | 程式碼轉換器 — 處理瀏覽器不允許獨佔執行緒的問題 |
| [04-html-shell](04-html-shell.md) | HTML 殼層產生器 — 產出承載遊戲的 HTML 頁面 |
| [05-dev-server](05-dev-server.md) | 開發伺服器 — 本地測試用 HTTP server |
| [06-asset-optimizer](06-asset-optimizer.md) | 資源優化器 — 壓縮圖片和音訊減少下載大小（可選） |
| [07-runtime-launcher](07-runtime-launcher.md) | Python Runtime 啟動器 — 在 wasm 中啟動並執行使用者的遊戲 |

## 其他文件

| 文件 | 說明 |
|------|------|
| [poc-log](poc-log.md) | POC 驗證記錄 — 技術可行性驗證的完整過程、方法、結果與踩坑紀錄 |

## 全螢幕

raylib 的 C 層面已經實作了全螢幕切換，Python 裡呼叫 `toggle_fullscreen()` 就行。

## 跟 pygbag 的差異

pygbag 是通用工具，為了支援所有 Python 遊戲框架，在 Python 層面做了大量替換（asyncio、threading、urllib 等）。這個工具只專注 raylib，raylib 的 C 層面已經處理了大部分 Web 平台問題，所以 Python 層面可以簡單得多。
