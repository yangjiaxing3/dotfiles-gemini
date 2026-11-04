---
name: meta-tags-optimizer
description: "Use when rewriting Title tags, Meta descriptions, and Open Graph tags to maximize SERP click-through rate (CTR). Title與Meta標籤優化/提升點擊率"
version: "9.9.10"
license: Apache-2.0
compatibility: "Claude Code and compatible agent-skill hosts"
---

# Meta Tags Optimizer

Creates title tags, meta descriptions, and social meta tags that improve CTR and sharing quality.

## Quick Start

```
Create meta tags for a page about [topic] targeting [keyword]
```

```
Improve these meta tags for better CTR: [current tags]
```

## Skill Contract

**Expected output**: a ready-to-use metadata package plus the standard handoff summary for `memory/content/`.

- **Reads**: the brief, target keywords, entity inputs, and quality constraints.
- **Writes**: a user-facing metadata deliverable and reusable summary.
- **Promotes**: approved angles, messaging choices, missing evidence, and publish blockers to `memory/hot-cache.md` and `memory/open-loops.md`; propose durable decisions as pending-decision items.
- **Done when**: three title and three description options are provided within the character limits with the keyword front-loaded; a complete OG/Twitter tag block is included; and C01 (Intent Alignment) and C02 (Direct Answer) pass.
- **Primary next skill**: [schema-markup-generator](https://github.com/aaron-he-zhu/seo-geo-claude-skills/blob/main/build/schema-markup-generator/SKILL.md) when the metadata package is ready for structured-data support.

### Handoff Summary

> Emit the standard shape from [skill-contract.md §Handoff Summary Format](https://github.com/aaron-he-zhu/seo-geo-claude-skills/blob/main/references/skill-contract.md).

## Data Sources

Optional search console and SEO tool integrations pull CTR data and competitor patterns automatically; otherwise ask for current tags, keywords, and competitors. See [CONNECTORS.md](https://github.com/aaron-he-zhu/seo-geo-claude-skills/blob/main/CONNECTORS.md).

## Instructions

When a user requests meta-tag optimization, run these six steps:

1. **Gather Page Information** — URL, page type, primary and secondary keywords, audience, CTA, and value proposition.
2. **Create Optimized Title Tag** — keep it near 50-60 characters, front-load the keyword, and generate three options using the supported title formulas.
3. **Write Meta Description** — target 150-160 characters, include the keyword and CTA, and generate three options.
4. **Create Open Graph, Twitter Card, and Additional Meta Tags** — include OG, Twitter, canonical, robots, viewport, author, and article tags as needed.
5. **CORE-EEAT Alignment Check** — verify C01 (Intent Alignment) and C02 (Direct Answer).
6. **Provide CTR Optimization Tips** — explain the winning elements, tradeoffs, and A/B test options.

Label every metric **Measured** (tool/export), **User-provided**, or **Estimated** (model inference); never present an estimate as measured; if a required metric is unavailable, mark it N/A — do not invent it.

> **Reference**: See [Instructions Detail](https://github.com/aaron-he-zhu/seo-geo-claude-skills/blob/main/build/meta-tags-optimizer/references/instructions-detail.md) for the compact workflow, formulas, alignment matrix, CTR analysis, and example. See [Meta Tag Code Templates](https://github.com/aaron-he-zhu/seo-geo-claude-skills/blob/main/build/meta-tags-optimizer/references/meta-tag-code-templates.md) for HTML blocks.

## Example

Sample outcome: a 55-character title, a 150-160 character description, and a complete OG / Twitter / Article tag block. See the full worked sample in [Instructions Detail — Example](https://github.com/aaron-he-zhu/seo-geo-claude-skills/blob/main/build/meta-tags-optimizer/references/instructions-detail.md#example).

## Tips for Success

Front-load keywords, match intent, be specific, test variations, and refresh tags when the SERP changes.

### Save Results

On user confirmation, save to `memory/content/YYYY-MM-DD-<topic>.md` — see [Skill Contract](https://github.com/aaron-he-zhu/seo-geo-claude-skills/blob/main/references/skill-contract.md) §Save Results Template.

## Reference Materials

- [Instructions Detail](https://github.com/aaron-he-zhu/seo-geo-claude-skills/blob/main/build/meta-tags-optimizer/references/instructions-detail.md) — Workflow, formulas, alignment matrix, example
- [Meta Tag Formulas](https://github.com/aaron-he-zhu/seo-geo-claude-skills/blob/main/build/meta-tags-optimizer/references/meta-tag-formulas.md) — Title and description formulas
- [Meta Tag Code Templates](https://github.com/aaron-he-zhu/seo-geo-claude-skills/blob/main/build/meta-tags-optimizer/references/meta-tag-code-templates.md) — HTML templates
- [CTR and Social Reference](https://github.com/aaron-he-zhu/seo-geo-claude-skills/blob/main/build/meta-tags-optimizer/references/ctr-and-social-reference.md) — CTR patterns and social guidance

## Next Best Skill

- **Primary**: [schema-markup-generator](https://github.com/aaron-he-zhu/seo-geo-claude-skills/blob/main/build/schema-markup-generator/SKILL.md) — complete the SERP package with structured data.

## ⚠️ Gotchas (避坑指南)
- **避免關鍵字堆砌與門頁懲罰 (Doorway Pages)**：多據點或多機型頁面必須結合在地真實數據（如實收租金、分店地標、真實檢測數據），禁止僅替換地名或機型名稱。
- **Schema 與畫面一致性**：產出的 JSON-LD (`FAQPage`, `LocalBusiness`, `Product`) 內容必須與頁面可見文字 100% 一致，否則會觸發 Google 結構化資料人工處罰。
