# 模組 03：遊戲迴圈

## 功能

讓 Python 的遊戲迴圈（`while not WindowShouldClose()`）在瀏覽器中持續執行，不凍結頁面。

## 問題

瀏覽器的 JS 是單執行緒的。Python 的 `while` 迴圈如果持續佔住執行緒，瀏覽器無法更新畫面、處理輸入，頁面會凍結。

## 解法：ASYNCIFY

raylib 的 C 碼在 `WindowShouldClose()` 函數內呼叫 `emscripten_sleep(12)`，暫停 12 毫秒把控制權交回瀏覽器。Emscripten 的 ASYNCIFY 功能在暫停時保存整個 C 呼叫堆疊，包括 CPython 的 ceval.c 主迴圈，12 毫秒後恢復繼續執行。

連結時的旗標：`-sASYNCIFY -sASYNCIFY_STACK_SIZE=65536`。

這個方案的優點是使用者的 Python 遊戲碼完全不需要修改。標準的 raylib 遊戲迴圈直接能跑：

```python
while not WindowShouldClose():
    BeginDrawing()
    ClearBackground(RAYWHITE)
    DrawText(b"Hello", 10, 10, 20, RED)
    EndDrawing()
```

## 前提條件

ASYNCIFY 需要靜態連結才能運作。模組 01 移除了 `-sMAIN_MODULE`（改為全部靜態連結），使得 ASYNCIFY 能穿透 CPython 的直譯器迴圈。如果使用動態連結，ASYNCIFY 無法追蹤跨模組的呼叫堆疊。

## 相關檔案

- `Makefile`（link 目標）：連結旗標中的 `-sASYNCIFY -sASYNCIFY_STACK_SIZE=65536`
