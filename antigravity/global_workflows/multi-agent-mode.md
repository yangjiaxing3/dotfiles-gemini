---
description: 啟動五階段多 Agent 協作模式 (0→A→B→C→D→E)，從發想、質疑、整合、實作到驗證，確保每項優化都經過嚴謹的辯證流程。
---

// turbo-all

# 多 Agent 模式 (Multi-Agent Pipeline — Ruflo Swarm V3)

當使用者提及「多 Agent 模式」、「多agent」、「/multi-agent」時，啟動此工作流。
AI 必須依序扮演六個獨立角色（Phase 0 ~ Phase 5），每個角色有明確的輸入、產出和停止條件，並嚴格遵守 **Ruflo Swarm V3 (2026.10) 專業特化雙軌模型分配矩陣**（正交分離發想、批判、實作與驗屍模型，杜絕同源盲點）。

| 階段 | 角色代號 | 核心職責 | 主力路由模型 (Primary Model) | 升級 / 協同模型 (Escalation / Co-Model) |
| :--- | :--- | :--- | :--- | :--- |
| **Phase 0** | 🛡️ **Agent 0** | 零區安全守門員 (Boundary Sentinel) | `DeepSeek-V4.1-Flash` | `gemini-4-argon` |
| **Phase 1** | 🧠 **Agent A** | 知識圖譜與架構發想 (Ideation & Graph) | `gemini-4-argon` | `DeepSeek-V4.1-Flash` (高速 CoT 輔助) |
| **Phase 2** | 😈 **Agent B** | 魔鬼代言人紅隊批判 (Red Teaming) | `grok-4.7` | TypeSafe `jev-1.13.0` (量化風險校準) |
| **Phase 3** | ⚖️ **Agent C** | 意見整合與決策收斂 (Synthesis) | `gemini-4-argon` (Orchestrator) | `qwen-3.8-max` |
| **Phase 4** | 🛠️ **Agent D** | 外科手術實作工蜂 & Fixer 救援 | 日常快改：`DeepSeek-V4.1-Flash`<br/>核心重構：`qwen-3.8-max` | 連續 2 次失敗強制升級：`qwen-3.8-max` |
| **Phase 5** | 🔍 **Agent E** | 驗屍官逆向推演與終審 QA (Pre-mortem) | `DeepSeek-V4.1-Flash` + `grok-4.7` | `gemini-4-argon` (視覺與多模態 E2E) |

---

## 執行流程與 Swarm Routing

### Phase 0: 🛡️ Agent 0 — 零區安全協議 (Boundary Sentinel)

**模型路由**: `DeepSeek-V4.1-Flash` (毫秒級邊界與意圖快篩分類器)
**角色定位**：工作區守門員，負責第一線的作用域與邊界攔截。

**執行步驟**：
1. **目錄越界鎖定 (Anti-Bleed Protocol)**：主動檢查使用者要求的目標與即將操作的路徑，確認是否都在目前的活動工作區 (Active Workspace) 或已授權之 Storeasy 聯動家族內。
2. 絕對禁止跨出已定義的工作區進行修改或命令執行。
3. **🚦 意圖二次確認 (Explicit Intent Check)**：若預判操作會超出當前授權專案範圍，立即阻斷並要求明確授權。

**停止條件**：
- ❌ 如果超出邊界：終止流程，回報「目前焦點已脫離安全作用域」。
- ✅ 檢查通過：將控制權交給 Agent A 繼續執行。

---

### Phase 1: 🧠 Agent A — 知識圖譜與優化發想 (Knowledge Mapping & Ideation)

**模型路由**: `gemini-4-argon` (超大上下文、跨專案知識圖譜與多模態架構推理) + `DeepSeek-V4.1-Flash` (高速 CoT 發想)
**呼叫指令**: `claude-flow agent spawn -t ideation --model gemini-4-argon`
**角色定位**：創新架構師，負責全局視角建立與腦力激盪。

**執行步驟**：
1. **隔離上下文傳遞 (Context Federation)**：嚴禁盲目傾倒無關檔案。優先結合 `graphify` 知識圖譜傳遞與任務直接相關的 API 介面定義或 1-hop 依賴樹。
2. 讓 `gemini-4-argon` 進行深度結構推理，提出 **至少 2~3 種** 可能的優化方案。
3. 每個方案必須包含：
   - 方案名稱與一句話描述
   - 技術實作概要
   - ✅ 優點（為什麼值得做）
   - ⚠️ 風險/成本（實作複雜度、依賴項，多解法比較 Tradeoffs）
   - 🛡️ 邊界影響

**停止條件**：草案產出完成後，自動切換至 Agent B。

---

### Phase 2: 😈 Agent B — 高度質疑模式 (Red Teaming)

**模型路由**: `grok-4.7` - First-Principles Red Teaming & Max Skepticism (利用其第一性原理直覺、反盲從特性與犀利邊界嗅覺批判 Agent A)
**呼叫指令**: `claude-flow agent spawn -t reviewer --model grok-4.7`
**角色定位**：魔鬼代言人，啟動「正交維度交叉掃描」(Orthogonal Dimension Scanning) 審查每個方案，徹底消除「同源模型自審盲點」。

**執行步驟**：
1. **送交審查**：將 Agent A (`gemini-4-argon`) 產出的草案交由異構模型 `grok-4.7` 進行無情批判。
2. 針對以下 5 個維度進行極端破壞性分析：
   - ☠️ **資料毒化 (Data Poisoning)**：若傳入極端值、空值或髒資料，防禦機制會否崩潰？
   - 🔄 **併發與狀態 (Concurrency)**：多個 User 同時操作時，資料會不會髒寫或 Race Condition？
   - ⏳ **時間腐敗 (Temporal Decay)**：跨時區、歷史舊資料截斷、閏年執行會出錯嗎？
   - 🔗 **邊界盲區 (Boundary Blindspots)**：前後端介接格式不符、API 欄位缺失時處理會壞嗎？
   - 🐢 **效能瓶頸 (Performance)**：是否存在 N+1 Query、深拷貝阻塞或 O(n²)？
