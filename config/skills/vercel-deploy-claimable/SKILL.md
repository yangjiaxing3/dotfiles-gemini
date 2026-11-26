---
name: vercel-deploy-claimable
description: "''Use when packaging and deploying web projects to claimable Vercel preview URLs. Vercel免登入預覽部署與認領連結''"
---

# Vercel Claimable Preview Deployment

封裝前端或全端專案並一鍵上傳至可認領之 Vercel 預覽環境（子模組位於 `./vercel-deploy-claimable/`）。

## 核心步驟
1. 確認專案可正常編譯且排除 `node_modules` 與 `.git`。
2. 呼叫部署腳本取得 Preview URL 與 Claim URL 回報給使用者。


## ⚠️ Gotchas (避坑指南)
- **終端機輸出保護 (Context Overflow Prevention)**：執行腳本或查詢時，禁止直接將大筆 JSON/日誌印到 stdout；請導向暫存檔或加上筆數限制。
- **相對路徑與環境保護**：引用子目錄腳本或規則時保持既有目錄結構，不覆寫未授權之系統設定。
