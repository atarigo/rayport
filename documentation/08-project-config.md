# 模組 08：遊戲專案設定

## 設定檔位置

Rayport 會在遊戲根目錄尋找 `rayport.toml`。也可以用 `--config PATH` 指定其他檔案。

```toml
config-version = 1

[web]
title = "My Game"
presentation = "stretch"
background = "#1a1a2e"

[package]
exclude = ["tests/**", "debug/**", "demo/**"]
include = ["tests/runtime_data/**"]
```

設定優先序為：CLI option、`rayport.toml`、Rayport default。未知欄位、錯誤型別、未知版本或未知 presentation mode 都會讓建置立即失敗，避免拼字錯誤被靜默忽略。

## Web 設定

- `title`：HTML page title。
- `presentation`：`stretch`、`fit`、`pixel-perfect` 或 `native`。
- `background`：CSS 色彩名稱或 hexadecimal color。

Rayport 不會從 Python source 猜測 `InitWindow()` 的數值，也不會從 JavaScript 改寫 canvas render target。遊戲碼是 render resolution 的唯一來源，`presentation` 只處理 CSS 顯示大小。

## Package 設定

- `exclude`：在預設排除規則之後套用的 glob patterns。
- `include`：優先於所有排除規則的 glob patterns。

`rayport.toml` 本身預設不會放入遊戲包。可先檢查每個檔案的決策，不需要反覆解開 tar：

```bash
rayport inspect ./game --excluded
rayport inspect ./game --explain debug/overlay.py
```

設定檔變更後，需重新執行 `rayport build` 或重啟 `rayport dev`。
