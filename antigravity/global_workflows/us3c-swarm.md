---
description: US3C 專案
---

# US3C 專案：Ruflo Swarm 技能掛載與冷熱庫協作工作流 (/us3c-swarm)

本工作流引導並調度位於 `C:\Users\Jiaxing\.gemini\antigravity\skills` 的 28 個 Active Skills (Hot Library)，在 US3C Next.js 重構專案中執行多 Agent 重複檢測、網頁 Premium 設計系統一致性校驗、以及二手 3C 深度價值分析內容自動化寫作發布流水線。

---

## ⚡ 工作流調用與執行指南

在 Antigravity 開發環境中，您可以隨時引用此工作流，或要求 Agent 執行以下指令以發動指定的 Swarm 協同任務。

---

## 🚀 步驟 1：啟動 AEO / SEO 多 Agent 重複檢測與質詢 (aeo-audit)

啟動 `Technical-Auditor`、`On-Page-Auditor` 與 `Schema-Validator` 三方 Agent，調用 `technical-seo-checker` + `on-page-seo-auditor` + `schema-markup-generator` 技能，在共享熱快取中反覆質詢，確保 SSR 路由、動態 Schema 與 Canonical 100% 正確，零 Cloaking 風險。

// turbo
```powershell
node scripts/ruflo-swarm-bridge.mjs --workflow aeo-audit
```

---

## 🎨 步驟 2：啟動網頁 Premium Design 視覺與微動畫 Token 校審 (design-verify)

調用 HSL Emerald 600（微動畫）與 slate 900 設計 Token 快取，校審 MacBook Pro / iPad 報價 Table UX，徹底去除 Placeholder 及「加碼價」垃圾欄位，維持極致的 Wow-effect 視覺。

// turbo
```powershell
node scripts/ruflo-swarm-bridge.mjs --workflow design-verify
```

---

## 🤖 步驟 3：發動二手 3C 機型功能與深度價值分析 Content 自動化流程 (content-auto)

調用 `keyword-research` (挖詞) ➔ `entity-optimizer` (撈 Specs) ➔ `geo-content-optimizer` (AEO 模板) ➔ `seo-content-writer`，實時生成包含 `cleanHtmlForSchema` 實體超連結、無 Cloaking 隱患的高質量分析文章，通過 Agent 重審後自動發布！

> [!NOTE]
> 請在執行時將 `<ModelName>` 替換為實際欲生成的機型名稱（例如："iPhone 17 Pro Max" 或 "Macbook Pro M4 Max"）。

// turbo
```powershell
node scripts/ruflo-swarm-bridge.mjs --workflow content-auto --model "<ModelName>"
```
