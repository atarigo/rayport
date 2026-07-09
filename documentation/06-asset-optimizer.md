# 模組 06：資源優化器

## 功能

壓縮 PNG 圖片和轉換音訊格式，減少遊戲的下載大小。

透過 `rayport build --optimize` 啟用。這是可選功能，不啟用時所有資源檔原樣打包。

## 運作方式

`optimize_assets()` 走訪遊戲目錄，根據副檔名分類處理：

- `.png`：呼叫 pngquant 壓縮，品質範圍 65-80
- `.wav`、`.mp3`：呼叫 ffmpeg 轉成 `.ogg`（libvorbis 編碼、44100 Hz、單聲道、品質等級 4）
- 其他檔案：直接複製

處理結果寫入暫存目錄，不動使用者的原始檔案。打包器從暫存目錄打包，打包完成後清理暫存目錄。

## 外部工具依賴

pngquant 和 ffmpeg 需要使用者自行安裝。工具不存在時只印一次警告，不中斷打包流程，該類型的檔案原樣複製。

pngquant 壓縮失敗時（例如圖片已經很小、壓縮後反而變大），也原樣複製原始檔案。

## 相關檔案

- `src/rayport/optimizer.py`：優化邏輯
- `src/rayport/packager.py`：呼叫優化器的整合點（`pack_game()` 的 `optimize` 參數）
