---
description: "跨語言測試規範，含 TDD 流程、測試結構、命名慣例（適用 Vitest / pytest）"
globs: ["**/*.test.*", "**/*.spec.*", "**/test_*", "**/__tests__/**", "**/tests/**"]
---

# 測試規範

## TDD 流程與自動化迴圈 (Autonomous Loop)

- 遵循 RED → GREEN → REFACTOR 循環
- **自動化執行**：撰寫測試與實作代碼後，AI 必須主動執行 `run_command` (例如 `npm test` 或 `pytest`)，自行讀取錯誤並修復。
- **邊界限制 (Bounded Loop)**：最多自我循環 5 次。若超過上限或連續出現同樣的錯誤 2 次，必須立即中止，不允許盲猜。
- **防作弊機制 (Anti-Cheating)**：嚴禁為了通過測試而刪除斷言 (assertions)、弱化驗證條件或使用 `@skip`。

## 測試結構

- 每個測試使用 AAA 模式：Arrange（準備）→ Act（執行）→ Assert（驗證）
- 一個測試只驗證一個行為，避免巨型測試函式
- 測試描述用自然語言，清楚表達「什麼情境下、預期什麼結果」

## 命名慣例

- 前端測試檔：`*.test.tsx` / `*.test.ts`（與元件同名）
- 後端測試檔：`test_*.py`（與模組同名，前綴 `test_`）
- 測試函式命名：`test_<行為>_<情境>_<預期結果>`

## Mock 與隔離

- 外部依賴（API、資料庫）一律 Mock，不做真實呼叫
- 共用的 Mock 資料抽離為 fixture / factory
- 避免測試之間互相依賴或共享狀態

## 覆蓋率

- 核心業務邏輯的測試覆蓋率應 ≥ 80%
- 邊界條件與錯誤路徑必須有對應測試
