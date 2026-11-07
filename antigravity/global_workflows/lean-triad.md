---
description: Lean-Triad 黃金三角工程工作流（AGENTS.md 確定性規範 + Graphify 知識圖譜導航 + Ponytail 極簡減法與 Role-Scoped 技能路由 + 強制執行回條）
---

# 🛡️ Lean-Triad 黃金三角工程工作流

本工作流將 **`AGENTS.md`（單一真相源）**、**`graphify`（知識圖譜導航）**、**`ponytail`（極簡減法）** 與 **`Role-Scoped × Task-Aware Skill Binding`（角色×任務動態技能綁定）** 整合為每次開發任務的標準閉環，並在回覆結尾強制輸出 **「🛡️ Lean-Triad 極簡執行回條」**。

---

## 步驟 1：讀取 `AGENTS.md` 與啟動「角色 × 任務領域」動態技能綁定

1. **先讀專案憲法**：若專案根目錄存在 `AGENTS.md`，優先讀取以鎖定不可妥協的業務鐵律與技術邊界。
2. **動態計算各 Agent 專屬技能包（而非整輪只用 1–2 個 Skill）**：
   執行確定性技能規劃器，依任務領域（`debug`、`data_analysis`、`ui_frontend`、`backend_api`、`seo_content`、`simplify_refactor`）為 `Agent 0 ~ E` 配置專屬技能組合（全流水線協同 8–12 個 Skills，但每個 Agent 僅載入與其職責及當輪任務匹配的 3–5 個 Skills，並略過無關的重型 MCP）：
   ```powershell
   python scripts/multi_model_gate.py plan-skills --prompt "<使用者任務描述>"
   ```

| 角色代號與對外模型 | 角色常駐基底技能 | 隨任務領域動態切換之專屬技能（範例） |
|---|---|---|
| **`🛡️ Agent 0 & E-Spec` (`deepseek-flash`)** | `accidental-data-loss-prevention`, `stage-gate-review` | Debug: `fixer-prompt, agent-tester` \| 數據: `data-autocleaning, schema-mapping` \| 後端: `security-audit, agency-testing-api-tester` |
| **`🧠 Agent A & E-Visual` (`gemini-4-argon`)** | `graphify`, `ponytail-audit` | 數據: `storeasy-mini-warehouse-viz, d3-data-visualization` \| UI: `impeccable, frontend-design, agent-desktop` \| SEO: `agency-marketing-data-seo-engineer, agency-marketing-geo-aeo-specialist` |
| **`😈 Agent B Red Team` (`grok-4.7`)** | `ponytail-review`, `agency-engineering-code-reviewer` | Debug: `fixer-prompt, agent-code-analyzer` \| 數據: `agency-support-analytics-reporter, ml-best-practices, xlsx` \| UI: `web-design-guidelines, agency-testing-accessibility-auditor` \| 後端: `security-audit, agency-engineering-database-optimizer` |
| **`⚖️ Agent C & 🛠️ Agent D` (`qwen-3.8-max`)** | `ponytail`, `decisions-governance` | Debug: `fixer-prompt, tdd-workflow` \| 數據: `xlsx, building-data-apps` \| UI: `impeccable, emil-design-eng` \| 後端: `fastapi-templates` |
| **`🎯 Agent Decision / JEV` (`jev-1.13` / `gpt-6.1-sol`)** | `ponytail-review`, `verification-quality` | 當環境配置 `TYPESAFE_API_KEY` 時呼叫 TypeSafe `jev-1.13` API；未配置時自動切換為授權之 `GPT Decision + local_rule_summary_v1` 校準替代方案 |

---

## 步驟 2：`graphify` 知識圖譜導航（先看地圖再動刀）

1. **動刀前查圖譜**：若專案存在 `graphify-out/graph.json` 或 `graphify-out/GRAPH_REPORT.md`，優先查詢核心節點與上下游呼叫鏈：
   ```powershell
   python -m graphify query "<修改目標或概念>"
   ```
2. **動刀後同步圖譜**：修改程式碼後，執行 AST 無損快速更新（零 API 成本）：
   ```powershell
   python -m graphify update .
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
   python scripts/multi_model_gate.py review --prompt "<變更摘要>" --git-diff --output temp_multi_review.json
   ```

---

## 步驟 5：收尾誠實揭露與極簡執行回條 (Final-Turn Compact Lean-Triad Receipt — 嚴禁中繼回合重複輸出)

- **🚫 嚴禁輸出回條之場景（防 Token 浪費）**：等待背景任務（`run_command` / subagent）完成的中繼進度回覆、澄清提問、純問答或閒聊，或同一任務無新程式碼變更時，**絕對禁止**附上執行回條。
- **✅ 僅在「任務最終完成交付（Final Delivery Turn）」結尾輸出一次精簡逐行版回條（每項獨立換行，清晰易讀且省去冗長標題）**：

```markdown
---
**🛡️ Lean-Triad**
- 🧰 **Skills**：`<Skills>`
- 🧭 **Graphify**：`<節點 / update>`
- ✂️ **Ponytail**：`+<新增> / -<刪除> 行 (shortcut: <無或註記>)`
- ⚖️ **Gate & QA**：`<multi_model_gate 真實 verdict/score/req_ids（若未跑腳本強制填「未執行 multi_model_gate」，嚴禁單一模型自評冒充）＋ 測試通過數>`
- ⚠️ **邊界**：`<略過項目與風險>`
```
