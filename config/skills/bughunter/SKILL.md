---
name: bughunter
description: Use when running red-team security audits, API auth checks, or bug hunting via local Claude-BugHunter vault. 紅隊漏洞挖掘/資安稽核
---

# bughunter

按需調用本機 `C:\Users\Jiaxing\Documents\GitHub\Claude-BugHunter\skills\`（83 個紅隊與漏洞挖掘技能），**嚴禁**全量複製進全域或專案目錄。

1. 依目標需求挑選對應技能（如 `bb-methodology`、`redteam-mindset`、`triage-validation`、`evidence-hygiene` 及對應 `hunt-*`），僅讀取所需 `SKILL.md`。
2. 在 `/multi-agent-mode` 或 `/swarm` 中，將該路徑與所需 `hunt-*` 技能名寫入 Security Worker 的 `brief`。

## ⚠️ Gotchas (避坑指南)

- 僅可對授權目標或本機開發環境進行測試，嚴禁未授權對外掃描。
