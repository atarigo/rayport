# 模組 4：HTML 殼層產生器

## 目的

產出一個 HTML 頁面，這個頁面就是使用者最終在瀏覽器裡開啟的東西。它負責載入 wasm、顯示遊戲畫面、提供載入進度條。

## 要做什麼

產出一個 `index.html`，裡面包含：

- 一個 `<canvas>` 元素——raylib 在這上面畫遊戲畫面
- 一個 `<script>` 載入 `main.js`（Emscripten 的膠水碼）
- 一些 JS 邏輯：設定 canvas 大小、顯示載入進度、下載並解壓遊戲檔案（如果用 runtime fetch 方式）
- 頁面標題、favicon、背景色等可自訂的外觀

## 怎麼做

用模板引擎（Jinja2 或 Python 內建的 string.Template）。定義一個 HTML 模板，裡面有佔位符（標題、canvas 大小、遊戲檔案名等），打包時填入實際值產出最終的 HTML。

Emscripten 本身有 `--shell-file` 參數接受 HTML 模板，raylib 也提供了一個最小的 `minshell.html`。可以基於它修改。
