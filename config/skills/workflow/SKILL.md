---
name: seo-workflow-rules
description: "''Use when checking shared SEO workflow rules, CORE-EEAT rubrics, and audit gates in workflow/rules. SEO工作流規則與EEAT審計門禁''"
---

# SEO 共用工作流規則庫 (Workflow Rules)

存放跨技能共用之 SEO 審查準則與驗證門禁（位於 `./rules/` 目錄下，供各 SEO 技能按需引用）。

## 核心步驟
1. 執行內容或技術 SEO 審計時，按需讀取 `./rules/` 下對應之規範檔。
2. 嚴格保留 `./rules/` 目錄結構以確保跨技能相對路徑引用正常。


## ⚠️ Gotchas (避坑指南)
- **終端機輸出保護 (Context Overflow Prevention)**：執行腳本或查詢時，禁止直接將大筆 JSON/日誌印到 stdout；請導向暫存檔或加上筆數限制。
- **相對路徑與環境保護**：引用子目錄腳本或規則時保持既有目錄結構，不覆寫未授權之系統設定。
