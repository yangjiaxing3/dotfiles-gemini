---
name: multi-agent-mode
description: "Use when tasks need 5-stage dialectical review (Sentinel/Ideation/Red Team/Synthesis/QA) to prevent blind spots. 多Agent模式/紅隊辯證/multi-agent"
---

# 多 Agent 模式（0→A→B→C→D→E，Ruflo Swarm V3 全模型正交路由）

目的：用異質模型與角色分離消除「自己寫、自己審、自作主張簡化」的盲點。六個角色依序執行，**不可跳過**。環境無法真的分派子代理時，仍要維持角色分離與停止條件。

每次切換角色都標示：`### 🤖 Agent [X]（[模型]）：[角色]`。全程繁體中文。

| Phase | 角色 | 主力模型 (`--model`) | 協同 / 備援模型 | 產出與 Ponytail 簡化把關職責 | 停止條件 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **0** | 🛡️ 邊界守門員 | **`deepseek-flash`** | `gemini-4-argon` | 確認路徑與指令在工作區（或授權聯動 repo）內，防跨庫誤刪 | 越界 → 停止並請求授權 |
| **A** | 🧠 圖譜與發想 | **`gemini-4-argon`** | `deepseek-flash` | 查 `graphify` 圖譜呼叫鏈，提 2–3 個方案（標註可重用元件與擬簡化項） | 方案寫完 → B |
| **B** | 😈 紅隊挑刺 | **`grok-4.7`** | TypeSafe **`jev-1.13.0`** | 對每個方案攻擊 6 個維度並結合 JEV 量化校準評 🟢/🟡/🔴 | 全部評完 → C |
| **C** | ⚖️ 整合收斂 | **`gemini-4-argon`** | **`qwen-3.8-max`** | 收斂正反意見，寫 `implementation_plan.md`（含擬刪減項目對照表） | 改動 ≥3 檔或刪減架構 → 暫停給使用者審；否則 → D |
| **D** | 🛠️ 實作與 Fixer | 快改 **`deepseek-flash`**<br/>重構/Fixer **`qwen-3.8-max`** | `gemini-4-argon` | 只改計畫核准的檔案，遵循 `ponytail` 最小完整變更 | 連續 2 次失敗 → 升級 `qwen-3.8-max` (`fixer-prompt`) |
| **E** | 🔍 驗屍與終審 QA | **`deepseek-flash` + `grok-4.7`** | **`jev-1.13.0`** (規格校準)<br/>**`gemini-4-argon`** (視覺 E2E) | 預演前 3 大致死原因、確認簡化未漏砍規格、跑真實測試與 `@ref` 驗證 | PASS → `walkthrough.md`；FAIL → 回 D（最多 2 輪） |

## Phase A：只傳相關脈絡（`gemini-4-argon` + `deepseek-flash`）

只帶與任務直接相關的介面、型別與一層依賴；有 `graphify` 圖譜就先查圖譜確認所有 callers，不要把整個專案丟進來。

## Phase B：六個攻擊維度（`grok-4.7` + TypeSafe `jev-1.13.0`）

1. **髒資料**：空值、極端值、格式錯、編碼錯時會不會崩？
2. **併發**：多人同時操作會不會髒寫、重複送出、競態？
3. **時間**：時區、跨月/閏年、歷史資料、快取過期。
4. **邊界介接**：前後端欄位不一致、API 缺欄位、版本不相容。
5. **效能**：N+1 查詢、O(n²)、大檔一次讀進記憶體。
6. **Ponytail 極簡度與防過度簡化雙向審查 (Lean vs. Over-Simplification Gate)**：
   - **挑過度設計**：有沒有多寫沒人要求的 wrapper/abstraction/config？能不能重用既有 helper？
   - **防自作主張過度簡化（全模型交叉把關）**：若提案涉及簡化既有架構或刪減 >15 行邏輯，必須同時通過：
     - `gemini-4-argon`（確認 `graphify` 圖譜與跨 repo 零斷鏈、3D/UI 視覺無損）
     - `grok-4.7` + `jev-1.13.0`（對抗式檢查是否誤傷 **3D 模擬器擺放/碰撞公式、DXF 幾何解析、財務精算** 或邊界容錯）
     - `qwen-3.8-max`（架構重構完整性與型別安全收斂）
     - `deepseek-flash` + `jev-1.13.0`（Spec Compliance 100% 規格未縮水校驗）

紅隊必須引用具體程式碼或資料，不接受「可能有風險」這種空話。

## Phase D & E：極簡實作與驗證要真的跑

- **Phase D（`deepseek-flash` / `qwen-3.8-max` 實作守則）**：遵循 `ponytail` 最小完整變更原則（刪除勝於新增、不加多餘抽象層、已知捷徑標註 `// shortcut: <上限>, <升級條件>`），嚴禁未經 A→B→C 多模型會審擅自刪減既有核心邏輯。
- **Phase E（`deepseek-flash` + `jev-1.13.0` + `grok-4.7` + `gemini-4-argon` 聯合驗收）**：
  - 每個任務寫成 `[步驟] → verify: [檢查指令]`，至少跑型別/靜態檢查與相關測試；牽涉前後端串接時要打真實端點。
  - **UI / E2E 驗證與狀態對比**：優先使用全域 CLI `agent-browser`（Web 端）或 `agent-desktop`（Windows 原生視窗/桌面端）執行 `snapshot` 取得 `@ref` 無障礙結構樹進行秒級結構對比（詳見 `agent-desktop` 技能），並由 `gemini-4-argon` 驗收最終 1 張 `screenshot` 存證。
  - 退回 D 時只交「原始目標 + 錯誤輸出 + 出錯檔案」，不帶失敗歷史。

## ⚠️ Gotchas (避坑指南)

- **整合不是投票**：Agent C (`gemini-4-argon` + `qwen-3.8-max`) 要說明為何採用/否決每個紅隊意見，不能只列結論。
- **小任務別硬套**：單檔、低風險的新增微調直接做；但凡涉及**刪減既有架構、合併模組或 >15 行邏輯簡化**，一律強制觸發多模型會審。
- **強制執行真實外部 API 會審 (`multi_model_gate.py`)**：嚴禁只做單模型角色扮演！在 Phase B / Phase E 審查或進行 Ponytail 架構簡化時，必須執行 `python C:\Users\Jiaxing\.gemini\scripts\multi_model_gate.py review --prompt "..." --git-diff --output temp_multi_review.json` 發送真實外部 HTTP Request 給 `deepseek-flash`、`grok-4.7`、`qwen-3.8-max`、`gemini-4-argon` 與 `jev-1.13.0`，並在報告附上各模型回傳的真實 `request_id`。
