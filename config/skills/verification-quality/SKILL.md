---
name: verification-quality
description: "Use when verifying T2/T3 changes via real-data sampling, fuzzing, CP950/secret scans, and tier_gate pass proofs. 交付品質驗證與獨立複查門禁"
version: "3.0.0"
---

# Verification & Quality Gate SOP（本機確定性交付驗收）

> 目的：取代無法本機執行的外部 CLI 幻想，用**可重現、零自嗨、防偽造**的四層實證驗收 T2/T3 變更，終結「作者只用自寫 Mock 宣告 PASS」。

## Step 1：機械定級與靜態防線（`tier_gate.py` + `rule_lint.py`）

先確認變更分級與靜態門禁（無 `scripts/` 則改用 `~/.gemini/scripts/`）：

```bash
# 1. 計算規模 × 風險分級與 prod_diff_fingerprint（非 Git 目錄改用 --files <paths...>）
python3 scripts/tier_gate.py assess --git-diff --format json

# 2. 靜態規則檢查（攔截 UI Emoji、.skip、空 catch、裸 bool(str)、缺 UTF-8、密鑰字面值）
python3 scripts/rule_lint.py --git-diff
```

- **T0 / T1**：跑既有單測與型別檢查（T1 必補 `>= 1` 失敗邊界案例），即可放行。
- **T2 / T3**：強制進入下方 Step 2–5，缺一即視為未驗收。

## Step 2：真實資料抽核（Real-Data Sampling，禁純 Mock）

作者自寫 Mock 只能驗證「作者以為的輸入」。T2/T3 必須對**真實語料**端對端實跑並揭露量化指標：

| 變更類型 | 必跑真實資料抽核動作 | 必揭露量化指標 |
| :--- | :--- | :--- |
| **Parser / Indexer / 規則引擎** | 抽樣或全量實跑本倉 / 目標目錄真實檔案（如近 30 筆 commits、真實 `.md`/`.yaml`/`.dxf`） | 總筆數、命中率、誤報率、0 崩潰筆數 |
| **Backend API / SQL / Schema** | 對本機 SQLite/Turso 測試庫或真實 fixture 執行完整 CRUD / 查詢契約 | 欄位吻合數、邊界狀態碼、無越權寫入 |
| **Frontend UI / 互動流程** | 透過 `agent-desktop` / `e2e` 或 `tsc --noEmit` + `vitest` 驗證真實渲染與表單狀態 | console error 數（必為 0）、型別錯誤數 |

## Step 3：對抗邊界 Fuzz 測試（Adversarial Edge Cases，`>= 5` 例）

針對新增或修改的解析、驗證、API、計算入口，至少實測以下 **5 類對抗輸入**（須納入自動化測試或獨立驗證腳本）：

1. **型別欺騙**：字串 `"false"`、`"0"`、`""` 傳入布林／數值欄位（嚴防 `bool("false") is True`）。
2. **空值與缺欄**：`None` / `null` / 空陣列 / 空物件 / 缺失必填鍵 / 重複鍵。
3. **路徑與注入**：`../` 路徑穿越、含空白或中文路徑、SQL/Shell 特殊字元。
4. **極端邊界**：0、負數、超大數值、超長字串、重複提交（冪等性）。
5. **毀損輸入**：截斷 JSON、非法 UTF-8 位元組、BOM (`\ufeff`) 與 `CRLF` 混用。

## Step 4：Windows CP950 編碼實測 × 密鑰／PII 掃描

- **Windows CP950 條件實測**（凡異動 Python CLI / MCP / 檔案讀寫腳本必跑；純 React/TS 前端免跑）：
  ```powershell
  $env:PYTHONIOENCODING="cp950"
  backend\.venv\Scripts\python.exe <target_script.py> <smoke_args>
  Remove-Item Env:PYTHONIOENCODING
  ```
  確認輸出含繁體中文或特殊符號時**不會拋出 `UnicodeEncodeError`**，且所有文字檔 `open()`/`.read_text()`/`.write_text()` 顯式指定 `encoding="utf-8"`（二進位模式除外）。
- **密鑰與 PII 零外洩掃描**：
  - 確認 `rule_lint.py --git-diff` 針對 `SECRET_LITERAL_GUARD` 為 **0 error**。
  - 若變更會產出 SQLite DB、JSON 快取、Log 或報表，抽檢輸出產物確認 **0 明文 API Key / Token / 私鑰頭 / 內部 salt / 真實客戶個資**。

## Step 5：獨立複查憑證與 `verify-pass` 落鎖

1. **外部異質多模型會審**：
   ```bash
   # T2（一般異質會審）；T3 加上 --include-grok-api
   python3 scripts/multi_model_gate.py review --prompt "<變更目的>" --git-diff --output temp_multi_review.json
   ```
   - 裁決為 `PASS` 或 `PASS_DEGRADED`（外部 API 故障且滿足 `>=2` 異質供應商 + 0 紅燈 + 異質紅隊補位）時，腳本會自動寫入 `lean_triad_gate_pass.json`。
2. **獨立唯讀複查（作者隔離）**：
   - **T2**：至少 1 名獨立唯讀複查者（Swarm `board#seq` 且 `agent != author`，或獨立 Subagent ID）。
   - **T3**：啟動 `stage-gate-review` 3 角色唯讀審查（邏輯破壞者 / 真實語料稽核者 / 對抗 Fuzz 與資安測試者），收斂至 **0 CRITICAL / 0 HIGH**。
3. **最終憑證核驗**：
   ```bash
   python3 scripts/tier_gate.py verify-pass --git-diff
   ```
   確認 `prod_diff_fingerprint` 吻合、無偷刪測試斷言、具真實外部 `request_id`（非 `cursor-plan-delegated` / `unknown`），將 `tier_token`、`req`、`review` 與 `pass` 路徑如實填入 `🛡️ Lean-Triad` 回條。

## ⚠️ Gotchas (避坑指南)
- **嚴禁同 Context 自演獨立複查**：同一位寫碼 Agent 不得自稱「已完成獨立複查」，亦不得以 `cursor-plan-delegated` 或 `unknown` 充當外部 `request_id`。
- **嚴禁過 Gate 後偷刪測試斷言**：`tier_gate.py verify-pass` 會比對 `test_integrity_snapshot`；補寫測試免重跑會審，但刪除斷言或加 `.skip` 會直接攔截。
- **終端機輸出保護 (Context Overflow Prevention)**：跑大量真實資料抽核或 diff 檢查時，禁止將整批 JSON 或日誌直接印到 stdout；請導向暫存檔並只輸出統計摘要。
- **嚴禁 AI 自填 Break-Glass**：`LEAN_TRIAD_BYPASS_REASON` 僅限人類於全斷網緊急止血時手動設定，AI Agent 絕不可自行注入該環境變數繞過門禁。
