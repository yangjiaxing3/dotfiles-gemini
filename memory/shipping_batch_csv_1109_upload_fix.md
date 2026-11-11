# 出貨單頁面 `1109.csv` 上傳解析卡住 5 分鐘之根因診斷與修復

<PatternExtract>
- Anti-Pattern:
  1. 在 `ShippingBatchPanel.tsx` 中，`<input type="file" accept=".csv,text/csv">` 的 `onChange` 僅執行 `void file.text().then(setCsv)` 且未清空 `event.target.value`，沒有自動觸發 `readIn()` 解析與展開批次；同時當 `stock_confirmations` 全為 `shortage`（未鎖定合約號）時，`GatedBatchTable` 將 86 列歸入 `hidden` 且未提供 CSV 解析明細預覽，導致使用者選檔後畫面毫無變化或看不到任何訂單列。
  2. 在 `shipOrderLog.ts` 的 `fetchShipOrderLatest` 對 82+ 筆訂單直接 `Promise.all(sns.map(...))` 無限制並發發起 N+1 HTTP 查詢。
  3. 在 `mall-server/orders/csv.ts` 的 `headerIndex` 以 `headers.findIndex` 從左至右匹配而非依 `aliases` 優先序匹配（在 `1109.csv` 誤抓第 6 欄空「品名」而忽略第 13 欄「商品名稱」），且 `shopee-file.ts` 缺少「2026蝦皮出貨清單」欄位別名與隱碼 `****` fallback，`ingest.ts` 逐筆串行 `await insertIfAbsent` 導致 82 筆訂單在 Serverless 超時。
- Correct-Pattern:
  1. 選取 CSV 檔案後立即推斷分頁名（如 `1109`）、清空 `event.target.value` 並自動執行 `applyBatchCsv` 入庫與選取；在 `GatedBatchTable` 保留 ADR 0009 出貨/列印門禁的同時，提供 `RawBatchSheetPreview` 展開顯示 CSV 解析出的全部列與狀態統計。
  2. `fetchShipOrderLatest` 與 `runIngest` 均採用 `chunkSize = 8~10` 分批並發控制，兼顧單筆查詢測試契約與連線池穩定度。
  3. `headerIndex` 依 `aliases` 優先序比對並正規化換行空白，`shopee-file.ts` 完整支援「2026蝦皮出貨清單」欄位與隱碼 fallback。
- Tags: #csv #xlsx #warehouse #shipping #mall #performance #react #supabase
</PatternExtract>
