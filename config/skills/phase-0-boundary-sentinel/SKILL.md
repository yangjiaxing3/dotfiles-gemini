---
name: phase-0-boundary-sentinel
description: "'Use when running phase-0-boundary-sentinel: Phase 0 零區守門：改檔、佈署或破壞性重構前強制檢查工作區邊界與部署 ID。Use before deploy, clasp push, or cross-f..."
---

# 零區安全協議 (Phase 0: Boundary Sentinel)

**觸發條件**：在執行任何檔案修改、佈署操作（如 `clasp push`, `npm run xxxx`），或發起任何破壞性重構任務前，強制無條件觸發此守則。

## 🛡️ Agent 0: 工作區守門員 (Boundary Sentinel)

### 1. 🔒 目錄越界鎖定 (Anti-Bleed Protocol)
- **規則**：絕對禁止跨出「該次對話約定之安全根目錄」進行程式碼修改或命令執行。
- **檢驗機制**：在執行修改或指令前，若發現 Active Document (當前焦點檔案) 不在已知的作用域專案內，即刻停止操作。
- **處置**：報錯並拒絕自動修改，嚴厲警告使用者「目前焦點已脫離安全作用域」。

### 2. 🔑 ID 來源孤立檢驗 (Deployment ID Isolation)
- **規則**：絕不透過歷史對話拼湊，或跨專案讀取未授權檔案來「猜測」部署網址及 ID。
- **檢驗機制**：針對 GAS 或 Vercel 等部署任務，部署指令發出前，強制執行 `cat .clasp.json` (或相對應配置檔) 進行實體讀取核對。
- **處置**：確認當下目錄的 config ID 是否完全等於使用者授權操作的 ID。如果不符，或配置檔不在安全作用域根目錄，立刻終止流程。

### 3. 🚦 意圖二次確認 (Explicit Intent Check)
- **規則**：在檢驗發現安全衝突時，不能自行修正邊界並「硬做」，必須將控制權交還。
- **處置**：停止當前所有 Pipeline (包含 Multi-Agent 流程)，輸出紅色的警戒訊息，要求使用者明確輸入授權文字或切換視窗回到安全區。

## ⚠️ Gotchas (避坑指南)
- **終端機輸出保護 (Context Overflow Prevention)**：執行腳本或查詢時，禁止直接將上百筆 JSON/日誌印到 stdout；請導向暫存檔或加上筆數限制。
- **零區防禦與 Port 禁令**：修改或執行指令前嚴守工作區邊界，嚴禁綁定或終止保留埠 (`8000`、`5100`、`3000`)。
