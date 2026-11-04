---
name: seo-google
description: "Use when tasks involve seo google: 'Google SEO APIs: Search Console (Search Analytics, URL Inspection, Sitemaps), PageSpeed Ins..."
license: MIT
version: "2.2.4"
---

# Google SEO APIs

Direct access to Google's own SEO data. Bridges the gap between crawl-based
analysis (existing claude-seo skills) and Google's real-time field data: actual
Chrome user metrics, real indexation status, search performance, and organic traffic.

All APIs are free. Setup requires a Google Cloud project with API key and/or
service account -- run `/seo google setup` for step-by-step instructions.

## Prerequisites

Before executing any command, check credentials:
```bash
"$HOME/.claude/skills/seo/bin/claude-seo" run google_auth.py --check --json
```

Config file: `~/.config/claude-seo/google-api.json`
```json
{
  "service_account_path": "/path/to/service_account.json",
  "api_key": "<GOOGLE_API_KEY>",
  "default_property": "sc-domain:example.com",
  "ga4_property_id": "properties/123456789"
}
```

If missing, read `references/auth-setup.md` and walk the user through setup.

### Credential Tiers

| Tier | Detection | Available Commands |
|------|-----------|-------------------|
| **0** (API Key) | `api_key` present | `pagespeed`, `crux`, `crux-history`, `youtube`, `nlp` |
| **1** (OAuth/SA) | + OAuth token or service account | Tier 0 + `gsc`, `inspect`, `sitemaps`, `index` |
| **2** (Full) | + `ga4_property_id` configured | Tier 1 + `ga4`, `ga4-pages` |
| **3** (Ads) | + `ads_developer_token` + `ads_customer_id` | Tier 2 + `keywords`, `volume` |

Always communicate the detected tier before running commands.

## Quick Reference

| Command | What it does | Tier |
|---------|-------------|------|
| `/seo google setup` | Check/configure API credentials | -- |
| `/seo google pagespeed <url>` | PSI Lighthouse + CrUX field data | 0 |
| `/seo google crux <url>` | CrUX field data only (p75 metrics) | 0 |
| `/seo google crux-history <url>` | 25-week CWV trend analysis | 0 |
| `/seo google gsc <property>` | Search Console: clicks, impressions, CTR, position | 1 |
| `/seo google inspect <url>` | URL Inspection: index status, canonical, crawl info | 1 |
| `/seo google inspect-batch <file>` | Batch URL Inspection from file | 1 |
| `/seo google sitemaps <property>` | GSC sitemap status | 1 |
| `/seo google index <url>` | Submit URL to Indexing API | 1 |
| `/seo google index-batch <file>` | Batch submit up to 200 URLs | 1 |
| `/seo google ga4 [property-id]` | GA4 organic traffic report | 2 |
| `/seo google ga4-pages [property-id]` | Top organic landing pages | 2 |
| `/seo google youtube <query>` | YouTube video search (views, likes, duration) | 0 |
| `/seo google youtube-video <id>` | YouTube video details + top comments | 0 |
| `/seo google nlp <url-or-text>` | NLP entity extraction + sentiment + classification | 0 |
| `/seo google entities <url-or-text>` | Entity analysis only (for E-E-A-T) | 0 |
| `/seo google keywords <seed>` | Keyword ideas from Google Ads Keyword Planner | 3 |
| `/seo google volume <keywords>` | Search volume lookup from Keyword Planner | 3 |
| `/seo google entity <query>` | Knowledge Graph entity check | 0 |
| `/seo google safety <url>` | Web Risk URL safety check | 0 |
| `/seo google quotas` | Show rate limits for all APIs | -- |

---

## PageSpeed + CrUX

### `/seo google pagespeed <url>`

Combined Lighthouse lab data + CrUX field data.

**Script:** `"$HOME/.claude/skills/seo/bin/claude-seo" run pagespeed_check.py <url> --json`
**Reference:** `references/pagespeed-crux-api.md`
**Default:** Both mobile + desktop strategies, all Lighthouse categories.

