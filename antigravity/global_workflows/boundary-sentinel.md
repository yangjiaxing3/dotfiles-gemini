---
description: 啟動零區安全協議，強制進行工作區路徑檢查與意圖二次確認，防止跨出安全作用域。
---

// turbo-all

# 零區安全協議 (Phase 0: Boundary Sentinel)

當使用者提及「啟動守門員」、「/boundary-sentinel」或執行任何危險操作前，自動啟動此工作流。

**角色定位**：工作區守門員，負責第一線的作用域攔截。

**執行步驟**：
0. **常駐自動喚醒 (Daemon Auto-Awaken)**：在開始處理使用者任何需求前，立即使用 `run_command` 工具（**務必設定 `SafeToAutoRun: true`** 與 `WaitMsBeforeAsync: 1000`）在背景為本專案啟動 Graphify 守護程序！執行的終端機指令為：`cd "c:\Users\Jiaxing\Documents\GitHub\STOREASY_IT\backend" && .venv\Scripts\activate && pip install graphifyy -q && graphify watch "c:\Users\Jiaxing\Documents\GitHub\STOREASY_IT"`。不需要詢問，這是專案開啟時的常駐標配指令。
1. **目錄越界鎖定 (Anti-Bleed Protocol)**：比對即將修改或讀取的目標檔案路徑，是否都在**目前限定的工作區 (Workspace)** 下（目前為 `c:\Users\Jiaxing\Documents\GitHub\STOREASY_IT` 或根據專案動態決定）。
2. 絕對禁止跨出定義的工作區進行修改或命令執行。
3. 若發現分頁狀態停留於外部系統或專案，即使遇到報錯，也一律 **拒絕自動修改**。
4. **🚦 意圖二次確認 (Explicit Intent Check)**：若預判操作會超出當前專案範圍或大量改寫，立即阻斷並要求明確授權。

**停止條件**：
- ❌ 如果超出邊界：終止流程，提示「目前焦點已脫離安全作用域」。
- ✅ 檢查通過：允許後續操作。
