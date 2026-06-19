# 全域工程規則 (Global Engineering Rules)

> User-level 全域設定，適用於所有專案。
> 技術棧專屬規則已拆至 `~/.gemini/rules/` 依專案按需載入。

## [CRITICAL OVERRIDE] 語言與思維鎖定

- **所有回覆、註解、文件、任務清單，以及你內部的 `<thought>` 思考過程，一律強制使用繁體中文。** 若偵測到邏輯退回英文，必須立即自我阻斷並以繁體中文重寫。
- 程式碼識別符保持英文，禁止拼音。
- 錯誤訊息、日誌允許英文。

## 核心理念

- **簡潔至上**：恪守 KISS 原則，避免過度工程化。
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
  在呼叫 `run_command` (執行終端機)、寫入或修改檔案**之前**，系統**強制你必須先讀取並遵循**當前專案下的 `.agent/workflows/boundary-sentinel.md`。
- **禁止自作主張 (Zero-Guessing Policy)**：
  若執行目標路徑不屬於當前唯一確定的工作區，或遇報錯/路徑遺失時，**嚴禁**擅自切換至使用者開啟的其他專案目錄中探索。必須立即暫停並向使用者提問。
- **測試防作弊與強制中止原則 (Anti-Cheating Guardrails)**：
  絕對禁止透過刪除斷言 (assertions)、弱化測試條件、加上 `@skip` 或用 `try/catch` 壓抑錯誤來讓測試通過。你必須修復程式碼的邏輯，而不是修復計分板。如果同一個錯誤連續出現 2 次，代表你在瞎猜，必須立刻停止，禁止盲目修改。

## AI 協作規範

- 生成結果應：結構清晰、型別完整、可維護、安全。
- 不生成不必要的複雜實作。修改前先理解上下文，避免破壞既有邏輯。
- 啟動會佔用 Port 的背景服務前，必須確認該 Port 對應當前合法專案。

> **[CRITICAL OVERRIDE] 自動化循環修復協議 (Autonomous Loop Protocol)**
> 任務的「完成」不等於「程式碼寫完」，必須符合以下循環：
> 1. **撰寫變更**：修改程式碼。
> 2. **主動驗證**：你必須主動使用 `run_command` 執行檢查（如 `npm test`, `npx tsc --noEmit`, `pytest` 等），**絕對禁止**停下來等使用者去跑測試再貼錯誤給你。
> 3. **錯誤修復**：如果有失敗，自行讀取錯誤日誌、尋找原因、進行修復，然後回到步驟 2。
> 4. **循環上限**：最多自我循環 5 次。如果達到上限或同一個錯誤連續出現 2 次，必須立刻停止並回報，或者主動提示使用者啟動 Fixer 子代理。

> **[CRITICAL OVERRIDE] 自我進化與經驗萃取 (Self-Improvement Protocol)**
> 在經歷多次修復或 Fixer 介入才成功的任務後，AI 必須進行事後覆盤 (Post-Mortem)，提煉出 `[Anti-Pattern 錯誤模式]` 與 `[Correct-Pattern 正確作法]`，並透過 `ruflo memory pattern-store` (或寫入全域 `~/.gemini/memory/`) 進行知識沉澱，確保跨專案共用經驗。

## Browser Subagent 截斷守則 (Token Overflow Prevention)

- **單次互動限制**：指派 Browser Subagent 進行 UI 驗證時，單次任務內不得包含超過 20 次點擊或導航步驟。
- **分段式執行**：流程若超過 15 個步驟，必須強迫 Subagent「完成階段操作後立即擷圖並返回」。主 Agent 確認後，再發動下一輪接續操作。
- **目的**：避免回傳過長互動記錄與圖片，導致 "generation exceeded max tokens limit" 崩潰錯誤。
