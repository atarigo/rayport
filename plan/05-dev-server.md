# 模組 5：開發伺服器

## 目的

讓使用者在本地開發時能在瀏覽器裡測試遊戲。

## 為什麼需要

不能直接用 `file://` 開 HTML 檔，因為：

1. 瀏覽器的安全限制不允許 `file://` 載入 `.wasm` 檔
2. wasm 的某些功能（SharedArrayBuffer）需要特定的 HTTP headers 才能啟用
3. fetch API（下載遊戲檔案用的）不支援 `file://`

## 怎麼做

一個簡單的 HTTP server（Python 內建的 `http.server` 就夠），加上兩個必要的 HTTP headers：

- `Cross-Origin-Opener-Policy: same-origin`
- `Cross-Origin-Embedder-Policy: require-corp`

還有一個 MIME type 修正：`.wasm` 檔必須回應 `application/wasm`，有些系統沒有預設註冊這個。

可以加檔案監控：偵測使用者改了 `.py` 檔就自動重新打包，省去手動操作。
