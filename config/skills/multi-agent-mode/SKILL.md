---
name: multi-agent-mode
description: "Use when tasks need phase-scoped Neon/Carbon planning, C1/C2 Hydrogen execution & Grok/Decision review. 多Agent動態啟停/紅隊辯證"
---

# 多 Agent 模式（Phase-Scoped 動態啟停：Model × Skills × 元件）

原則：**拒絕靜態高佔用常駐底座（只啟動、不釋放），改按階段（Phase）動態啟動最適合的 Model、Skills 與確定性元件，交棒即釋放**。先由 Phase A 唯讀探索定計並訂 **Re-plan Triggers**，再切進 `C1 Build → C2 Verify` 兩段執行，遇阻交回 Phase A 修補。切換角色標示：`### 🤖 Agent [X]（[模型]）：[角色]`。全程繁體中文。

## 六階段動態啟停流程（Plan ⇄ Execute ⇄ Re-plan Loop）

| Phase | 角色 | 主力模型 | 動態啟動 Skills 與元件 *(交棒即釋放)* | 停止 / 交回條件 |
| :--- | :--- | :--- | :--- | :--- |
| **0** | 🛡️ 邊界與脫敏探勘 | `deepseek-flash` | **Skills**：`boundary-sentinel`, `accidental-data-loss-prevention`, 按需 `bughunter`/`hunt-*`<br/>**元件**：`xlsx_ingest_profiler.py --mask-pii`, `check_sensitive_paths.py` | 越界／未授權／敏感外送 → 停手請求授權 |
| **A** | 🧠 唯讀定計與契約 | `gemini-4-neon-xhigh` *(輕量選 `carbon-high`)* | **Skills**：`graphify`, 領域架構/對帳/圖表設計（含 `spreadsheet-reconciliation`）<br/>**元件**：`graphify query/path`, `DECISIONS.md` 索引, `Re-plan Triggers` | 計畫與契約完成 → 進 B 或 C1 *(釋放探索工具)* |
| **B** | 😈 紅隊 ＋ 裁判 *(門禁)* | `grok-4.7` ＋ `Decision API` (`jev`/Gemini; 備援 `qwen4-max`) | **Skills**：`ponytail-review`, `bughunter`, 領域稽核（如 `spreadsheet-reconciliation`, `xlsx`）<br/>**元件**：靜態缺陷掃描、Claude-BugHunter Vault、`Decision API` 燈號 | 非 🔴 → C1；🔴 → 回 A 修補 *(釋放紅隊上下文)* |
| **C1** | 🛠️ 實作建構 *(Build)* | `gemini-4-hydrogen-xhigh` *(硬骨頭升 `qwen4-max`)* | **Skills**：**4 槽滿配領域實作技能**（如 `xlsx`、`fastapi-templates`、`spreadsheet-reconciliation`；僅觸及安全面時掛 1 槽 `security-audit`，**0 測試佔槽**）<br/>**元件**：`recalc.py`, `formula_engine_hub.py`, `hyperformula_eval.js` | 觸發 Re-plan Trigger → 回 A；寫碼完成 → C2 *(釋放 Build)* |
| **C2** | 🧪 驗證測試 *(Verify)* | `gemini-4-hydrogen-xhigh` | **Skills**：`tdd-workflow`, `agent-tester`, `verification-quality`, `api-tester`/`agent-desktop`<br/>**元件**：`pytest`, `tsc`, `vitest`, `rule_lint.py --git-diff` | 同錯連敗 2 次 → 回 A；全綠 → D *(釋放測試)* |
| **D** | 🔍 終審與白話交付 | `qwen4-max` *(備 `deepseek-flash`)* ＋ `Decision API` | **Skills**：`ponytail-review`, `eli5`, `verification-quality` ＋ 領域終審<br/>**元件**：`multi_model_gate.py review`, `graphify update .`, `SESSION-HANDOFF.md` | PASS → 輸出 `/eli5` 結案報告；FAIL → 回 A/C1 |

## Re-plan Triggers（執行層必須停手交回 Phase A 的條件）
1. **隱藏依賴浮現**：發現計畫外跨模組契約衝突或須改動未授權檔案。
2. **環境／套件假設失效**：編譯、依賴或外部 API 與探索假設不符。
3. **同錯連敗 2 次**：同一錯誤連續失敗 **2 次**（交回 Phase A 重設計；必要時升派 `qwen4-max`）。
4. **逼近受保護禁區**：可能改寫 3D 幾何、財務計價公式、只作廢不刪除或 PII 防護。

## ⚠️ Gotchas (避坑指南)
- **不可再把 `C1` 與 `C2` 混在同一回合佔滿基地台**：`C1` 專注結構與邏輯實作（免背 `tdd-workflow`），完成後切換 `C2` 載入測試矩陣驗證，確保每階段都用滿最適合的工具組。
- **禁止靜態猜難度與單票假綠燈**：門禁腳本採「一模型一票」統計，多數 `🔴` 或紅隊逾時即 `BLOCK`；可用 `python scripts/multi_model_gate.py plan-skills --phase <0|A|B|C1|C2|D> --prompt "..."` 檢視各階段啟動／釋放清單。
- **模型路由鐵律 (`multi_model_gate.py`)**：Grok 走 Cursor Plan 或 `grok.exe` Plan；Gemini 優先 `agy.exe --mode plan`；Qwen MaaS `sk-sp-...` 鎖定 `token-plan.maas`，直連失敗後才走 OpenRouter。
