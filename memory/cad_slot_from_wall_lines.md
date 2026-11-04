# CAD 倉位必須用牆線矩形，不能用文字標籤框

- 日期：2026-09-07
- 專案：STOREASY_IT

## Anti-Pattern

把 DXF TEXT 插入點加上固定 60×40 當倉位幾何。真實店圖「單層倉」常是 4 條 LINE，不是封閉 LWPOLYLINE；前端再用預設 DOMPurify HTML profile，會把 svg/line/path 整張拆掉，畫面上只剩漂浮標籤。

## Correct-Pattern

1. 從 wall 圖層的水平／垂直 LINE 重建軸對齊矩形，文字落在格內才綁 slot_number。
2. slot.x/y/width/height 用格子 bbox。
3. 平面圖 SVG 必須用 `USE_PROFILES: { svg: true }` 消毒，並與 overlay 共用同一 viewBox。
4. mm 圖的 stroke 維持 1–3px，文字用 DXF height × scale 並夾在 8–22px。禁止 `12/(scale*0.01)`，否則字級會到數千 px，疊成整片灰色陰影。
