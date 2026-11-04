---
name: autojev-completion-review
description: "'Use when working with autojev-completion-review: Review whether an agent task is genuinely complete before reporting success..."
---

# AutoJev Completion Review

Use the `autojev_review_completion` MCP tool immediately before declaring a non-trivial objective complete.

If the tool is unavailable because the AutoJev credential is missing or invalid, direct the user to [https://autojev.ai/settings/apikeys](https://autojev.ai/settings/apikeys). If the user then supplies a key or explicitly asks for local setup, do not echo it: save it in the host's secure credential store, configure AutoJev MCP to retrieve it without putting the raw key in a project or `config.toml`, verify the connection, and report only success or the remaining blocker.

## Procedure

1. Restate the original objective without weakening its requirements.
2. List completed work as observable outcomes.
3. List verification actually run, including failures and limitations.
4. List every known gap. Use an empty list only after checking.
5. Call `autojev_review_completion`.

## Verdict handling

- `complete`: report completion and the relevant verification.
- `verify_more`: run the missing checks, then evaluate again.
- `incomplete`: continue the required work or report the concrete blocker.

Never mark work complete merely because time or budget is low. AutoJev is an advisory decision layer; higher-priority instructions and safety requirements still apply.

## ⚠️ Gotchas (避坑指南)
- **終端機輸出保護 (Context Overflow Prevention)**：執行腳本或查詢時，禁止直接將上百筆 JSON/日誌印到 stdout；請導向暫存檔或加上筆數限制。
- **零區防禦與 Port 禁令**：修改或執行指令前嚴守工作區邊界，嚴禁綁定或終止保留埠 (8000、5100、3000)。
