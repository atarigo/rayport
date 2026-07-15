# 模組 04：HTML 殼層產生器

## 功能

產出 `index.html`，這是使用者在瀏覽器開啟的頁面。它負責載入 wasm、顯示載入進度、下載並解壓遊戲檔案、啟動遊戲。

## 運作方式

`generate_html()` 讀取 `src/rayport/templates/index.html` 模板，用 Python 的 `string.Template` 填入參數，產出最終的 HTML。

可透過 `rayport.toml` 自訂的參數：

- `title`：頁面標題（預設 `rayport game`）
- `presentation`：canvas 的 CSS 顯示模式（預設 `stretch`）
- `background`：viewport 未被 canvas 覆蓋時的背景色

遊戲的 render resolution 只由 Python 遊戲碼的 `InitWindow(width, height, ...)` 決定。HTML 不會改寫 `canvas.width` 或 `canvas.height`，只調整 CSS presentation size，避免 raylib、WebGL render target 和網頁同時爭奪解析度。

Emscripten GLFW 預設回傳 CSS pixel 座標。Rayport 會依 GLFW logical window 與 canvas 顯示矩形的比例，把滑鼠座標映射回 raylib resolution；因此 viewport 拉伸、等比例縮放和 letterbox 下的 `GetMouseX()` / `GetMouseY()` 都維持正確範圍。

顯示模式：

- `stretch`：CSS 尺寸為 `100vw × 100dvh`，完整填滿瀏覽器可視區域，比例不同時會拉伸。
- `fit`：保持遊戲比例並盡量填滿 viewport，剩餘區域使用背景色。
- `pixel-perfect`：空間足夠時使用整數倍縮放，適合像素遊戲；空間不足時縮小以保持完整可見。
- `native`：不縮放 canvas。

舊有 `--width` 與 `--height` 仍可一起使用，以維持相容性，但新專案應由 `InitWindow()` 宣告 render resolution。

## HTML 模板的內容

單一模板包含以下基礎結構：

- 載入畫面：黑色背景上的進度條和狀態文字，wasm 初始化完成後隱藏
- canvas 元素：raylib 在這上面繪製遊戲畫面
- 遊戲檔案載入邏輯：以 Emscripten 的 `addRunDependency` / `removeRunDependency` 機制，在 wasm 啟動前完成 `game.tar.gz` 的下載和解壓
- tar.gz 解壓器：純 JS 實作，用 `DecompressionStream("gzip")` 解壓後解析 tar 格式，逐檔寫入虛擬檔案系統的 `/usr/local/game/`
- Emscripten `Module` 物件設定：指定 canvas 元素、啟動參數（`launcher.py` 路徑）、preRun 勾點

wasm 啟動參數設為 `/usr/local/lib/python3.12/launcher.py`，讓 CPython 直接執行 launcher 腳本而非進入 REPL。

## 相關檔案

- `src/rayport/html_generator.py`：模板填充邏輯
- `src/rayport/templates/index.html`：全畫面 HTML 模板
