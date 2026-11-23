---
description: 按需調用進階 SEO、Google Ads、GA4、GSC 與關鍵字／競品分析技能，不佔常駐額度
---

# /storeasy-seo 工作流

1. 依任務類型前往 `~/.gemini/config/skills/` 按需讀取對應技能：
   - **Google Ads / GA4 / GSC 診斷**：`notfair-google-ads-audit/SKILL.md`、`notfair-seo-analysis/SKILL.md`
   - **關鍵字與內容缺口**：`keyword-research/SKILL.md`、`keyword-clustering/SKILL.md`、`content-gap-analysis/SKILL.md`、`serp-analysis/SKILL.md`
   - **站內連結與權重／外鏈**：`internal-linking-optimizer/SKILL.md`、`backlink-analyzer/SKILL.md`、`competitor-analysis/SKILL.md`
   - **舊文翻新與排名追蹤**：`content-refresher/SKILL.md`、`rank-tracker/SKILL.md`、`seo-drift/SKILL.md`
2. 若搭配 `/swarm` 或 `/multi-agent-mode`，將所需技能路徑寫入對應 Worker 的 `brief` 中按需載入。
