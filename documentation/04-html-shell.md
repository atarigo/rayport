# 模組 04：HTML 殼層產生器

## 功能

產出 `index.html`，這是使用者在瀏覽器開啟的頁面。它負責載入 wasm、顯示載入進度、下載並解壓遊戲檔案、啟動遊戲。

## 運作方式

`generate_html()` 讀取 `src/rayport/templates/index.html` 模板，用 Python 的 `string.Template` 填入參數，產出最終的 HTML。

可自訂的參數：

- `title`：頁面標題（預設 `rayport game`）
- `width`：canvas 寬度（預設全畫面）
- `height`：canvas 高度（預設全畫面）

未指定寬高時使用全畫面模板，canvas 以 `window.innerWidth` / `window.innerHeight` 動態填滿視窗，並監聽 resize 事件自動調整。指定寬高時使用固定尺寸模板，canvas 設定固定的 width/height 屬性。

## HTML 模板的內容

兩個模板共用相同的基礎結構：

- 載入畫面：黑色背景上的進度條和狀態文字，wasm 初始化完成後隱藏
- canvas 元素：raylib 在這上面繪製遊戲畫面
- 遊戲檔案載入邏輯：以 Emscripten 的 `addRunDependency` / `removeRunDependency` 機制，在 wasm 啟動前完成 `game.tar.gz` 的下載和解壓
- tar.gz 解壓器：純 JS 實作，用 `DecompressionStream("gzip")` 解壓後解析 tar 格式，逐檔寫入虛擬檔案系統的 `/usr/local/game/`
- Emscripten `Module` 物件設定：指定 canvas 元素、啟動參數（`launcher.py` 路徑）、preRun 勾點

wasm 啟動參數設為 `/usr/local/lib/python3.12/launcher.py`，讓 CPython 直接執行 launcher 腳本而非進入 REPL。

## 相關檔案

- `src/rayport/html_generator.py`：模板填充邏輯
- `src/rayport/templates/index.html`：全畫面 HTML 模板
- `src/rayport/templates/index_fixed.html`：固定尺寸 HTML 模板
