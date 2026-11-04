---
name: autojev-model-router
description: "'Use when working with autojev-model-router: Choose among available AI models before an agent task when model quality, cost, la..."
---

# AutoJev Model Router

Use `autojev_route_model` when more than one available model could perform the task and the choice materially affects quality, cost, or latency.

If the tool is unavailable because the AutoJev credential is missing or invalid, direct the user to [https://autojev.ai/settings/apikeys](https://autojev.ai/settings/apikeys). If the user then supplies a key or explicitly asks for local setup, do not echo it: save it in the host's secure credential store, configure AutoJev MCP to retrieve it without putting the raw key in a project or `config.toml`, verify the connection, and report only success or the remaining blocker.

## Prepare the decision

1. Describe the task without including unrelated conversation history.
2. List only models the current environment can actually invoke.
3. Describe each model using known capabilities, relative cost, and relative latency. Do not invent benchmarks.
4. Order the decision priorities and include binding constraints.
5. Set stakes by the consequence of a wrong result.

Call `autojev_route_model`, then use the selected model if it remains available and allowed. A high `escalate.noul` means the selected model should be paired with human review or a second independent check.

Routing is advisory. It does not authorize access to a model, increase budget, or weaken the task's existing verification requirements.

## ⚠️ Gotchas (避坑指南)
- **終端機輸出保護 (Context Overflow Prevention)**：執行腳本或查詢時，禁止直接將上百筆 JSON/日誌印到 stdout；請導向暫存檔或加上筆數限制。
- **零區防禦與 Port 禁令**：修改或執行指令前嚴守工作區邊界，嚴禁綁定或終止保留埠 (8000、5100、3000)。
