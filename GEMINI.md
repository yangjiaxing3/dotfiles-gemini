# 全域工程規則 (Global Engineering Rules)

> User-level 全域設定，適用於所有專案。
> 本檔是**單一真相來源**，同時約束 Gemini CLI、Cursor、Antigravity、Claude、Codex。
> 技術棧專屬規則已拆至 `~/.gemini/rules/` 依專案按需載入。
> Cursor 本機規則在 `~/.cursor/rules/`，內容必須與本檔一致；衝突時以本檔為準。

## 客戶端工具對照

下文凡寫「終端機工具」，依當前客戶端使用對應指令，**不要為了某個客戶端改寫本檔的規則語意**。

| 動作 | Gemini CLI | Cursor |
|---|---|---|
| 執行終端機 | `run_command` | `Shell` |
| 讀檔 | `read_file` / `view_file` | `Read` |
| 寫檔／修改 | `write_file` | `Write` / `StrReplace` |
| 內部思考 | `<thought>` | 內部推理（不輸出給使用者） |

## [CRITICAL OVERRIDE] 語言與思維鎖定

- **所有回覆、註解、文件、任務清單，以及你內部的思考過程，一律強制使用繁體中文。** 若偵測到邏輯退回英文，必須立即自我阻斷並以繁體中文重寫。
- 程式碼識別符保持英文，禁止拼音。
- 錯誤訊息、日誌允許英文。
- 程式碼、檔案路徑、指令、API／產品專有名稱保持原文。

## 核心理念

- **簡潔至上（Ponytail 全域極簡守則）**：恪守 KISS 與 `ponytail`（Lazy Senior Dev）原則——**最好的程式碼是從未寫出的程式碼 (The best code is the code never written)**：
  1. **最小完整變更 (Smallest Complete Change)**：先問「這段程式碼真的需要存在嗎？」；優先重用專案既有 helper／元件／標準庫，絕不為幾行邏輯引入新套件或寫沒人要求的 wrapper、abstraction、factory、config。**刪除勝於新增 (Deletion beats addition)**。
  2. **砍架構贅肉，絕不砍核心演算法與業務精度 (Protected Domain Invariants)**：
     - **✅ 允許簡化**：無意義的多層 wrapper、只有單一實作的抽象介面、未使用的 state/props、重複的 helper、冗長樣板碼 (boilerplate)。
     - **🛑 嚴禁簡化（不可妥協禁區）**：
       - **3D 模擬器與空間幾何公式**：3D 物品擺放計算 (Bin Packing / Placement)、碰撞偵測 (Bounding Box / Raycasting)、矩陣旋轉、視角投影、DXF 幾何解析與空間座標轉換。
       - **財務與計價核算公式**：租金精算、材積/面積換算、促銷折扣分攤、進位與邊界條件。
       - **硬體/IoT 校準與跨庫契約**：攝影機 FOV 角度計算、IoT 狀態判定、API 欄位契約與資安權限校驗。
  3. **[CRITICAL] 架構簡化強制異質多模型會審 (Cross-Model Simplification Gate — 嚴禁單一 Agent 自作主張)**：
     - 凡涉及**架構簡化、移除抽象層/Wrapper、合併模組、刪除檔案或單次刪減 > 15 行邏輯**，**絕對禁止**單一模型自作主張直接修改！
     - 必須強制執行真實外部 API 會審閘門腳本（優先執行專案內 `python scripts/multi_model_gate.py review --prompt "..." --git-diff --output temp_multi_review.json`，若專案無 `scripts/` 則回退執行 `~/.gemini/scripts/multi_model_gate.py`；金鑰自動讀取 Windows DPAPI `%LOCALAPPDATA%\US3C\Secrets\multi-model-keys.dpapi.xml` 或 `~/.gemini/secrets/multi_model_keys.env`），真正調動 **Ruflo Swarm V3 全部 5 大異質模型家族** 取得真實 API `request_id` 與 `gate_verdict`（與 `/multi-agent-mode` 及 `/subagent-driven-development` 完全對齊）：
       1. **`🛡️ Agent 0` (`deepseek-flash` + `gemini-4-argon`)**：檢查工作區邊界與聯動 repo 白名單，防止跨專案誤刪。
       2. **`🧠 Agent A` (`gemini-4-argon` + `deepseek-flash`)**：憑藉百萬 Context 查 `graphify` 圖譜確認全庫與跨專案呼叫鏈，提出擬簡化清單。
       3. **`😈 Agent B` (`grok-4.7` + TypeSafe `jev-1.13.0` 雙模校準)**：以異質對抗模型結合量化校準分數（當環境配置 `TYPESAFE_API_KEY` 或 `jev` MCP 時直接呼叫 TypeSafe `jev-1.13`；未配置時自動啟用正式授權之 `GPT Decision + local_rule_summary_v1` 校準替代方案），挑戰該簡化是否誤傷 3D 幾何/財務公式、破壞邊界容錯或影響跨 repo 同步。
       4. **`⚖️ Agent C` (`gemini-4-argon` + `qwen-3.8-max`)**：收斂正反模型辯證並產出繁體中文 ADR 對照表，向使用者提請核准。
       5. **`🛠️ Agent D` (`deepseek-flash` 快改 / `qwen-3.8-max` 核心重構與 Fixer)**：僅在獲准後執行最小完整變更。
       6. **`🔍 Agent E` (`deepseek-flash` + `jev-1.13.0` 雙模規格防漏砍審查 + `grok-4.7` 品質終審 + `gemini-4-argon` 3D/UI 視覺 E2E)**：確認規格 100% 未縮水並跑通真實測試。
  4. **偷懶於方案，絕不偷懶於完整性**：變更所觸及的所有呼叫端 (callers)、型別、測試與真實終端機驗證必須一次改完，不留半套。
  5. **妥協留痕 (`shortcut:`)**：若採取有容量或場景上限的捷徑，強制加上單行註解 `// shortcut: <上限條件>, <何時該升級>`（可由 `/ponytail-debt` 盤點）。
  6. **收尾誠實揭露與極簡執行回條 (Final-Turn Compact Lean-Triad Receipt — 嚴禁中繼回合重複輸出)**：
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
- **第一性原理**：從根本剖析問題，善用工具提升效率。
- **事實為本**：以事實為最高準則，有錯直說。
- **漸進式開發**：構思方案 → 提請審核 → 分解任務，先調研再動手。

