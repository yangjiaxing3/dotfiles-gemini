---
name: us3c-swarm
description: "'US3C Ruflo Swarm 技能掛載與冷熱庫協作。Use when the user says /us3c-swarm or wants the US3C swarm pipeline.'"
---

# US3C 專案：Ruflo Swarm 技能掛載與冷熱庫協作工作流 (/us3c-swarm)

本工作流引導並調度位於 `C:\Users\Jiaxing\.gemini\antigravity-ide\skills` 的 28 個 Active Skills (Hot Library)，在 US3C Next.js 重構專案中執行多 Agent 重複檢測、網頁 Premium 設計系統一致性校驗、以及二手 3C 深度價值分析內容自動化寫作發布流水線。

需要換模型時只准 Ruflo Swarm V3 五家，通道與停損條件以 `multi-agent-mode` 為準：`deepseek-flash`（`DEEPSEEK_API_KEY`）、`qwen-3.8-max`（`QWEN_API_KEY`，北京 QwenCloud，model `qwen3.8-max`）、`gemini-4-carbon`（`GEMINI_API_KEY`，`models/gemini-4-carbon`）、`grok-4.7`（Cursor 方案裡的 Grok，不要讀 `XAI_API_KEY`）、TypeSafe `jev-1.13.0`（變數名 `TYPESAFE_API_KEY`，評分器，不當聊天模型）。下面的橋接腳本負責工作流，不另外指定第六個模型。

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

## ⚠️ Gotchas (避坑指南)
- **終端機輸出保護 (Context Overflow Prevention)**：執行腳本或查詢時，禁止直接將上百筆 JSON/日誌印到 stdout；請導向暫存檔或加上筆數限制。
- **零區防禦與 Port 禁令**：修改或執行指令前嚴守工作區邊界，嚴禁綁定或終止保留埠 (`8000`、`5100`、`3000`)。
