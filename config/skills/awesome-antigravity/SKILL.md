---
name: awesome-antigravity
description: "Use when looking up Antigravity IDE agent personas, mission templates, and troubleshooting patterns. Antigravity代理模板與排錯指南"
---

# Awesome Antigravity

This skill provides access to the Awesome Antigravity guide and resources.

## ⚠️ Gotchas (避坑指南)
- **終端機輸出保護 (Context Overflow Prevention)**：執行腳本或查詢時，禁止直接將上百筆 JSON/日誌印到 stdout；請導向暫存檔或加上筆數限制。
- **優先使用確定性腳本**：遇到格式轉換、字數統計或合規檢查，優先調用 `scripts/` 下的 Python 工具，不要依賴純語意猜測。
