---
name: ai-seo
description: "'''Use when tasks involve ai seo: ai-seo'''"
---

# AI SEO Optimization Skill

這是一個專門用於優化網頁搜尋引擎排名的技能。

## 核心準則

1.  **技術性 SEO (Technical SEO)**:
    - 確保頁面具備正確的 `canonical` 標籤。
    - 檢查 `robots.txt` 與 `sitemap.xml` 的完整性。
    - 優化 Web Vitals（如 LCP, FID, CLS）。
2.  **內容與關鍵字 (Content & Keywords)**:
    - 標題 (Title) 與 描述 (Meta Description) 必須包含核心關鍵字。
    - 確保 `h1` 標籤唯一且具備描述性。
    - 圖片必須具備語意化的 `alt` 屬性。
3.  **結構化數據 (Structured Data)**:
    - 為 FAQ、組織、軟體服務提供 JSON-LD 標記。
    - 優先使用 `Organization` 與 `WebSite` 標記。

## 執行流程

1.  **掃描**: 檢查當前頁面的元數據與標籤。
2.  **診斷**: 找出缺少的 SEO 元素或不佳的內容。
3.  **優化**: 提出具體的內容修改建議。
4.  **驗證**: 使用模擬爬蟲或檢查工具確認修改。

## ⚠️ Gotchas (避坑指南)
- **避免關鍵字堆砌與門頁懲罰 (Doorway Pages)**：多據點或多機型頁面必須結合在地真實數據（如實收租金、分店地標、真實檢測數據），禁止僅替換地名或機型名稱。
- **Schema 與畫面一致性**：產出的 JSON-LD (`FAQPage`, `LocalBusiness`, `Product`) 內容必須與頁面可見文字 100% 一致，否則會觸發 Google 結構化資料人工處罰。
