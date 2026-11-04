---
name: decisions-governance
description: "''Use when recording, reading, superseding, or auditing architectural decisions in DECISIONS.md and docs/decisions. 架構決策紀錄ADR與防..."
---

# 漸進式架構決策治理 (Progressive DECISIONS.md Governance)

結合 `graphify`（結構圖譜）、`README.md`（系統導覽）與 `DECISIONS.md`（決策索引），以零成本、跨 AI 工具（Antigravity、Cursor、Claude、Codex）通用的方式記錄「**為什麼這樣改**」，同時防止單一檔案淪為臃腫流水帳。

## 核心三原則 (Three Golden Rules)

1. **一個決策一個小檔（漸進式載入）**：
   - 根目錄 [`DECISIONS.md`](DECISIONS.md) **只當目錄**，一行一條，標註狀態：`有效` 或 `被 NNNN 取代`。
   - AI 進場時先讀 `DECISIONS.md` 目錄，**只遵守狀態為「有效」的條目**；當任務觸及該領域時，才按需打開 `docs/decisions/NNNN-slug.md`。
   - 每份 `docs/decisions/NNNN-slug.md` 嚴格控制在 **10～20 行**（僅寫：**背景、決定、理由**）。
2. **只記重要的決定（高訊噪比）**：
   - **要記**：以後很難改回來、跨專案邊界、或「光看程式碼看不出原因」的決定（例如：預覽站連正式庫但禁寫、某張事實表官網禁直讀、禁止引入某框架）。
   - **不記**：日常重構、欄位微調、一般 Bug 修復（這些寫在 PR 說明與 Git commit 即可）。
3. **作廢就標出來（保留歷史但不干擾 AI）**：
   - 當舊決定被推翻時，**不刪檔**；新增一份新編號決策檔（如 `0012-xxx.md`），並將 `DECISIONS.md` 與舊檔中的狀態改為 `被 0012 取代`。

## 標準操作流程 (Workflows)

### A. 新增一條重要決策
1. 檢視目標專案的 `DECISIONS.md` 取得下一個四位數編號 `NNNN`。
2. 參考 `docs/decisions/0000-template.md`，建立 `docs/decisions/NNNN-kebab-title.md`（控制在 10～20 行）。
3. 在 `DECISIONS.md` 表格新增一行，狀態設為 `**有效**`。
4. 若此決策取代了舊決策 `MMMM`，將 `DECISIONS.md` 中 `MMMM` 的狀態改為 `被 NNNN 取代`，並同步更新 `docs/decisions/MMMM-*.md` 的狀態列。

### B. 定期防臃腫與一致性巡檢（每月排程或手動執行）
執行確定性巡檢腳本，檢查 Storeasy 聯動家族各專案的 `DECISIONS.md` 有效條目數、小檔行數上限、斷鏈與到期複查事項（如 2026-11-21 複查外部記憶工具 Windows 支援與 Issue `#120`）：

```powershell
& "C:\Users\Jiaxing\AppData\Local\Python\bin\python.exe" C:\Users\Jiaxing\.gemini\config\skills\decisions-governance\scripts\audit_decisions.py
```

## ⚠️ Gotchas (避坑指南)
- **禁止把 `DECISIONS.md` 寫成詳情流水帳**：任何超過 1 行的背景或程式碼細節，一律放進 `docs/decisions/NNNN-*.md`，目錄表每列保持單行摘要。
- **禁止遵守已取代決策**：AI 讀取 `DECISIONS.md` 時，凡標註 `被 NNNN 取代` 或 `已取代` 之條目一律跳過，不得作為現行開發規則。
- **終端機輸出保護 (Context Overflow Prevention)**：執行巡檢腳本時維持精簡 JSON 輸出，禁止傾印全部檔案內文至 stdout。
