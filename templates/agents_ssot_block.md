<!-- BEGIN_LEAN_TRIAD_SSOT -->
## Cursor Cloud & Agent Skills (Lean-Triad 單一真相來源)

> 本區塊由 `scripts/sync_skills_to_cloud_repos.py` 與 `scripts/bootstrap_cursor_cloud.py` 自 `~/.gemini/templates/agents_ssot_block.md`（同步自 `GEMINI.md` / `engineering-core.mdc`）自動鎖定；請勿單獨手改，避免本機與雲端規則分裂。

- **常駐底層引擎與受保護禁區**：`🧭 Graphify 圖譜導航` + `🧰 Role-Scoped Skills 動態掛載` + `✂️ Ponytail 極簡守則` 為常駐引擎；嚴禁簡化 3D 空間幾何／財務計價／硬體 IoT FOV 校準與跨庫 API 契約。
- **規模 × 風險分級強制複查門禁（Tier 0–3）**：
  - 交付前必執行 `python3 scripts/tier_gate.py assess --git-diff`（非 Git 目錄用 `--files <paths...>`；無 `scripts/` 用 `~/.gemini/scripts/tier_gate.py`），依 `required_tier = max(Scale, Risk)`（`S2+R2` 升 `T3`；4 層優先序：P1 保護清單 > P2 鎖檔/產物/symlink 排除 > P3 測試防偷刪/純文件 S1 帽 > P4 生產碼語境分軌）驗收，T2/T3 並跑 `python3 scripts/tier_gate.py verify-pass --git-diff`：
  | Tier | 規模（生產碼 `add+del` / 新增 / 刪減 / 檔數 / 新模組>=40行） | 風險自動升格（路徑或變動行，哪怕改 1 行；UI 純展示豁免裸詞） | 強制驗證與獨立複查（禁作者自寫 mock 驗收） |
  | :--- | :--- | :--- | :--- |
  | **T0** | `<=15` / `<=15` / `<=5` / `1` 檔 / `0` 新模組（純文案/CSS 上限 S1） | `R0` 純文案、註解、靜態樣式 | `rule_lint --git-diff` + 既有測試；免開子代理／多模型 |
  | **T1** | `16–60` / `16–50` / `6–15` / `1–2` 檔 / `0` 新模組 | `R1` 一般邏輯、UI 互動、一般測試 | `T0` + 補 `>=1` 失敗邊界單測 + 型別檢查（UI 補 `agent-desktop`/`e2e`） |
  | **T2** | `61–200` / `51–150` / `16–60` / `3–5` 檔 / `>=1` 新模組 | `R2` `routers/api/webhook/crawler/upload/config/parser/indexer/mcp`、SQL 查詢寫入、測試刪斷言 `>15` 行 | `T1` + `multi_model_gate review`（`PASS`/`PASS_DEGRADED`）+ **1 名獨立唯讀複查者** + 真實資料抽核 + `>=5` 對抗邊界 |
  | **T3** | `>200` / `>150` / `>60` / `>=6` 檔 / `>=2` 新模組（或單檔 `>=150` 行）或 `S2+R2` | `R3` `auth/security/rbac/secret/blacklist`、`migrations/turso/supabase/DDL/破壞性SQL`、門禁與規則自身（`GEMINI.md`/`AGENTS.md`/`DECISIONS.md`/`.cursor/rules/*`/`tier_gate`/`rule_lint`/`multi_model_gate`）、`3D/DXF/FOV/財務計價/薪資/sha256/只作廢不刪除`、跨 repo 契約 | `T2` + `multi_model_gate review --include-grok-api`（`PASS`/`PASS_DEGRADED`）+ **3 角色唯讀 `stage-gate-review`**（邏輯破壞/真實語料稽核/對抗 Fuzz 與密鑰掃描；Python I/O 補 CP950 實測）；0 CRITICAL/HIGH 方可放行 |
  - **模型調度三鐵律與降級協議**：Grok 走 Cursor Plan / `grok.exe` Plan；Gemini 外部腳本清空 API Key 優先 `agy.exe --mode plan` → 失敗才退 DPAPI 官方直連 → OpenRouter；Qwen 預設 `qwen4-max-preview`（備 `qwen-max`）。外部 API 故障時具 `>=2` 異質供應商且 0 紅燈並由異質紅隊補位可降級 `PASS_DEGRADED`；全斷網僅限人類設 `LEAN_TRIAD_BYPASS_REASON` 留痕，嚴禁 AI 自填。
  - **反偽造獨立複查鐵律**：獨立複查僅認 Swarm `board#seq`（`agent != author`）、Subagent ID 或 `multi_model_gate` 真實 `request_id`，**硬拒** `cursor-plan-delegated` / `unknown` 與同 Context 自演；T3 缺獨立唯讀角色禁止宣告完成。
- **確定性門禁與技能路由**：
  - 改碼後必跑 `python3 scripts/rule_lint.py --git-diff`（攔截 UI Emoji、按鈕過長/缺 A11y、`<input type="date" lang="en" />`、`.skip`/空 `catch`、`TODO:`/`FIXME:`/`HACK:`/`XXX:`、裸 `bool(str)`/缺 UTF-8/密鑰字面值；僅允許 `// shortcut: <上限條件>, <何時該升級>`）。
  - 前端 UI 遵循 `stageshow` × `impeccable` × `design-taste-frontend`（`.cursor/rules/react-typescript.mdc`）；精簡時禁刪不可逆警告、交易計價/稅額、合規聲明與 SEO/GEO 訊號。
  - 技能檢索：`python3 scripts/skill_router.py route "<任務描述>"` | 技能矩陣：`python3 scripts/multi_model_gate.py plan-skills --prompt "<任務描述>"`
- **任務結案白話總結與人機雙讀（`/eli5` × `/ponytail`）**：
  - 改碼走 `/ponytail`；結案之「完成項目」與「重點任務總結」走 `/eli5`（先白話說明影響與差異，再保留檔案路徑／API 原文，不稀釋演算法／契約精度）。
  - `README.md` 採雙層標準：上半部給人看（`/eli5` 白話＋`/diagram-design` 中文架構圖 `nodes <= 9, edges <= 12`），下半部給 AI／工程師看（全庫真實結構、啟動測試指令與跨庫紅線）。
- **收尾誠實揭露與極簡防重複回條（Final-Turn Compact Lean-Triad Receipt）**：
  - **🚫 禁輸出場景**：中繼進度、純合併/部署回報、澄清提問、純問答閒聊，或無新程式碼變更時禁附回條。**🚫 防重複**：每欄僅填關鍵字/路徑/行數/結果（`<= 60` 字），正文與回條不互抄。
  - **✅ 最終交付格式**（僅在最終完成交付結尾輸出一次；T2/T3 缺真實 `req`、`pass:` 或獨立複查一律視為未驗收）：
    ```markdown
    ---
    **🛡️ Lean-Triad**
    - 🧰 **Skills**：`<Skills>`
    - 🧭 **Graphify**：`<節點 / update>`
    - ✂️ **Ponytail**：`+<新增> / -<刪除> 行 (shortcut: <無或註記>)`
    - ⚖️ **Gate & QA**：`<tier_token> | gate:<PASS|PASS_DEGRADED|T0-T1免跑>(score, req=<id1,id2>) | review:<board#seq|subagent:id|NONE> | pass:<path|N/A> | tests:<n/n>`
    - ⚠️ **邊界**：`<略過項目與風險>`
    ```
<!-- END_LEAN_TRIAD_SSOT -->