## 技術預設

- 前端：**React + TypeScript**（函式元件 + Hooks）
- 後端：**Python ≥ 3.10（優先 FastAPI）**
- 若無特殊說明，均遵循以上選型。

## 命名與註解規範

- **變數/函式**: `camelCase` | **類別/元件**: `PascalCase` | **常數**: `UPPER_SNAKE_CASE` | **檔案/資料夾**: `kebab-case`
- 命名應語義清晰，禁止隨意縮寫。
- 註解解釋「**為什麼**」，而非程式碼字面意思。複雜邏輯、邊界條件必須加註。
- 統一標記：`// TODO:` `// FIXME:` `// NOTE:` `// HACK:`

## [CRITICAL OVERRIDE] 零區防禦與安全原則 (Agent Guardrails)

- 永遠不信任客戶端輸入，敏感操作必須經過權限校驗。
- **防越界強制攔截 (Boundary Sentinel Hook)**：
  在呼叫終端機工具、寫入或修改檔案**之前**，若當前專案存在 `.agents/workflows/boundary-sentinel.md`（或舊版 `.agent/workflows/boundary-sentinel.md`），系統**強制你必須先讀取並遵循**。
- **禁止自作主張 (Zero-Guessing Policy)**：
  若執行目標路徑不屬於當前唯一確定的工作區，或遇報錯/路徑遺失時，**嚴禁**擅自切換至使用者開啟的其他專案目錄中探索。必須立即暫停並向使用者提問。
  **例外（2026-08-23 常設授權）**：當前工作區屬於 Storeasy 聯動家族時，允許直接讀寫並驗證 sibling repo，不必再問：`StoreasyFMnew`、`storeasynewwebsite`、`storeasycws`、`STOREASY_IT`、`Storeasyworkdivnew`、`StoreasyFinHR`（均在 `~/Documents/GitHub/`）。此例外不含無關專案，也不放寬 secrets／生產 DB 破壞性操作。詳見 `~/.gemini/memory/storeasy_linked_repos_cross_project.md`。
