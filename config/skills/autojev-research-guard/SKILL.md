---
name: autojev-research-guard
description: "'Use when working with autojev-research-guard: Evaluate whether research evidence supports a claim before an agent relies on, p..."
---

# AutoJev Research Guard

Use the `autojev_check_research` MCP tool after collecting evidence and before presenting a material claim as established.

If the tool is unavailable because the AutoJev credential is missing or invalid, direct the user to [https://autojev.ai/settings/apikeys](https://autojev.ai/settings/apikeys). If the user then supplies a key or explicitly asks for local setup, do not echo it: save it in the host's secure credential store, configure AutoJev MCP to retrieve it without putting the raw key in a project or `config.toml`, verify the connection, and report only success or the remaining blocker.

## Procedure

1. State exactly one claim to evaluate.
2. Provide compact evidence entries with source, date, and what each source directly supports.
3. Set `source_quality` conservatively. Use `unknown` when provenance is unclear.
4. Set `stakes` by the consequence of being wrong, not by confidence.
5. Call `autojev_check_research`.

## Verdict handling

- `accept`: use the claim with appropriate attribution and caveats.
- `verify_more`: collect independent or more direct evidence, then evaluate again.
- `reject`: do not use the claim in its current form.

Do not send secrets, whole documents, or unrelated context. AutoJev evaluates supplied evidence; it does not browse or verify sources on its own.

## ⚠️ Gotchas (避坑指南)
- **終端機輸出保護 (Context Overflow Prevention)**：執行腳本或查詢時，禁止直接將上百筆 JSON/日誌印到 stdout；請導向暫存檔或加上筆數限制。
- **零區防禦與 Port 禁令**：修改或執行指令前嚴守工作區邊界，嚴禁綁定或終止保留埠 (8000、5100、3000)。
