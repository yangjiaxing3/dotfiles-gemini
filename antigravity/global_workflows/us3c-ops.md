---
description: 按需調用 US3C 二手回收、iMCheck 質檢、機台巡檢與社群輿情技能，不佔常駐額度
---

# /us3c-ops 工作流

1. 依任務類型前往 `~/.gemini/config/skills/` 按需讀取對應技能（嚴禁全量複製進專案）：
   - **驗機與黑名單**：`us3c-imcheck-device-qc/SKILL.md`
   - **24H 回收機台與司機端**：`us3c-kiosk-driver-ops/SKILL.md`、`kiosk-image-optimizer/SKILL.md`
   - **估價定價與毛利**：`us3c-tradein-margin-pricing/SKILL.md`
   - **SEO 飛輪與社群輿情**：`us3c-seo-loop/SKILL.md`、`agent-reach/SKILL.md`、`social-listening-brief/SKILL.md`
2. 若搭配 `/swarm` 或 `/multi-agent-mode`，將所需技能路徑寫入對應 Worker 的 `brief` 中按需載入。
