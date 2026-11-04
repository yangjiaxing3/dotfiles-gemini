---
description: Lean-Triad 黃金三角工程工作流（AGENTS.md 確定性規範 + Graphify 圖譜導航 + Ponytail 極簡動刀 + Multi-Agent 角色×任務動態技能會審 + 強制執行回條）
---

// turbo-all

# Lean-Triad 黃金三角工程工作流 (`/lean-triad`)

本工作流將 **`AGENTS.md`（確定性規範）**、**`graphify`（全局結構導航）**、**`ponytail`（極簡減法動刀）** 與 **`multi-agent-mode`（角色 × 任務領域動態技能組合會審）** 封裝為可驗證的標準流水線，並強制在每次修改結尾輸出 **「🛡️ Lean-Triad 執行回條 (Execution Receipt)」**。

---

## 步驟 1：確定性規範讀取與「角色 × 任務領域」動態技能配置 (Role-Scoped Skill Binding)

1. **讀取專案單一真相來源**：確認當前專案 `AGENTS.md` / `CLAUDE.md` 之業務鐵律與測試指令，禁止盲目探索無關目錄。
2. **動態計算各 Agent 專屬技能包（而非整輪只用 1–2 個 Skill）**：
   執行確定性技能規劃器，依任務領域（`debug`、`data_analysis`、`ui_frontend`、`backend_api`、`seo_content`、`simplify_refactor`）為 `Agent 0 ~ E` 配置專屬技能組合（全流水線協同 8–12 個 Skills，但每個 Agent 僅載入與其職責及當輪任務匹配的 3–5 個 Skills，並略過無關的重型 MCP）：
   ```powershell
   C:\Users\Jiaxing\Documents\GitHub\StoreasyFMnew\backend\.venv\Scripts\python.exe C:\Users\Jiaxing\.gemini\scripts\multi_model_gate.py plan-skills --prompt "<使用者任務描述>"
   ```

| 角色代號与對外模型 | 角色常駐基底技能 | 隨任務領域動態切換之專屬技能（範例） |
| :--- | :--- | :--- |
| **🛡️ Agent 0 (`deepseek-flash`)** | `accidental-data-loss-prevention`, `stage-gate-review` | `debug`: `fixer-prompt`, `agent-tester`<br/>`backend_api`: `security-audit`, `agency-testing-api-tester` |
| **🧠 Agent A (`gemini-4-argon`)** | `graphify`, `ponytail-audit` | `data_analysis`: `agency-data-consolidation-agent`, `storeasy-mini-warehouse-viz`, `d3-data-visualization`<br/>`ui_frontend`: `impeccable`, `frontend-design` |
| **😈 Agent B (`grok-4.7` 紅隊)** | `ponytail-review`, `agency-engineering-code-reviewer` | **`debug`**: `fixer-prompt`, `agent-code-analyzer`, `agent-performance-optimizer`<br/>**`data_analysis`**: `agency-support-analytics-reporter`, `ml-best-practices`, `xlsx`<br/>**`ui_frontend`**: `web-design-guidelines`, `agency-testing-accessibility-auditor`, `design-taste-frontend`<br/>**`backend_api`**: `security-audit`, `agency-testing-api-tester`, `agency-engineering-database-optimizer` |
| **⚖️ Agent C & 🛠️ Agent D (`qwen-3.8-max`)** | `ponytail`, `decisions-governance` | `debug`: `fixer-prompt`, `tdd-workflow`<br/>`data_analysis`: `xlsx`, `building-data-apps`<br/>`ui_frontend`: `impeccable`, `emil-design-eng` |

---

## 步驟 2：`graphify` 結構導航與爆炸半徑鎖定

1. **動刀前查圖譜**：若專案存在 `graphify-out/graph.json` 或 `graphify-out/GRAPH_REPORT.md`，優先查詢核心節點與上下游呼叫鏈：
   ```powershell
   C:\Users\Jiaxing\Documents\GitHub\StoreasyFMnew\backend\.venv\Scripts\python.exe -m graphify query "<修改目標或概念>"
   ```
2. **動刀後同步圖譜**：修改程式碼後，執行 AST 無損快速更新（零 API 成本）：
   ```powershell
   C:\Users\Jiaxing\Documents\GitHub\StoreasyFMnew\backend\.venv\Scripts\python.exe -m graphify update .
   ```

---

## 步驟 3：`ponytail` 極簡外科手術動刀

1. **最小完整變更**：優先刪除重複按鈕、無用 Wrapper 與死碼；絕不觸碰受保護業務公式（3D 幾何、計價稅額公式、`HASH_KEYS` SHA-256 雜湊鏈、只作廢不刪除）。
2. **統計淨增減行數**：執行 `git diff --shortstat` 取得實際 `+新增 / -刪除` 行數。

---

## 步驟 4：分級異質多模型會審與真實終端機測試

1. **小改動（`< 15` 行、純樣式微調或文案修正）**：直接執行專案單元測試（`pytest` / `vitest` / `tsc`）。
2. **中大型改動（刪減 `> 15` 行、移除抽象層、跨模組重構、觸及核心業務/API）**：
   強制執行 `multi_model_gate.py review`，腳本會自動將各角色綁定的 `SKILL.md` 避坑指南、`AGENTS.md` 鐵律與 `graphify` 核心節點注入對外 5 大異質模型：
   ```powershell
   C:\Users\Jiaxing\Documents\GitHub\StoreasyFMnew\backend\.venv\Scripts\python.exe C:\Users\Jiaxing\.gemini\scripts\multi_model_gate.py review --prompt "<變更摘要>" --git-diff --output temp_multi_review.json
   ```

---

## 步驟 5：強制輸出「🛡️ Lean-Triad 執行回條 (Execution Receipt)」

每次程式碼修改回覆的最末端，**必須**附上以下 5 行回條供使用者驗收：

```markdown
---
### 🛡️ Lean-Triad 執行回條 (Execution Receipt)
- **🧰 Role-Scoped Skills (角色×任務技能組合)**：`<列出本輪任務領域與各 Agent 掛載之專屬 Skills>`
- **🧭 Graphify 圖譜導航**：`<動刀前檢索之節點 / 動刀後 graphify update 狀態>`
- **✂️ Ponytail 精簡度**：`+<新增行數> / -<刪除行數> 行（淨增減）｜shortcut: <無或註記>`
- **⚖️ 分級會審與測試門禁**：`<快改免會審 或 multi_model_gate.py (models ok, score, verdict) + pytest/vitest 結果>`
- **⚠️ 略過項目與邊界風險**：`<1-2 行列出刻意略過未做的項目與需注意的邊界風險>`
```
