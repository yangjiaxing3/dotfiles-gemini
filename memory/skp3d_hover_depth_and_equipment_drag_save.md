# 3D Sitemap 1秒懸停對位、Drag-and-Drop 拖曳與 localStorage 持久化經驗萃取

## [Anti-Pattern 錯誤模式]
1. **3D 等角透視下使用 `depthTest: false` 繪製被遮擋物件的 12 稜線外框**：
   - 當後排上層倉位（如 `U463`）下半部被前排倉位（如 `471`）遮擋時，若高亮外框設定 `depthTest: false`，被遮擋的底面稜線會強行畫在前排櫃頂上方，產生嚴重的 Necker Cube 視錯覺，看起來像外框脫離櫃體、浮在半空中。
2. **在 `pointerdown` 立即觸發 `zoomToEquipment3D` 鏡頭飛行**：
   - 使用者準備按住滑鼠左鍵拖曳（Drag-and-Drop）3D 設備時，若 `pointerdown` 立即啟動 `camAnim` 鏡頭推進，會導致滑鼠射線與水平拖曳平面（`eqDragPlane`）相對座標劇烈偏移，無法穩定拖動。
3. **`localStorage` 還原迴圈內呼叫未暴露至全域的局部閉包函式**：
   - `loadEquipmentIotStateFromStorage()` 位於頂層作用域，內部呼叫 `syncEquipmentHealthVisuals3D(it)` 時，若材質輔助函式（`getStatusVisualMaterials`、`getMepBadgeMaterial`）僅定義於 `buildStoreasyCeilingInfrastructure` 閉包內，第 0 筆設備就會拋出 `ReferenceError` 並被 `try/catch` 靜默吞掉，導致後續設備的 `x, y, z` 座標無法還原。

## [Correct-Pattern 正確作法]
1. **真實深度測試（`depthTest: true`）+ 櫃體自身微發光 + 頂蓋品牌金對位框**：
   - `sitemapActiveBoxHelper` 一律啟用 `depthTest: true`，直接使用 `targetCab.position` 與 `(b.x1..x2, b.y1..y2, b.z1..z2)` 包覆櫃體，並搭配 `applyActiveHoveredUnitGlow(targetCab)` 提升櫃體材質自發光與邊線對比。
2. **分離 Click 與 Drag（4px 位移閾值）**：
   - `pointerdown` 僅記錄 `downOnEqItem` 與點擊偏移量 `eqDragOffset`；`pointermove` 位移 `> 4px` 才進入 `isDraggingEquipment = true`（並鎖定 `camAnim = null`），`pointerup` 位移 `<= 4px` 才執行單擊聚焦。
3. **跨作用域共用函式顯式掛載 `window.*` 並加上 E2E 重整驗證**：
   - 凡會被頂層狀態還原呼叫的 3D 材質生成函式一律掛載於 `window`，且 E2E 測試必須涵蓋 `drag -> save -> page.reload() -> 座標與 3D position 一致性斷言`。
