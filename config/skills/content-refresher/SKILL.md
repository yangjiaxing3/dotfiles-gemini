---
name: content-refresher
description: "Use when updating decaying or outdated articles to recover lost organic rankings and refresh GEO signals. 舊文翻新與流量衰退排名恢復"
version: "9.9.10"
license: Apache-2.0
compatibility: "Claude Code and compatible agent-skill hosts"
---

# Content Refresher

Identifies outdated content, scores decay/freshness, prioritizes refresh work, and produces update plans with GEO and republishing guidance.

## Quick Start

```text
Find content on [domain] that needs refreshing
Which of my blog posts have lost the most traffic?
Refresh this article for [current year]: [URL/content]
Update this content to outrank [competitor URL]: [your URL]
Create a content refresh strategy for [domain/topic]
```

## Skill Contract

**Expected output**: a scored diagnosis, prioritized repair plan, and a short handoff summary ready for `memory/audits/`.

- **Reads**: candidate URLs/content, traffic and ranking history, publish/update dates, and competitor examples.
- **Writes**: a user-facing refresh plan (and optional refreshed content) plus a reusable summary that can be stored under `memory/audits/`.
- **Promotes**: blocking defects, repeated weaknesses, fix priorities, and pending decisions to `memory/open-loops.md`.
- **Done when**: decay drivers are identified with evidence; a refresh plan lists specific updates with a republish-date strategy; a Changes Made block and handoff summary are produced.
- **Primary next skill**: use the `Next Best Skill` below when the repair path is clear.

### Handoff Summary

> Emit the standard shape from [skill-contract.md §Handoff Summary Format](https://github.com/aaron-he-zhu/seo-geo-claude-skills/blob/main/references/skill-contract.md).

## Data Sources

Use ~~analytics, ~~search console, and ~~SEO tool when connected; otherwise ask for traffic data, ranking history, publish dates, candidate URLs, and competitor examples. See [CONNECTORS.md](https://github.com/aaron-he-zhu/seo-geo-claude-skills/blob/main/CONNECTORS.md).

## Instructions

Label every metric **Measured** (tool/export), **User-provided**, or **Estimated** (model inference); never present an estimate as measured; if a required metric is unavailable, mark it N/A — do not invent it.

When a user requests content refresh help:

1. **CORE-EEAT Quick Score** — Estimate all 8 dimensions, prioritize red/yellow areas, and hand off to [content-quality-auditor](https://github.com/aaron-he-zhu/seo-geo-claude-skills/blob/main/cross-cutting/content-quality-auditor/SKILL.md) for full scoring when needed.
2. **Identify Refresh Candidates** — Use age, dated claims, declining traffic, lost rankings, broken links, SERP shifts, and missing topics.
3. **Analyze Page-Level Decay** — Compare 6-month-old vs current performance, keyword deltas, SERP intent, competitor updates, and the why-refresh rationale.
4. **Define Updates Needed** — Capture outdated elements, competitor/PAA gaps, SEO updates, GEO updates, links, images, sources, and dates.
5. **Create Refresh Plan** — Specify title, structure, new sections, refreshed statistics, internal/external links, images, and validation requirements.
6. **Write Refresh Content** — Draft updated intro, replacement sections, refreshed facts, FAQ answers, and Changes Made notes.
7. **Optimize for GEO** — Add 40-60 word definitions, quotable statements, Q&A, dated citations, and standalone factual statements.
8. **Set Republishing Strategy** — Use published-date update for 50%+ new content, last-updated date for 20-50%, original date for <20%; update schema, sitemap `lastmod`, cache, Search Console, and 4-6 week monitoring.
9. **Create Refresh Report** — Summarize completed changes, expected outcomes, owners, next review date, and open loops.

> **Reference**: [references/refresh-templates.md](https://github.com/aaron-he-zhu/seo-geo-claude-skills/blob/main/optimize/content-refresher/references/refresh-templates.md) has compact templates for steps 2-9.

## Decision Gates

**Stop and ask the user when:**
- A page is decayed enough that a rewrite may beat a refresh (e.g., outdated premise, intent shift, or >50% of content stale) — state the finding and ask: (1) refresh in place, or (2) rewrite as new content via [seo-content-writer](https://github.com/aaron-he-zhu/seo-geo-claude-skills/blob/main/build/seo-content-writer/SKILL.md).

**Continue silently (never stop for):**
- Missing analytics/ranking history — score decay from on-page signals (dated claims, broken links, stale stats), label findings Estimated, and proceed.
- A request to "refresh" content that is actually net-new (no existing URL) — note the mismatch once and route to [seo-content-writer](https://github.com/aaron-he-zhu/seo-geo-claude-skills/blob/main/build/seo-content-writer/SKILL.md) rather than fabricating a prior version.
- Which republish-date treatment to apply — follow the Step 8 thresholds without asking.

## Example

**User**: "Refresh my blog post about 'best cloud hosting providers'"

**Output**: CORE-EEAT quick score flags weak Referenceability, Experience, and Trust; recommends pricing refresh, broken-link fixes, author credential additions, affiliate disclosure, and a Changes Made block ready for republish.

> **Reference**: See [references/refresh-example.md](https://github.com/aaron-he-zhu/seo-geo-claude-skills/blob/main/optimize/content-refresher/references/refresh-example.md) for the full worked example and checklist.

## Tips for Success

Prioritize by ROI/search demand, make substantive improvements instead of date-only edits, add stronger evidence than competitors, track post-publish rankings/traffic, and treat every refresh as a GEO citation opportunity.

> **Reference data**: [references/content-decay-signals.md](https://github.com/aaron-he-zhu/seo-geo-claude-skills/blob/main/optimize/content-refresher/references/content-decay-signals.md) covers decay signals, lifecycle stages, refresh-vs-rewrite decisions, and content-type strategy.

### Save Results

Ask to save results; if yes, write a dated summary to `memory/audits/content-refresher/YYYY-MM-DD-<topic>.md`. Hand off veto-level risks to the auditor gate before any hot-cache marker.

**Gate check recommended**: Run content-quality-auditor on refreshed content before republishing.

## Reference Materials

- [Content Decay Signals](https://github.com/aaron-he-zhu/seo-geo-claude-skills/blob/main/optimize/content-refresher/references/content-decay-signals.md) — Decay indicators, lifecycle stages, and refresh triggers by content type
- [Refresh Templates](https://github.com/aaron-he-zhu/seo-geo-claude-skills/blob/main/optimize/content-refresher/references/refresh-templates.md) — Compact templates for steps 2-9
- [Refresh Example & Checklist](https://github.com/aaron-he-zhu/seo-geo-claude-skills/blob/main/optimize/content-refresher/references/refresh-example.md) — Full worked example and pre/post-refresh checklist

## Next Best Skill

Primary: [content-quality-auditor](https://github.com/aaron-he-zhu/seo-geo-claude-skills/blob/main/cross-cutting/content-quality-auditor/SKILL.md) — re-score refreshed content before shipping.

## ⚠️ Gotchas (避坑指南)
- **避免關鍵字堆砌與門頁懲罰 (Doorway Pages)**：多據點或多機型頁面必須結合在地真實數據（如實收租金、分店地標、真實檢測數據），禁止僅替換地名或機型名稱。
- **Schema 與畫面一致性**：產出的 JSON-LD (`FAQPage`, `LocalBusiness`, `Product`) 內容必須與頁面可見文字 100% 一致，否則會觸發 Google 結構化資料人工處罰。