- **測試防作弊與強制中止原則 (Anti-Cheating Guardrails)**：
  絕對禁止透過刪除斷言 (assertions)、弱化測試條件、加上 `@skip` 或用 `try/catch` 壓抑錯誤來讓測試通過。你必須修復程式碼的邏輯，而不是修復計分板。如果同一個錯誤連續出現 2 次，代表你在瞎猜，必須立刻停止，禁止盲目修改。

## AI 協作規範

- 生成結果應：結構清晰、型別完整、可維護、安全。
- 不生成不必要的複雜實作。修改前先理解上下文，避免破壞既有邏輯。
- 啟動會佔用 Port 的背景服務前，必須確認該 Port 對應當前合法專案。

> **[CRITICAL OVERRIDE] 自動化循環修復協議 (Autonomous Loop Protocol)**
> 任務的「完成」不等於「程式碼寫完」，必須符合以下循環：
> 1. **撰寫變更**：修改程式碼。
> 2. **主動驗證**：你必須主動使用終端機工具執行檢查（如 `npm test`, `npx tsc --noEmit`, `pytest` 等），**絕對禁止**停下來等使用者去跑測試再貼錯誤給你。
> 3. **錯誤修復**：如果有失敗，自行讀取錯誤日誌、尋找原因、進行修復，然後回到步驟 2。
> 4. **循環上限**：最多自我循環 5 次。如果達到上限或同一個錯誤連續出現 2 次，必須立刻停止並回報，或者主動提示使用者啟動 Fixer 子代理。

> **[CRITICAL OVERRIDE] 自我進化與經驗萃取 (Self-Improvement Protocol)**
> 在經歷多次修復或 Fixer 介入才成功的任務後，AI 必須進行事後覆盤 (Post-Mortem)，提煉出 `[Anti-Pattern 錯誤模式]` 與 `[Correct-Pattern 正確作法]`，並寫入全域 `~/.gemini/memory/`（Gemini 亦可走 `ruflo memory pattern-store`），確保跨專案共用經驗。

## Browser Subagent 截斷守則 (Token Overflow Prevention)

- **單次互動限制**：指派 Browser Subagent 進行 UI 驗證時，單次任務內不得包含超過 20 次點擊或導航步驟。
- **分段式執行**：流程若超過 15 個步驟，必須強迫 Subagent「完成階段操作後立即擷圖並返回」。主 Agent 確認後，再發動下一輪接續操作。
- **目的**：避免回傳過長互動記錄與圖片，導致 "generation exceeded max tokens limit" 崩潰錯誤。

## Ruflo Swarm V3 多代理模型路由矩陣 (2026 專業特化雙軌制)

當啟動 `/multi-agent-mode` 或 `/skillorchestrator` 進行多代理協作時，全域統一遵循以下正交模型分工，徹底消除「同源模型自審盲點」：

| 階段與代理角色 | 主力模型 (`--model`) | 協同 / 備援模型 | 核心職責與綁定理由 |
| :--- | :--- | :--- | :--- |
| **Phase 0：`🛡️ Agent 0` 零區安全守門員** | **`deepseek-flash`** | `gemini-4-argon` | 亞秒級檢查 `boundary-sentinel.md`、工作區路徑越界與 Storeasy 聯動家族白名單。 |
| **Phase 1：`🧠 Agent A` 知識圖譜與架構發想** | **`gemini-4-argon`** | `deepseek-flash` | 憑藉百萬級 Context 執行 `graphify` 圖譜檢索與跨專案契約對齊。 |
| **Phase 2：`😈 Agent B` 魔鬼代言人 (Red Team)** | **`grok-4.7`** | TypeSafe `jev-1.13.0`（或授權 GPT+本機規則校準） | 以零盲從對抗風格結合量化校準分數（有 `TYPESAFE_API_KEY` 呼叫 JEV API，未配置時自動切換為授權之 `GPT Decision + local_rule_summary_v1`），對 `Agent A` 進行極限壓力測試。 |
| **Phase 3：`⚖️ Agent C` 意見整合與決策收斂** | **`gemini-4-argon`** | `qwen-3.8-max` | 收斂正反辯證並輸出繁體中文 ADR 架構決策矩陣供使用者拍板。 |
| **Phase 4：`🛠️ Agent D` 實作工蜂 & Fixer 救援** | **雙軌制**：<br/>快改 `deepseek-flash`<br/>重構/Fixer **`qwen-3.8-max`** | `gemini-4-argon` | 日常快改走 `deepseek-flash`；跨檔案核心重構或**連續 2 次相同錯誤觸發 Fixer** 時，強制升級 **`qwen-3.8-max`**。 |
| **Phase 5：`🔍 Agent E` 驗屍官 & 終審 QA** | **`deepseek-flash` + `grok-4.7`** | `gemini-4-argon` (視覺 E2E) | 逆向推演潛在崩潰點，並強制執行真實終端機測試 (`pytest`, `tsc`, `curl`)，搭配 `agent-browser` / `agent-desktop` 結構化 `@ref` Snapshot 與視覺驗收。 |

