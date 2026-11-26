---
id: mem-us3c-store-locations-supabase-ssot
brand: us3c
tier: L2_CONTRACT
status: active
valid_from: "2026-11-18"
scope_repos: [us3c-next, us3cwebsite-env]
---

# [Correct-Pattern] US3C 直營分店資訊 SSOT：Live Supabase × 專案程式碼

## 📌 Context

- 確立日：2026-11-18
- 適用專案：`us3cwebsite-env`（`us3c-next-poc`）
- 唯一真相來源（Only Source of Truth）：
  1. **Live Supabase**：專案 `<SUPABASE_PROJECT_REF>` 資料表 `published_kiosk_snapshot`（`payload->>kind` 為 `null` 之最新一筆 `payload.stores`）提供即時門市營運欄位（`storeCode`、`name`、`address`、`note`、`phone`、`hoursByDay`、`status`、`lineId`、`googleMapUrl`、`youtubeUrl`、`metro`、`parking`）。
  2. **專案程式碼**：[`us3c-next-poc/src/data/locations.ts`](file:///c:/Users/Jiaxing/Documents/GitHub/us3cwebsite-env/us3c-next-poc/src/data/locations.ts) 保存站點結構性權威欄位（`id`、SEO Canonical `slug`、`lat`/`lng` 防呆基準、`features`、`serviceAreas`、`heroImage`／`galleryImages`、`STORE_LINE_URL_BY_ID` 權威短鏈對照表）。

---

## ❌ [Anti-Pattern 錯誤模式]

1. 仍自舊 Google Sheet（`GID: 995828836`）拉取門市資料覆蓋官網，導致營業時間與現場實際調度脫節。
2. 在 [`store-status.ts`](file:///c:/Users/Jiaxing/Documents/GitHub/us3cwebsite-env/us3c-next-poc/src/utils/store-status.ts) 或頁面對特定分店硬寫例外公休日（例如誤將台北南港旗艦店寫死週六公休），違反 Live Supabase `hoursByDay`（週一至週六 12:00-20:00）。
3. 新設或異動分店直接填寫總部 LINE@（`@us3c` / `https://lin.ee/V5HSH5g`）而非區店專屬帳號（如中和威力店實際為新北區 `@us3ctb` / `https://lin.ee/WBvSBwf`）。
4. 未檢查座標防呆即直接覆寫經緯度（例如 Snapshot #134 中台南安平店 `lat` 誤載高雄緯度 `22.6335161`，須保留 `22.9888192`）。

---

## ✅ [Correct-Pattern 正確作法]

1. 所有直營分店異動一律執行 `npm --prefix us3c-next-poc run stores:sync`（實作於 [`scripts/sync-direct-stores-from-sheet.mjs`](file:///c:/Users/Jiaxing/Documents/GitHub/us3cwebsite-env/scripts/sync-direct-stores-from-sheet.mjs)）自 Live Supabase `published_kiosk_snapshot` 拉取最新 `payload.stores` 同步至 `locations.ts`。
2. `lineUrl` 統一透過 `STORE_LINE_URL_BY_ID` 嚴格校驗，確保 `lineId` 與短網址一一對應。
3. 所有前台展示（`AppleArchiveClient.tsx`、`location/page.tsx`、`location/[slug]/page.tsx` 等）禁止手寫硬編碼分店清單，統一從 `STORE_LOCATIONS` 讀取，並搭配雙視窗 `/e2e`（`npm --prefix us3c-next-poc run test:e2e`）驗證。

### 全台 8 間直營分店權威對照表

| `storeCode` | `id` | Canonical `slug` | `lineId` | `lineUrl` |
| :--- | :--- | :--- | :--- | :--- |
| `US3C-NANMEN` | `taipei-nanmen` | `price-and-location-taipei` | `@us3ctp` | `https://lin.ee/scVcrlht` |
| `US3C-NANGANG` | `taipei-nangang` | `location-nangang-store` | `@us3cts` | `https://lin.ee/QsoWVQp` |
| `US3C-BANQIAO` | `new-taipei-banqiao` | `price-and-location-banqiao` | `@us3ctb` | `https://lin.ee/WBvSBwf` |
| `US3C-ZHONGHE` | `new-taipei-zhonghe` | `location-zhonghe-power-store` | `@us3ctb` | `https://lin.ee/WBvSBwf` |
| `US3C-CHUNRI` | `taoyuan-chunri` | `taoyuan-store` | `@us3cty` | `https://lin.ee/y7MPoTl` |
| `US3C-WENXIN` | `taichung-wenxin` | `qinghai-store` | `@us3ctc` | `https://lin.ee/uCr7LWD` |
| `US3C-ANPING` | `tainan-anping` | `tainan-anping-store` | `@us3cap` | `https://lin.ee/t1Q3B0hm` |
| `US3C-FUXING` | `kaohsiung-fuxing` | `price-and-location-kaohsiung` | `@us3ckh` | `https://lin.ee/8ynpP2W` |
