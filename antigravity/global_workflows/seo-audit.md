---
description: 執行完整的 SEO 審查工作流，確保頁面符最佳實踐。
---

# SEO 審查工作流 (SEO Audit Workflow)

本工作流旨在規範專案的 SEO 檢查程序，提升搜尋引擎友善度。

## 執行步驟

### 1. 基礎標籤檢查 (Basic Meta Tags)
- [ ] 檢查 `<title>` 是否具備主要關鍵字且長度適中（50-60 字元）。
- [ ] 檢查 `<meta name="description">` 是否吸引人且包含關鍵字。
- [ ] 確保具備 `<link rel="canonical">` 標籤以防止重複內容。

### 2. 結構化數據驗證 (Structured Data Verification)
- [ ] 驗證 `Organization` 標記是否包含完整的聯絡資訊與 Logo。
- [ ] 檢查是否有 `FAQPage` 標記（若頁面有 FAQ 區塊）。
- [ ] 確保 `WebSite` 標記已正確配置。

### 3. 內容語意化檢查 (Content Semantics)
- [ ] 檢查 `h1` 標籤是否唯一且為頁面核心標題。
- [ ] 確保 `h2-h6` 結構邏輯層次分明。
- [ ] **強制**：所有 `<img>` 標籤必須具備描述性的 `alt` 屬性。

### 4. 外部文件檢查 (External Files)
- [ ] 驗證 `/robots.txt` 是否存在並正確指向 Sitemap。
- [ ] 檢查 `/sitemap.xml` 是否包含所有活躍頁面且更新日期正確。

### 5. 效能與最佳實踐 (Performance & Best Practices)
- [ ] 核心網站指標 (Core Web Vitals) 是否達標？
- [ ] 是否針對非首屏圖片使用 `loading="lazy"`？