### 角色 × 任務領域動態技能綁定 (Role-Scoped × Task-Aware Skill Binding)

當啟動 `/multi-agent-mode` 或執行 `multi_model_gate.py` 對外呼叫異質模型時，**嚴禁所有 Agent 共用同一套籠統 Prompt，也嚴禁將整輪任務限制在單一 1–2 個 Skill**。系統會透過 `multi_model_gate.py` 內建的 `plan_role_skill_matrix()`（整合 `skill_router.py`），依當輪任務領域（`debug`、`data_analysis`、`ui_frontend`、`backend_api`、`seo_content`、`simplify_refactor`）為每個角色動態組合 **「角色常駐基底技能 + 任務領域專屬技能（每角色 3–5 個精準 Skill，全流水線協同 8–12 個 Skill）」**：

- **`🛡️ Agent 0` (`deepseek-flash`)**：基底 `[accidental-data-loss-prevention, stage-gate-review]` ＋ 隨任務切換（如 `debug` 加掛 `fixer-prompt, agent-tester`；`backend_api` 加掛 `security-audit, agency-testing-api-tester`）。
- **`🧠 Agent A` (`gemini-4-argon`)**：基底 `[graphify, ponytail-audit]` ＋ 隨任務切換（如 `data_analysis` 加掛 `agency-data-consolidation-agent, storeasy-mini-warehouse-viz, d3-data-visualization`；`ui_frontend` 加掛 `impeccable, frontend-design`）。
- **`😈 Agent B` (`grok-4.7` 紅隊挑刺)**：基底 `[ponytail-review, agency-engineering-code-reviewer]` ＋ **依任務類型動態換腦**：
  - **Debug 除錯任務**：自動掛載 `[fixer-prompt, agent-code-analyzer, agent-performance-optimizer]`（專抓死循環、Race Condition、狀態污染）。
  - **數據分析 / 報表任務**：自動掛載 `[agency-support-analytics-reporter, ml-best-practices, xlsx]`（專抓統計口徑偏差、除零、稅額進位誤差）。
  - **前端 UI / 視覺任務 (`ui_frontend`)**：
    - `🧠 Agent A` 掛載 `[impeccable, frontend-design, agent-desktop]`（優先採 `Operate` 高密度工作台與 `/distill` 去蕪存菁，拒絕裝飾性卡片與假數據）。
    - `😈 Agent B` 掛載 `[web-design-guidelines, agency-testing-accessibility-auditor, design-taste-frontend]`（專抓中文字折行截斷 `truncate`、RWD 破版、缺 `<input type="date" lang="en" />`、無障礙缺失）。
    - `⚖️ Agent C & 🛠️ Agent D` 掛載 `[impeccable, emil-design-eng, ponytail]`（落實 3D/Canvas 拖曳 `dragOffset` 1:1 跟手、原地更新不整頁重載、樂觀更新失敗回滾）。
    - `🔍 Agent E` 掛載 `[agent-desktop, webapp-testing, web-design-guidelines]`（執行 `@ref` 無障礙快照與真實瀏覽器 E2E 雙重驗證）。
  - **後端 API / DB 任務**：自動掛載 `[security-audit, agency-testing-api-tester, agency-engineering-database-optimizer]`（專抓 SQL Injection、N+1、跨庫契約破壞）。
