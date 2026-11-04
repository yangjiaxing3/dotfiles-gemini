---
name: kiosk-image-optimizer
description: "Use when compressing, resizing (<=1500px), and converting 24H recycling kiosk or branch photos to WebP (<=250KB). 門市回收機圖片壓縮/縮圖轉WebP"
---

# 🖼️ Kiosk Image Optimizer Skill (據點圖片優化與過濾技能)

本技能用於處理 US3C 機台據點與實體門市的照片資產庫（來源包含 Google Drive 資料夾 `1rCG6BeI045FISWqf8tqTPx9hagXIHqzU`）。

## 核心規格與限制 (Image Quality & Size Budget Rules)

1. **尺寸重定 (Dimensions & Orientation)**：
   - 橫向照片 (Landscape) 寬度強制縮減至 **1500px**（高依比例自動等比縮放）。
   - 直向照片 (Portrait) 高度控制在 **1500px** 內。
   - 嚴禁放大原圖（僅對原圖 > 1500px 者進行 downscaling）。

2. **檔案大小預算 (File Size Limit)**：
   - 單張圖片檔案大小 **絕對不可超過 250KB** (`<= 250KB`)。
   - 使用 WebP 格式 (80-85% 壓縮率) 或 高品質 JPEG 進行優化。

3. **據點對位目錄結構 (Directory Structure)**：
   - 來源資料夾命名需精準對應 `storeId` 或 `slug`（例：`518Q2506039` 或 `kiosk-taipei-518q2506039`）。
   - 前台靜態資源路徑統一存放至 `public/images2/locations/[storeId]/`。
   - 命名格式遵循 SEO 規範：`us3c-[storeId]-store-[index].webp` (或 `.jpg`)。

## 執行腳本 (Python / Node Optimizer Scripts)

可以使用 `python scripts/optimize-kiosk-images.py` 或 `node scripts/optimize-kiosk-images.mjs` 進行全量自動化轉檔與壓縮。

### Python 處理核心語法範例：

```python
from PIL import Image
import os

def optimize_image(input_path, output_path, max_width=1500, max_kb=250):
    with Image.open(input_path) as img:
        # 轉 RGB 避免 PNG/RGBA 轉 WebP/JPEG 顏色異常
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")

        # 尺寸縮減 (寬度限制 1500px)
        width, height = img.size
        if width > max_width:
            new_height = int(height * (max_width / width))
            img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)

        # 迭代壓縮直到檔案 <= 250KB
        quality = 85
        img.save(output_path, "WEBP", quality=quality, optimize=True)

        while os.path.getsize(output_path) > max_kb * 1024 and quality > 30:
            quality -= 5
            img.save(output_path, "WEBP", quality=quality, optimize=True)
```

## ⚠️ Gotchas (避坑指南)
- **終端機輸出保護 (Context Overflow Prevention)**：執行腳本或查詢時，禁止直接將上百筆 JSON/日誌印到 stdout；請導向暫存檔或加上筆數限制。
- **優先使用確定性腳本**：遇到格式轉換、字數統計或合規檢查，優先調用 `scripts/` 下的 Python 工具，不要依賴純語意猜測。
