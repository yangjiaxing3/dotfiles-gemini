# 倉位關聯只認號碼，不認尺寸

- 日期：2026-09-11
- 專案：STOREASY_IT / StoreasyFMnew

## 規則

CAD 平面圖上的倉位寬深，可以跟價目表／`storage_inventory.size` 有些許不同。這是正常的。

真正的關聯是 **倉位號碼**（DXF 文字 `TD522` ↔ FM `st_id`）。DXF 是為了空間資訊（之後 3D、室內導航），不是拿來對價格尺寸。

## Anti-Pattern

用 width/height 或價目 size 去 match FM 格位。或因圖層名不是「單層倉」、外框是短 LINE，就把格子退回 60×40 標籤框。

## Correct-Pattern

1. `auto_match` / `bind` 只比 `slot_number` 與 `st_id`。
2. 格位幾何：文字附近的軸對齊牆線（含短線拼接、不限圖層）圍出 bbox，再換算公尺。
3. 尺寸差不阻斷綁定。
4. 新莊公園有兩種外框：部分是 LINE（約 1109×700–900 mm），其餘是 LWPOLYLINE（約 843×400 mm）。先 LINE 再就近多段線，避免內框把已對上的 LINE 倉位縮小。
