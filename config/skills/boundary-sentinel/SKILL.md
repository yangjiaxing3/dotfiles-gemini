---
name: boundary-sentinel
description: "'零區安全協議：工作區路徑檢查與意圖二次確認。Use when a request might leave the current project boundary or touch another repo.'"
---

// turbo-all

# 零區安全協議 (Phase 0: Boundary Sentinel)

當使用者提及「啟動守門員」、「/boundary-sentinel」或執行任何危險操作前，自動啟動此工作流。

**角色定位**：工作區守門員，負責第一線的作用域攔截。

**執行步驟**：
1. **目錄越界鎖定 (Anti-Bleed Protocol)**：比對即將修改或讀取的目標檔案路徑，是否都在**目前限定的工作區 (Workspace)** 下（目前為 `c:\Users\Jiaxing\Documents\GitHub\STOREASY_IT` 或根據專案動態決定）。
2. 絕對禁止跨出定義的工作區進行修改或命令執行。
3. 若發現分頁狀態停留於外部系統或專案，即使遇到報錯，也一律 **拒絕自動修改**。
4. **🚦 意圖二次確認 (Explicit Intent Check)**：若預判操作會超出當前專案範圍或大量改寫，立即阻斷並要求明確授權。

**停止條件**：
- ❌ 如果超出邊界：終止流程，提示「目前焦點已脫離安全作用域」。
- ✅ 檢查通過：允許後續操作。

---

## 🛑 [CRITICAL] 自動化循環驗證協議 (Autonomous Loop Protocol)

**【Anti-Pattern 反模式】**
> 實作前端 API 呼叫後，僅依賴後端單元測試通過，或僅看靜態 Code Review 沒發現錯誤就直接交回給使用者，結果因為前端 `apiClient` 遺漏 `/api/` 等路徑前綴，導致使用者畫面出現 `404 Not Found`。

**【Correct-Pattern 正確作法】**
> 1. **前置防呆 (API Contract Check)**：任何牽涉前後端通訊的修改，必須強制比對 Frontend API Client 的路徑與 Backend Router 的路徑。
> 2. **動態執行驗證 (Dynamic Execution Validation)**：實作完畢後，Agent 必須使用 `run_command` (如 `curl`, Playwright, 或是專案的 E2E 腳本) 實際在終端機對該 Endpoint 或 UI 進行動態測試。
> 3. **禁止瞎等**：絕對不允許停下來等待使用者測試再貼錯誤給你。必須親眼看到 HTTP 200 或 `PASS` 日誌後，才能交件或進入下一個 Review 階段。

## ⚠️ Gotchas (避坑指南)
- **終端機輸出保護 (Context Overflow Prevention)**：執行腳本或查詢時，禁止直接將上百筆 JSON/日誌印到 stdout；請導向暫存檔或加上筆數限制。
- **零區防禦與 Port 禁令**：修改或執行指令前嚴守工作區邊界，嚴禁綁定或終止保留埠 (`8000`、`5100`、`3000`)。
