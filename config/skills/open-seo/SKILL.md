---
name: open-seo
description: "''Use when running self-hosted Open-SEO keyword tracking, SERP analytics, and Drizzle database workflows. 自託管Open-SEO關鍵字與SERP分析''"
---

# Open-SEO 關鍵字與搜尋分析套件

提供自託管之 SEO 關鍵字追蹤、SERP 排名監控與網站流量分析工作流。

## 核心步驟
1. 檢視 `src/` 與 `drizzle/` 下的資料表定義與分析管線。
2. 依任務需求調用對應之資料擷取與報表模組。


## ⚠️ Gotchas (避坑指南)
- **終端機輸出保護 (Context Overflow Prevention)**：執行腳本或查詢時，禁止直接將大筆 JSON/日誌印到 stdout；請導向暫存檔或加上筆數限制。
- **相對路徑與環境保護**：引用子目錄腳本或規則時保持既有目錄結構，不覆寫未授權之系統設定。
