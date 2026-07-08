# 模組 7：Python Runtime 啟動器

## 目的

在瀏覽器裡的 wasm Python 直譯器啟動後，設定好環境，然後執行使用者的遊戲。

## 要做什麼

wasm 啟動後，CPython 直譯器跑起來了，但它不知道要執行哪個 `.py` 檔。這個啟動器告訴它：

1. 遊戲檔案在虛擬檔案系統的哪個目錄
2. 把那個目錄加進 Python 的模組搜尋路徑
3. 執行 `main.py`

## 怎麼做

一個極短的 Python 腳本：

```python
import sys, os, runpy
game_dir = "/data/data/game/assets"
os.chdir(game_dir)
sys.path.insert(0, game_dir)
runpy.run_path("main.py", run_name="__main__")
```

就這樣。不需要像 pygbag 那樣搞 1700 行的啟動腳本。不需要替換標準庫模組、不需要 shell 指令集、不需要 REPL、不需要套件管理器。因為所有遊戲需要的東西（raylib 綁定、Python 標準庫）在模組 1 的編譯階段就已經嵌進 wasm 了。
