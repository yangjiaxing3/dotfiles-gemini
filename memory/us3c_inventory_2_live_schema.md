# us3c 正式庫 inventory_2 欄位（2026-08-29）

[Anti-Pattern 錯誤模式]
- 用 HQ TypeScript 型別（accepted_items、receipt_date、sku、accepted_quantity、item status=completed/accepted）直接 insert／update 正式庫。
- PostgREST 回 PGRST204 / 23502 / 23514，ensurePickupReceipt 只 console.error，任務仍 200 completed，lookup 變成 404。

[Correct-Pattern 正確作法]
- 寫入前先查正式庫真實欄位與 check constraint（或既有列的 distinct status）。
- header：received_items、received_date、delivery_date（NOT NULL，YYYY-MM-DD）。沒有 accepted_items／receipt_date。
- items：不要寫 sku／accepted_quantity；status 只允許 pending／received／rejected。
- API 回傳再把 received_* 映成前端 accepted_*。
