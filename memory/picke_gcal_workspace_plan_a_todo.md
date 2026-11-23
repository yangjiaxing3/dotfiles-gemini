# PICKÉ+ Google 日曆雙向整合：方案 A 待辦與實作規格

> 狀態：**[TODO - 等待 IT 申請帳號與憑證]**
> 決策日期：2026-11-23
> 目標專案：`StoreasyFMnew`（PICKÉ+ 預約與營運模組）

## 1. 決策摘要

- 使用者已拍板採 **方案 A（公司 Google Workspace 專屬營運帳號）**，向公司 IT 申請專屬營運帳號與獨立日曆權限，申請需時間；待帳號、日曆 ID 與服務帳戶憑證就緒後，再啟動工程開發。
- 依賴套件 `google-auth>=2.28.0`、`google-api-python-client>=2.0.0` 已列於 `backend/requirements.txt`。

## 2. 老闆／IT 端前置檢核表

1. **申請 Workspace 專屬營運帳號**：建議命名 `picke-neihu@storeasy.com.tw`。
2. **建立 3 本獨立次日曆**（時區強制設為 `(GMT+08:00) 台北`）：
   - `PICKÉ+ A場 (VIP)` → 對應 SKU `PKM-VIP`
   - `PICKÉ+ B場 (一般場A)` → 對應 SKU `PKM-GEN-A`
   - `PICKÉ+ C場 (一般場B)` → 對應 SKU `PKM-GEN-B`
3. **沿用既有 `StoreasyFMnew` GCP 專案，建立獨立服務帳戶**：
   - 於該 GCP 專案啟用 `Google Calendar API`。
   - 建立專屬服務帳戶 `picke-gcal-sync`（最小權限隔離，**切勿與 Drive／Sheets 服務帳戶共用金鑰**）。
4. **日曆共用授權**：
   - 將上述 3 本次日曆分別共用給 `picke-gcal-sync` 服務帳戶 Email，權限設為「進行變更並管理共用設定」。
5. **私密交付與環境變數配置**：
   - 取得 3 組 `...@group.calendar.google.com` 日曆 ID 與服務帳戶 JSON Key。
   - 將 JSON Key 轉為 Base64 寫入 Vercel 環境變數 `PICKE_GOOGLE_CREDENTIALS_B64`（**嚴禁寫入 repo 或任何公開設定檔**，並留意 `drive_credentials_b64_valueerror_postmortem.md` 所載之私鑰 `\n` 換行與 Base64 正規化踩坑）。

## 3. 工程端 4 項實作規格（啟動後施工清單）

1. **共用憑證載入器與真實 Calendar v3 Transport（`backend/app/modules/space/gcal_sync.py`）**：
   - 參考 `backend/app/services/drive_service.py:15-54` 之 B64／JSON／PATH 解析與私鑰 `\n` 正規化邏輯，抽取獨立於 `drive.readonly` scope 的共用憑證載入器。
   - 取代目前 `_custom_gcal_transport=None`、`LOCAL_ONLY` 模擬模式與 L171 偽標 `SYNCED`。
   - 補齊列表分頁（`pageToken`）與增量同步失效（HTTP `410 Gone`）全量重拉處理。
   - 修正 L252-294 改期後重複封鎖時誤查回已 `CANCELLED` 舊單的 bug。
2. **後台綁定 API 與前端同步狀態對齊（`admin_router.py` / `panels.tsx` / `PickeDailySchedulePage.tsx`）**：
   - 新增 `PATCH /api/picke/admin/skus/{sku_code}/gcal` 後端端點與 `VenuesPanel`（`frontend/src/pages/Picke/panels.tsx:1146-1182`）UI 綁定介面，將 3 個 SKU 對應到 3 組 `calendar_id`。
   - 修復 `panels.tsx:88-94` `GCAL_SYNC_STATUS` 小寫鍵名與後端回傳大寫 `SYNCED`／`LOCAL_ONLY`／`FAILED` 不匹配問題。
   - 修正 `frontend/src/pages/Picke/PickeDailySchedulePage.tsx:439-460` 同步按鈕，誠實顯示實際同步結果而非假成功提示。
3. **反向封鎖同步排程（`vercel.json` / `router.py`）**：
   - Phase 1 優先於 `vercel.json` 新增每 5–10 分鐘輪詢 Cron（免除 Google Calendar Push Webhook 每 7 天自動過期續期之維運成本）。
   - 保留 `backend/app/modules/space/router.py:806-845` `/webhooks/gcal` 端點相容性。
4. **安全與個資脫敏紅線（CRITICAL）**：
   - 移除 `gcal_sync.py:135-140` 將明文 6 碼門禁 `access_pin` 與 `storeasy_user_id` 寫入外部共用日曆 `summary`／`description` 的設計，改寫去識別化場地摘要，防止繞過軌道 A 脫敏稽核及外洩開門密碼。

## 4. 啟動條件

- 使用者明確通知「Workspace 帳號／3 組日曆 ID／服務帳戶 JSON Key 已備妥並完成 `PICKE_GOOGLE_CREDENTIALS_B64` 設定（或私密交付）」時，立即依第 3 節 4 項展開詳細計畫與實作驗證。
