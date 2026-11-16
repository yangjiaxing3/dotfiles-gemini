---
name: multi-agent-mode
description: "Use when tasks need Carbon planning & Hydrogen execution/re-plan loop with Grok/Flash/Gemini Decision API. 多Agent模式/紅隊辯證/multi-agent"
---

# 多 Agent 模式（Carbon 唯讀定計 ⇄ Hydrogen 執行測試 × 動態重規劃）

原則：**拒絕憑第一個 Prompt 猜難度的靜態路由**。改採階段式動態接力：先由 **`gemini-4-carbon`** 唯讀探索並定出附「重新規劃觸發條件」的計畫，再交由 **`gemini-4-hydrogen`** 執行改碼、裝套件與測試；遇阻立即交回 Carbon 檢視現狀並修補計畫。切換角色時標示：`### 🤖 Agent [X]（[模型]）：[角色]`。全程繁體中文。

## 動態執行流程（Plan ⇄ Execute ⇄ Re-plan Loop）

| Phase | 角色 | 主力模型 (`--model`) | 核心職責與階段轉換 | 停止 / 交回條件 |
| :--- | :--- | :--- | :--- | :--- |
| **0** | 🛡️ 邊界守門 | **`deepseek-flash`** | 亞秒級檢查工作區邊界與授權白名單（**不做靜態難度猜測外包**） | 越界或未授權跨庫 → 停止請求授權 |
| **A** | 🧠 唯讀定計與重規劃 | **`gemini-4-carbon`** | **唯讀階段**：查 `graphify`/依賴鏈、釐清模糊點，建立計畫並明訂 **Re-plan Triggers** 與受保護禁區 | 計畫與觸發條件完成 → B（高風險）或 C（低風險） |
| **B** | 😈 紅隊 ＋ 裁決 *(門禁觸發)* | **`grok-4.7` (Cursor Plan)** ＋ **Gemini Decision API** *(與 `jev-1.13.0` 雙軌；額度不足備案 **`qwen4-max-preview`**)* | 僅當 `>=3` 檔、刪架構/`>15` 行、相機/金流/3D 公式/資安時啟動：Grok 攻 6 維度，Decision API 吐結構化 JSON 燈號 | 非 🔴 且高風險已獲使用者確認 → C；🔴 → 回 A 修補計畫 |
| **C** | 🛠️ 主力執行與測試 | **`gemini-4-hydrogen`** *(額度不足／極端重構備案 **`qwen4-max-preview`**)* | 依 Carbon 計畫改碼、更新套件、執行測試與實機驗證 | **觸發 Re-plan Trigger** → 立即停手交回 **A (`Carbon`)** 修補計畫 |
| **D** | 🔍 規格核對與終審放行 | **`qwen4-max-preview`** *(備案 **`deepseek-flash`**)* ＋ **Gemini Decision API** | **Qwen / Flash**：逐條核對 100% 規格未縮水並確認最終測試輸出<br/>**Decision API**：高風險任務輸出終審 `PASS / BLOCK` | PASS → `walkthrough.md`；FAIL → 回 A 重估或 C 修正（最多 2 輪） |

## Re-plan Triggers（Hydrogen 必須停手交回 Carbon 的條件）

1. **隱藏依賴浮現**：發現計畫外之跨模組依賴、API 契約不合或必須改動未授權檔案。
2. **環境/套件假設失效**：更新套件、編譯環境或外部服務回應與唯讀探索時不符。
3. **執行連敗 2 次**：同一錯誤或測試連續失敗 **2 次**（嚴禁在執行層繼續瞎猜，交回 `Carbon` 檢視現狀修補計畫；若為重度演算法/跨檔硬骨頭，Carbon 重規劃後可指派 `qwen-max` 接手）。
4. **逼近受保護禁區**：實作時發現可能傷及 3D 幾何、計價毛利、雜湊鏈或只作廢不刪除規則。

## ⚠️ Gotchas (避坑指南)

- **禁止靜態單一廉價外包**：不可只看第一句 Prompt 就把整條長程任務直接鎖死在最便宜模型；低風險也須經唯讀釐清再動手。
- **Hydrogen 遇阻不硬幹**：觸發任何 Re-plan Trigger 必須交回 `gemini-4-carbon` 檢視現狀並修補計畫，不可原地重試超過 2 次。
- **勿用散文猜燈號取代 Decision API**：門禁放行一律以結構化 `traffic_light` / `protected_harm` / `spec_shrink` 為準（`scripts/multi_model_gate.py` 支援 `gemini_decision_direct` 與 TypeSafe JEV 雙軌）。
- **模型路由鐵律 (`multi_model_gate.py`)**：
  1. `grok` 走 Cursor Plan 內建額度；當需在外部 CLI / 腳本呼叫 Grok（含搜 X.com 貼文或 `--include-grok-api`）時，**第一順位（免 API 費）**呼叫 `grok.exe -p ... [--json-schema ...] --permission-mode plan` 並自動清空子程序 `XAI_API_KEY`，強制讀取 `~/.grok/auth.json` 走 Grok Plan 訂閱額度；**第二順位（備援）**僅在本機未登入 `~/.grok/auth.json` 時才退回 `XAI_API_KEY`。
  2. Gemini（`Carbon` / `Hydrogen` / `Decision`）預設**第一順位（免 API 費）**清空子程序 `GEMINI_API_KEY` / `GOOGLE_API_KEY`，呼叫 `agy.exe --mode plan` 走 Antigravity Plan 訂閱額度；除非明確指定 `--force-gemini-api`（或 `FORCE_GEMINI_API=1`）或 Plan 未登入／Quota 不足失敗時，才退回**第二順位**讀取 Windows DPAPI 的 `GEMINI_API_KEY` 直打官方 API（`gemini_direct`）。
  3. 其他直打官方 API（`deepseek_direct`, `qwen_direct`, `typesafe`）及上述第二順位全部失敗後，才走 OpenRouter。
  4. Qwen 優先使用 `qwen4-max-preview`（DashScope 直連優先，支援 `qwen-max` 與 OpenRouter 備援）。
