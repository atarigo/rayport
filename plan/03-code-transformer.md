# 模組 3：程式碼轉換器

## 目的

處理「瀏覽器不允許程式獨佔執行緒」這個問題。

## 問題是什麼

一個 raylib 遊戲的主迴圈長這樣：

```python
while not window_should_close():
    begin_drawing()
    draw_text("Hello", 10, 10, 20, RED)
    end_drawing()
```

在桌面上，這個 `while` 一直跑，作業系統沒問題。但瀏覽器裡，JS 是單執行緒的。如果這個 `while` 一直佔著執行緒，瀏覽器就卡死了——畫面不會更新、按鈕點不了、頁面沒有回應。

瀏覽器要求：你跑一小段，把控制權還給我，讓我更新畫面、處理滑鼠鍵盤，然後你再跑下一小段。

## 怎麼做

有兩條路：

### 路線 A：讓 C 層面自動暫停（ASYNCIFY）

raylib 的 C 原始碼裡，`WindowShouldClose()` 函數會呼叫 `emscripten_sleep(12)`，也就是「暫停 12 毫秒，把控制權交回瀏覽器」。Emscripten 的 ASYNCIFY 功能會在暫停時把整個 C 的函數呼叫堆疊保存下來，12 毫秒後恢復繼續跑。

如果這個機制能穿透 Python 直譯器——也就是說，Python 呼叫 `window_should_close()` → C 的 `WindowShouldClose()` → `emscripten_sleep()` 暫停 → 瀏覽器更新 → 恢復 → 回到 Python——那使用者的程式碼完全不用改。

但有個問題：現有的 raylib-python-cffi wasm build 把 `emscripten_sleep()` 移除了。原因是 CFFI 綁定被編譯成「動態模組」（side module），而 ASYNCIFY 跟動態模組不相容。

如果我們改成把 CFFI 綁定靜態連結進主模組（模組 1 的編譯方式改變），就能恢復 ASYNCIFY。代價是 wasm 體積增大約 50%，且需要驗證技術可行性。

### 路線 B：自動改寫使用者程式碼（coroutine）

用 Python 的 AST 模組解析使用者的程式碼，自動把遊戲迴圈改成 async 版本。在每個 `end_drawing()` 呼叫後插入 `await asyncio.sleep(0)`，把控制權交回瀏覽器。

改寫後的程式碼：

```python
async def main():
    while not window_should_close():
        begin_drawing()
        draw_text("Hello", 10, 10, 20, RED)
        end_drawing()
        await asyncio.sleep(0)  # ← 插入這行

asyncio.run(main())
```

這是目前 pygbag + raylib-python-cffi 實際在用的做法，已驗證可行。

## 哪條路比較好

路線 A 對使用者最友善（不用改程式碼），但需要驗證技術可行性。路線 B 已經驗證可行，但使用者要接受程式碼被改寫（或自己加 `await`）。

可以先走路線 B 確保能用，同時研究路線 A 的可行性。
