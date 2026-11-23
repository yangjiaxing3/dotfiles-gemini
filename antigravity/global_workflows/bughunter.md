---
description: 按需調用本機 Claude-BugHunter 紅隊與漏洞挖掘知識庫（83 skills），不佔常駐技能額度
---

# /bughunter 工作流

1. 知識庫根目錄位於 `C:\Users\Jiaxing\Documents\GitHub\Claude-BugHunter\skills\`（嚴禁全量複製進全域或專案 `.agents/skills/`）。
2. 先依使用者任務需求（如 API 越權、XSS、SSRF、OAuth、偵察、報告驗證），列出或挑選最相關的技能目錄（例如 `bb-methodology`、`redteam-mindset`、`triage-validation`、`evidence-hygiene` 及對應的 `hunt-*` 技能），僅讀取所需 `SKILL.md`。
3. 若在 `/multi-agent-mode` 或 `/swarm` 中執行，請將上述路徑與對應 `hunt-*` 技能名稱直接寫入 Security Worker 的 `brief`，由該 Worker 按需載入並回報可驗證的弱點證據。