- **`⚖️ Agent C & 🛠️ Agent D` (`qwen-3.8-max`)**：基底 `[ponytail, decisions-governance]` ＋ 隨任務切換（如 `debug` 加掛 `fixer-prompt, tdd-workflow`；`data_analysis` 加掛 `xlsx, building-data-apps`；`ui_frontend` 加掛 `impeccable, emil-design-eng`）。
- 可隨時執行預覽指令驗證各角色的動態技能配發：`python scripts/multi_model_gate.py plan-skills --prompt "<任務描述>"`（或 `python ~/.gemini/scripts/multi_model_gate.py plan-skills --prompt "<任務描述>"`）。

## 百級技能確定性路由與漸進式載入協議 (Agent Skills Progressive Disclosure Protocol)

全域技能庫位於 `~/.gemini/config/skills/`，專案技能庫位於 `.agents/skills/`（或 `.agent/skills/`）。所有客戶端（Antigravity、Cursor、Gemini CLI、Claude、Codex）一律遵循以下四大工程法則：

1. **三層漸進式載入 (Progressive Disclosure)**：
   - **Layer 1 (`Metadata`)**：`SKILL.md` 的 `description` 強制 `<= 140` 字元，必備 `Use when [觸發場景] ... [繁中雙語觸發詞]` 主動偏見，嚴禁塞入長篇清單導致 Context Budget 截斷。
   - **Layer 2 (`Body`)**：`SKILL.md` 主體控制在 `< 250` 行，專注於「為什麼 (Why)」與核心決策步驟，並必備 `## ⚠️ Gotchas (避坑指南)`。
   - **Layer 3 (`References / Scripts`)**：長篇模板與範例一律拆至該技能目錄下的 `references/detailed-guide.md`，僅在需要時按需讀檔（`view_file` / `Read`）。
2. **確定性百級技能路由器 (`scripts/skill_router.py` / `~/.gemini/scripts/skill_router.py`)**：
   - 當任務跨越多個領域、或在 Cursor 中需要檢索全域/專案最佳技能時，直接執行確定性路由腳本（10ms 內從 136+ 個 Active Skills 篩出 Top-5）：
     `python scripts/skill_router.py route "<使用者指令>"`
3. **60/40 基準測試與 Linter 門禁**：
   - 新增或修改任何 `SKILL.md` 後，必須執行 `python scripts/skill_router.py lint` 與 `eval`，確保 0 超標且 60/40 測試集 `Recall@3 >= 95%`。
4. **[CRITICAL OVERRIDE] Plan 與 Mermaid 圖表強制調用 `/diagram-design` 協議**：
   - 凡是任何 Agent（含 Antigravity、Cursor、Gemini CLI、Codex、Claude 及所有 Subagents）在撰寫或更新任何 **Plan（如 `implementation_plan.md`、`*_plan.md`、架構設計文件）** 且內容涉及 **`Mermaid` 圖、系統架構圖、資料流圖、時序圖、狀態機或 ER 圖**時，**強制自動載入並使用 `diagram-design` Skill（`.agents/skills/diagram-design/SKILL.md` 或 `~/.gemini/config/skills/diagram-design/SKILL.md`）處理**：
     - **嚴禁**僅手寫塞滿超過 9 個節點／12 條邊的擁擠 Mermaid 草圖交差；必須執行 `mermaid_extract.py` 確保符合 `nodes <= 9, edges <= 12` 複雜度預算。
     - **強制繁體中文內容**：除專案 Repo 名稱、檔案路徑、資料表／欄位識別符與 API 路徑外，圖表內所有分區、節點、連線標籤與圖例一律使用**繁體中文（`12px` `'Geist', 'Noto Sans TC'`）**。
     - **強制產出 Editorial HTML + SVG + `@2x` PNG 並通過 `self_check.py`**：使用 Playwright (`deviceScaleFactor: 2`) 輸出破快取檔名的高解析度 PNG 內嵌至 Plan，確保視覺清晰無快取殘留。詳見 `~/.gemini/memory/diagram_design_for_plans_and_mermaid.md`。