Output merges lab scores (point-in-time Lighthouse) with field data (28-day
Chrome user metrics). CrUX tries URL-level first, falls back to origin-level.

### `/seo google crux <url>`

CrUX field data only (no Lighthouse run). Faster.

**Script:** `"$HOME/.claude/skills/seo/bin/claude-seo" run pagespeed_check.py <url> --crux-only --json`

### `/seo google crux-history <url>`

25-week CrUX History trends. Shows whether CWV metrics are improving, stable, or degrading.

**Script:** `"$HOME/.claude/skills/seo/bin/claude-seo" run crux_history.py <url> --json`
**Reference:** `references/pagespeed-crux-api.md`

Output includes per-metric trend direction, percentage change, and weekly p75 values.

---

## Search Console

### `/seo google gsc <property>`

Search Analytics: clicks, impressions, CTR, position for last 28 days.

**Script:** `"$HOME/.claude/skills/seo/bin/claude-seo" run gsc_query.py --property <property> --json`
**Reference:** `references/search-console-api.md`
**Default:** 28 days, dimensions=query,page, type=web, limit=1000.

Includes quick-win detection: queries at position 4-10 with high impressions.
The `totals` block comes from a separate dimensionless aggregate query because
query-level rows can omit anonymized low-volume traffic. Treat totals as
site-wide only when `totals_complete` is true. `--limit` caps total returned
dimension rows, not the size of every pagination request.

> **AI surfaces in GSC (2026):**
> - **Generative AI performance report** (launched 2026-06-03), a dedicated view of **AI Overviews + AI Mode** visibility. **Impressions only** (no clicks/CTR/position/query); dimensions Pages/Countries/Devices/Dates (Pacific Time); 1,000-row limit; newest data preliminary; a separate Discover gen-AI report also exists. Rolling out to a subset of properties.
> - **AI Mode already rolls into standard Performance totals** (Web search type), clicks (external-link clicks in AI Mode) and impressions are counted in the normal report, so you **cannot** cleanly split "classic" vs "AI" traffic from totals. Use the Generative AI report for impressions-only AI visibility.
> - **Data-reliability caveat:** a GSC logging error made **impressions, CTR, and average position unreliable from 2025-05-13 to 2026-04-27** (clicks unaffected; fixed forward-only, **no backfill**). Treat impression/CTR/position trends spanning that window with caution; expect an apparent impressions drop after the fix.

### `/seo google inspect <url>`

URL Inspection: real indexation status from Google.

**Script:** `"$HOME/.claude/skills/seo/bin/claude-seo" run gsc_inspect.py <url> --json`

Returns: verdict (PASS/FAIL), coverage state, robots.txt status, indexing state,
page fetch state, canonical selection, mobile usability, rich results.

### `/seo google inspect-batch <file>`

Batch inspection from a file (one URL per line). Rate limited to 2,000/day per site.

**Script:** `"$HOME/.claude/skills/seo/bin/claude-seo" run gsc_inspect.py --batch <file> --json`

### `/seo google sitemaps <property>`

List submitted sitemaps with status, errors, warnings. Sitemap contents report
submitted counts only; URL Inspection API is the indexation truth for whether
specific URLs are indexed.

**Script:** `"$HOME/.claude/skills/seo/bin/claude-seo" run gsc_query.py sitemaps --property <property> --json`

---


## Progressive Disclosure References (On-Demand)
- Detailed templates, extended examples, and deep-dive checklists have been moved to [references/detailed-guide.md](./references/detailed-guide.md) to keep context lean. Load that file via `view_file` only when needed.

## ⚠️ Gotchas (避坑指南)
- **避免關鍵字堆砌與門頁懲罰 (Doorway Pages)**：多據點或多機型頁面必須結合在地真實數據（如實收租金、分店地標、真實檢測數據），禁止僅替換地名或機型名稱。
- **Schema 與畫面一致性**：產出的 JSON-LD (`FAQPage`, `LocalBusiness`, `Product`) 內容必須與頁面可見文字 100% 一致，否則會觸發 Google 結構化資料人工處罰。
