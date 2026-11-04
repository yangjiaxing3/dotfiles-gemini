---
name: storeasy-location-migration
description: "'舊站門市資料遷移、爬蟲與 SEO 重寫。Use when migrating Storeasy / store location pages.'"
---

# 門市資料庫遷移與 SEO 自動化工作流 (Store Location Migration & SEO Workflow)

本工作流規範了如何將舊網站的門市網頁資訊，經過多重爬蟲 (定價、圖片、全文)、大語言模型 (LLM) 改寫，最終以 SEO 優化的結構呈現於前端的標準程序。包含了 Google Sheets 營運資料的同步機制。

## 階段一：營運資料基礎同步 (Google Sheets Sync)
**執行腳本**：`scripts/sync_new_locations.ts`
1. **驗證憑證**：讀取 `.env.local` 中的 `GOOGLE_CLIENT_EMAIL` 與 `GOOGLE_PRIVATE_KEY` 進行服務帳號驗證。
2. **獲取資料**：存取指定的 Google Sheet (`1EFxL8vERajrjxBfc66xRqYSPjhhYwmW5KdoKgcjqZk0`) 獲取最新的門市名稱、地址、電話、經緯度與營業狀態。
3. **資料清洗**：過濾掉特定的隱藏名單 (HideList)，並補齊預設屬性 (如：`category`, `status`)。
4. **輸出結果**：將整理後的陣列寫入至 `src/data/locations.json` 做為門市的基礎 Metadata。

## 階段二：原始網址的動態資料爬取 (Prices & Images Scraping)
**執行腳本**：`scripts/scrape_all_prices.py` / `scripts/scrape_store_prices.py`
> **資料來源：門市舊版原始網址** (如：`https://www.storeasy.com.tw/store/...`)
1. **讀取網址對應表**：從 `locations_temp.csv` 讀取每家門市的 `slug` 與對應的原始網站 URL。
2. **定價與圖片爬蟲**：利用 BeautifulSoup (bs4) 針對原始網頁的 DOM 結構進行解析：
   - 提取上下層倉位的詳細尺寸與價格表 (`monthly`, `yearly`, `boxCount`)。
   - 抓取網頁中所有的門市實景照片連結 (`image_urls`)，讓新站直接引用舊站圖床，不需重新上傳。
3. **更新資料庫**：將爬取到的定價與照片直接寫入並更新 `src/data/locations.json` 的對應門市中。

## 階段三：舊網站文案爬取與轉換 (Web Scraping to Markdown)
**執行腳本**：`scripts/urls_to_markdown.py`
> **資料來源：門市舊版原始網址**
1. **MarkItDown 轉換**：利用 Microsoft 的 `markitdown` 工具，實際存取原始網頁，將 HTML 完美轉換為乾淨的 Markdown 格式（保留表格、圖片連結、清單）。
2. **儲存備份**：將解析後的檔案儲存至 `src/data/markdown_exports/{slug}.md` 作為 LLM 的上下文知識庫。

## 階段四：AI 驅動的 SEO 內容重構 (SEO Content Generation)
**執行腳本**：`scripts/generate_seo_content.py`
1. **啟動 Gemini 引擎**：使用 `google-genai` SDK 呼叫 Gemini 3.5 Flash 模型。
2. **專家角色賦能**：套用 `agency-marketing-seo-specialist` 與 `seo-content-writer` 的系統提示詞 (System Prompt)，要求模型依據階段三產生的 Markdown 執行：
   - **在地化 SEO 介紹 (`seo_intro`)**：融入城市、行政區與周邊地標。
   - **核心特點 (`core_features`)**：提煉舊網頁中最吸引人的 3 大賣點。
   - **FAQ 分類結構 (`faq_categories`)**：整理承租規則、環境設備等常見問答。
   - **Meta Tags**：自動生成長度符合規範且具備轉換率的 Meta Title 與 Description。
3. **陣列結構化儲存**：將模型輸出的 JSON 格式解析後，比對 `slug` 以**陣列 (Array)** 的形式**增量寫入**至 `src/data/locations_content.json`，跳過已生成的門市以節省 Token。同時將 Meta Tags 更新回 `locations.json`。

## 階段五：前端動態渲染與 Schema 注入 (Frontend Integration)
**前端元件**：`src/app/locations/[slug]/page.tsx`
1. **資料聚合**：於 Server Component 動態讀取 `locations.json` (基本營運資料、照片、價格) 與 `locations_content.json` (SEO 文案)。
2. **在地化補充**：如遇到無 AI 文案的門市，透過 `generateGeoText` 啟動 Fallback 預設文案。
3. **UI 佈局更新**：
   - 將「地址」與「專屬備註 (如：入口於萊爾富超商後方)」綁定顯示。
   - 重構「參觀與進出時間」區塊，明確區分預約時段與 24H 進出權限。
   - 結合階段二抓取的定價資料動態生成 `StoreSizeEstimator` 3D估算器。
4. **JSON-LD Schema 注入**：
   - 生成符合 Google 規範的 `SelfStorage` LocalBusiness Schema。
   - 提取 `faq_categories` 自動建立 `FAQPage` Schema 以爭取 PAA (People Also Ask) 曝光。
   - 建立 `BreadcrumbList` Schema 強化網站層級關係。

## ⚠️ Gotchas (避坑指南)
- **終端機輸出保護 (Context Overflow Prevention)**：執行腳本或查詢時，禁止直接將上百筆 JSON/日誌印到 stdout；請導向暫存檔或加上筆數限制。
- **零區防禦與 Port 禁令**：修改或執行指令前嚴守工作區邊界，嚴禁綁定或終止保留埠 (`8000`、`5100`、`3000`)。
