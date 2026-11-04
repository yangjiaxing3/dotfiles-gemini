---
name: us3c-imcheck-device-qc
description: "'Use when handling iMCheck phone diagnostics, Securaze erasure, arrival QC grading, or /blacklist admin APIs. 二手手機驗機質檢與iMCheck黑名單'"
---

# iMCheck 二手手機硬體檢測、到貨驗收質檢 (QC) 與黑名單治理

本技能規範 US3C 家族中 `iMCheck`（`www.imcheck.com.tw`）、`us3c-next`（商品主檔、到貨驗收 QC、`/blacklist` 黑名單管理）與 `usdwarrantynew`（保固與檢測）的跨系統契約與業務邊界。

## 1. 到貨驗收質檢 (QC) 與 5 級庫位平帳

1. **商品與驗機閉環 (Phase 2 S2/S3/S4)**：
   - 每台回收設備入庫須經過 IMEI / 序號唯一性校驗、Securaze 資料抹除憑證核對、iMCheck 硬體功能檢測與外觀分級，始得寫入庫存並分配 5 級庫位（倉/區/架/層/籃）。
   - 任何庫存異動與盤點平帳必須留存不可竄改之異動日誌。

## 2. 黑名單跨庫治理 (`/blacklist` ↔ `iMCheck` Neon DB)

1. **架構與代理通道**：
   - `us3c-next` 的 `/blacklist` 頁面讀寫的是 `www.imcheck.com.tw` 的 **Neon PostgreSQL** 資料表，而非 US3C 本身的 Supabase 表。
   - 正式環境經由 Supabase Edge Function `imcheck-blacklist` (`supabase.functions.invoke`) 轉發；本機開發經由 Vite Proxy `/__imcheck/blacklist` (`vite-plugin-imcheck-blacklist.ts`)。
2. **權限與 HTTP 方法邊界**：
   - 權限強制要求 `rbac:read`，**僅接線 Admin 管理端路由**，嚴禁在後台開放公開 search / report / check / intercept。
   - **案件欄位更新**（不含 `status` / `email`）一律使用 `PATCH`（設備更新可含 `imageUrls`）；**案件狀態變更**維持使用 `POST`。
   - 若修改 `iMCheck` 倉庫（根目錄 `official_website`），需確認 Vercel 正式環境已部署，避免線上 `PATCH` 回傳 `405`。

## 3. US3C 家族三站 SEO 關鍵字防競食法典 (Anti-Cannibalization)

撰寫或審計 `iMCheck`、`US3C`、`7-11 專站` 的頁面與 FAQ 時，嚴格遵守三站語意分工：
- **`imcheck.com.tw`**：獨佔泛詞（`手機回收`、`二手手機回收`、`手機回收機`、`24H手機回收機`、`手機線上估價`、`手機回收估價`）與智慧機台據點頁。
- **`us3c.com.tw`**：專攻品牌與機型長尾詞（如 `iPhone 16 回收`、`MacBook 回收價格`）與實體門市據點詞。
- **`711us3cwebsite`**：僅限超商寄件回收相關詞（如 `7-11手機回收`）。

## ⚠️ Gotchas (避坑指南)
- **禁止混用資料庫連線**：黑名單資料在 iMCheck Neon DB，商品與機台資料在 US3C Supabase，切勿在 Supabase Migration 中誤建黑名單表。
- **終端機輸出保護 (Context Overflow Prevention)**：查詢驗機報告或黑名單列表時，強制加上分頁或筆數限制。
- **零區防禦與 Port 禁令**：修改跨倉庫 API 時優先對齊 `us3c-next` 與 `iMCheck` 契約，嚴禁綁定保留埠 (`8000`、`5100`、`3000`)。
