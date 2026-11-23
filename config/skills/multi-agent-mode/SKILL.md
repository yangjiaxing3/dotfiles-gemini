---
name: multi-agent-mode
description: "Use when tasks need Neon XHigh/Carbon High planning & Hydrogen XHigh execution loop. 多Agent模式/紅隊辯證/multi-agent"
---

# 多 Agent 模式（Neon XHigh 協調定計 ⇄ Hydrogen XHigh 平行執行測試 × 動態重規劃）

原則：**對齊 Antigravity Orchestrator 官方協作設計，拒絕憑第一個 Prompt 鎖死低配靜態路由**。預設由 **`gemini-4-neon-xhigh`**（Extra High mode）擔任 Planner（協調者）統籌探索定計與重規劃（僅純輕量文案／錯字／省額度情境可改選 **`gemini-4-carbon-high`** High mode），搭配速度極快、成本最低的 **`gemini-4-hydrogen-xhigh`**（Extra High mode）作為 Executor 平行讀取檔案、改碼與跑測試；遇阻立即交回 Phase A 修補計畫。切換角色時標示：`### 🤖 Agent [X]（[模型]）：[角色]`。全程繁體中文。

## 動態執行流程（Plan ⇄ Execute ⇄ Re-plan Loop）

| Phase | 角色 | 主力模型 (`--model`) | 核心職責與階段轉換 | 停止 / 交回條件 |
| :--- | :--- | :--- | :--- | :--- |
| **0** | 🛡️ 邊界守門 | **`deepseek-flash`** | 亞秒級檢查工作區邊界與授權白名單（**不做靜態難度猜測外包**） | 越界或未授權跨庫 → 停止請求授權 |
| **A** | 🧠 唯讀定計與重規劃 | 預設主力：**`gemini-4-neon-xhigh`**（Extra High mode）<br/>輕量可選：**`gemini-4-carbon-high`**（High mode） | **唯讀協調階段**：預設以 `Neon XHigh` 統籌架構、查 `graphify`/依賴鏈並拆派任務（純輕量文案／單點微調可選 `Carbon High`），明訂 **Re-plan Triggers** 與禁區 | 計畫與觸發條件完成 → B（高風險）或 C（低風險） |
| **B** | 😈 紅隊 ＋ 裁決 *(門禁觸發)* | **`grok-4.7` (Cursor Plan)** ＋ **Gemini Decision API** *(與 `jev-1.13.0` 雙軌；備案 **`qwen4-max`**)* | 僅當 `>=3` 檔、刪架構/`>15` 行、相機/金流/3D 公式/資安時啟動：Grok 攻 6 維度，Decision API 吐結構化 JSON 燈號 | 非 🔴 且高風險已獲使用者確認 → C；🔴 → 回 A 修補計畫 |
| **C** | 🛠️ 主力執行與測試 | **`gemini-4-hydrogen-xhigh`**（Extra High mode；額度不足備案 **`qwen4-max`**） | 發揮高速低成本優勢，平行讀檔、依 Phase A 計畫改碼、更新套件、執行測試與實機驗證 | **觸發 Re-plan Trigger** → 立即停手交回 **A (`Neon XHigh`/`Carbon High`)** 修補計畫 |
| **D** | 🔍 規格核對與終審放行 | **`qwen4-max`** *(備案 **`qwen4-max-preview`** / **`deepseek-flash`**)* ＋ **Gemini Decision API** | **Qwen / Flash**：逐條核對 100% 規格未縮水並確認最終測試輸出<br/>**Decision API**：高風險任務輸出終審 `PASS / BLOCK` | PASS → `walkthrough.md`；FAIL → 回 A 重估或 C 修正（最多 2 輪） |

## Re-plan Triggers（Hydrogen 必須停手交回 Phase A 的條件）

1. **隱藏依賴浮現**：發現計畫外之跨模組依賴、API 契約不合或必須改動未授權檔案。
2. **環境/套件假設失效**：更新套件、編譯環境或外部服務回應與唯讀探索時不符。
3. **執行連敗 2 次**：同一錯誤或測試連續失敗 **2 次**（嚴禁在執行層繼續瞎猜，交回 Phase A（`Neon XHigh` / `Carbon High`）檢視現狀修補計畫；若為重度演算法/跨檔硬骨頭，重規劃後可指派 `qwen4-max` 接手）。
4. **逼近受保護禁區**：實作時發現可能傷及 3D 幾何、計價毛利、雜湊鏈或只作廢不刪除規則。

## ⚠️ Gotchas (避坑指南)

- **禁止靜態單一廉價外包**：不可只看第一句 Prompt 就把整條長程任務直接鎖死在最便宜模型；低風險也須經唯讀釐清再動手。
- **Hydrogen 遇阻不硬幹**：觸發任何 Re-plan Trigger 必須交回 Phase A（`gemini-4-neon-xhigh` / `gemini-4-carbon-high`）檢視現狀並修補計畫，不可原地重試超過 2 次。
- **禁止單票 JEV 覆蓋與假綠燈**：門禁腳本採「一模型一票」統計散文燈號，多數 `🔴` 或紅隊失敗／200s 逾時（Option B）強制輸出 `BLOCK`；未傳 `--include-grok-api` 時 `Agent B` 標記為 `delegated_to_ide`，不計入實跑通過率。
- **模型路由鐵律 (`multi_model_gate.py`)**：
  1. `grok` 預設委派 IDE 子代理 (`delegated_to_ide`)；當加上 `--include-grok-api` 或 `grok-x` 時，**第一順位（免 API 費）**呼叫 `grok.exe --permission-mode plan`（強制鎖定 `tempdir`、25KB 摘要、`--max-turns 2`、200s 逾時即觸發 Option B 阻斷）。
  2. Gemini（Phase A `Neon XHigh` / `Carbon High`、Phase C `Hydrogen XHigh`、`Decision`）預設**第一順位（免 API 費）**清空子程序 `GEMINI_API_KEY` / `GOOGLE_API_KEY`，呼叫 `agy.exe --mode plan`（注入唯讀禁工具守門）走 Antigravity Plan 訂閱額度；失敗時退回 `GEMINI_API_KEY` 直打公式 API。
  3. `qwen4-max` 採金鑰網域 1:1 鎖定：`sk-sp-...` MaaS 專鑰僅走 `token-plan.maas`（預設 `thinking_budget=2048` / `max_tokens=12288`，遇空轉關 thinking 重試），嚴禁跨網域送至 DashScope；直連全敗後才走 OpenRouter。
