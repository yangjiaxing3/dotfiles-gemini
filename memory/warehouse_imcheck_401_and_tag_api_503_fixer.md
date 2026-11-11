# [Fixer Post-Mortem] `/warehouse` 頁面 `imcheck-blacklist` 401 與 `api/hardware/tags` 503 根因與治理模式

## [Anti-Pattern 錯誤模式]
1. **頂欄全站 Hook 未守門 Session Token 即打 Edge Function 且透傳上游 401**：
   - `Layout.tsx` 全站掛載 `useBlacklistCases()`，但 `src/features/blacklist/api.ts` 在正式站分支未先等待 `supabase.auth.getSession()` 並顯式帶入 `Authorization: Bearer <access_token>`。
   - 上游 `www.imcheck.com.tw/api/blacklist/admin` 新增 `requireAdmin()`（檢查 `x-admin-api-key`）後回傳 HTTP `401 {"error":"UNAUTHORIZED"}`，Edge Function `imcheck-blacklist` 原封不動以 HTTP `401` 回傳給瀏覽器，且 React Query 預設重試 3 次，導致全站每頁（含 `/warehouse`）Console 連噴 `401 ()` 紅字。
2. **硬體輪詢代理將上游「守護程序未啟動」的業務 JSON 直接以 HTTP 503 回傳瀏覽器**：
   - `EcommerceShipTodayStrip.tsx` 在 `/warehouse` 每 30 秒輪詢 `/api/hardware/tags?action=status`。當現場 `tag_server.php` 未執行時，上游 `tag_api.php` 回傳 HTTP `503` + `{"ok":false,"error":"tag_server.php 沒有在執行"}`，代理原樣回傳 `503` 導致瀏覽器網路層每 30 秒強制印出 `503 ()` 紅字。

## [Correct-Pattern 正確作法]
1. **BFF / Edge Function 認證鏈路與上游狀態解耦**：
   - 前端 `authedFetch` 與 `useBlacklistCases` 強制先確認 `Boolean(session?.access_token)` 並顯式帶入 `Authorization` header，同時設 `retry: false` 防止重試風暴。
   - Edge Function (`supabase/functions/imcheck-blacklist/index.ts`) 與本機 Vite Proxy (`vite-plugin-imcheck-blacklist.ts`) 支援帶入 `x-admin-api-key`（讀取 `IMCHECK_ADMIN_API_KEY`），且在呼叫者通過本系統 JWT + RBAC 驗證後，將上游非 2xx 轉為 HTTP `200` 結構化錯誤 `{ ok: false, error, upstreamStatus }`，由前端依 `'error' in data` 處理，徹底消除全站頂欄的瀏覽器 401 紅字。
2. **硬體狀態輪詢的結構化業務錯誤正規化**：
   - `api/hardware/tagApi.ts` 在 `TAG_API_TOKEN` 缺失時維持回傳 `503`、上游網路斷線回傳 `502`（完整保留單元測試契約）；當上游已成功回應含布林 `ok` 的業務 JSON（如 `{ ok: false, error: "tag_server.php 沒有在執行" }`）時，以 HTTP `200` 回應並由 `tagApiClient.ts` 依 `body.ok === false` 拋出業務錯誤，兼顧 UI 狀態提示與零瀏覽器 503 紅字。