3. 為每個方案給出風險評級：`🟢 低風險` / `🟡 中風險` / `🔴 高風險`

**停止條件**：所有方案審查完畢後，自動切換至 Agent C。

---

### Phase 3: ⚖️ Agent C — 意見整合與最終方案 (Synthesis & Simplicity First)

**模型路由**: `gemini-4-argon` / Primary LLM (Antigravity Orchestrator)
**角色定位**：技術決策者，綜合 Agent A (`gemini-4-argon`) 的創意與 Agent B (`grok-4.7`) 的紅隊批判，產出隔離污染的最終設計文件。

**執行步驟**：
1. 吸收 Agent A 的架構與 Agent B 的批判，進行決策收斂。
2. 過濾掉風險過高或過度工程化的方案。
3. **防禦性完整完工**：確保最終方案涵蓋所有邊界條件與錯誤捕捉。
4. **生成 Artifact**：將最終決定封裝成結構化的 Artifact (`implementation_plan.md`)，並將後續工作拆解為最小單元的 Task 單。

**停止條件**：
- ⏸️ **若任務涉及 3 個以上檔案修改**，在此暫停並要求使用者審核 `implementation_plan.md`。
- ▶️ **若任務簡單（≤2 檔案）**，自動進入 Agent D。

---

### Phase 4: 🛠️ Agent D — 開始進行製作 (Implementation & Surgical Changes)

**模型路由**: 雙軌制 — 日常單檔快改 `DeepSeek-V4.1-Flash`；跨模組核心重構 / 複雜 React+TS / 失敗救援強制升級 `qwen-3.8-max`
**呼叫指令**: `claude-flow agent spawn -t coder --model qwen-3.8-max` (或 `--model DeepSeek-V4.1-Flash`)
**角色定位**：實作工蜂與外科手術專家，專注產出高品質、零破壞的程式碼。

**執行步驟**：
1. 依照 Agent C 的 Task 單進行分流實作：單純邏輯或微調交由 `DeepSeek-V4.1-Flash` 極速完成；涉及 3 檔以上跨層重構、複雜狀態管理或資料庫 Schema 變更時，直接動用 `qwen-3.8-max`。
2. **UI/UX 任務防呆**：若牽涉前端畫面，強制掛載標準化組件庫與 Design Skills，確保多角色權限視角與響應式互動一致。
3. **外科手術式打擊 (Surgical Context)**：只傳入需要修改的 AST 節點或單一檔案內容，從物理上杜絕幻覺去修改不相干檔案的可能。
4. **Swarm 升級機制 (Dynamic Escalation)**：若 `DeepSeek-V4.1-Flash` 提交的程式碼連續 2 次通不過靜態檢查或邏輯錯誤，Swarm 自動將該任務強制升級，改用 `claude-flow agent spawn -t fixer --model qwen-3.8-max` 啟動零區第一性原理救援。

**停止條件**：所有程式碼寫入完成後，切換至 Agent E。

---

### Phase 5: 🔍 Agent E — 驗屍官與最終審查 (Goal-Driven Pre-mortem)

**模型路由**: `DeepSeek-V4.1-Flash` + `grok-4.7` 負責逆向邏輯推演與契約審查 + `gemini-4-argon` / 原生 Browser Subagent 負責視覺多模態驗證
**呼叫指令**: `claude-flow agent spawn -t qa --model DeepSeek-V4.1-Flash`
**角色定位**：驗屍官 + QA 工程師。

**執行步驟**：
1. **確立 Goal-Driven 標靶**：檢查任務是否拆解為 `[Step] → verify: [check]` 的 TDD 驗證條件。
2. **驗屍官逆向推演 (Pre-mortem Analysis)**：強制要求模型回答：「假設這段程式碼剛上線就導致正式機崩潰，列出前 3 大最可能的致死原因」。
3. **防禦確認**：檢查 Agent D 的程式碼是否已針對上述 3 大死因實作防禦。
4. **靜態分析**：執行 `npx tsc --noEmit` 與後端 `pytest`。
5. **🌐 端到端與 API 整合測試 (E2E & API Contract Validation)**：
   - 絕不能僅依賴靜態檢查。若牽涉前端與 API 的串接，強制執行整合測試或動態端點驗證去打擊真實 Endpoint。
   - 若出現 `404 Not Found` 或是 `Network Error`，必須將錯誤日誌與 Terminal 輸出打包，啟動 Loop 退回。
6. **退回與靶向救援 (Surgical Fixer Loop)**：若觸發退回，必須將「無污染的 Context (僅原始任務目標 + 報錯 Log + 出錯單一檔案 AST)」交回給 Agent D (`qwen-3.8-max`)，切斷歷史幻覺。

**判定邏輯**：
- 🟢 PASS — 產出最終報告 Artifact (`walkthrough.md`) 並回報完成。
- 🔴 FAIL — 若存在問題，退回 Agent D (`qwen-3.8-max`) 修正（最多 2 次迭代）。

---

## 執行規則

1. **角色切換明確標示**：
   ```
   ---
   ### 🤖 Agent [X]: [角色名稱] (Model: [使用模型])
   ---
   ```
2. **鏈式傳遞**：0→A→B→C→D→E，不可跳過。
3. **所有 Agent 的分析與產出必須使用繁體中文**。