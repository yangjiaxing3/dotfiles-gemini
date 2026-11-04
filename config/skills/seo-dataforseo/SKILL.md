---
name: seo-dataforseo
description: "Use when tasks involve seo dataforseo: 'Live SEO data via DataForSEO MCP server: SERP analysis, keyword research (volume, diffi..."
license: MIT
compatibility: "Requires DataForSEO MCP server"
version: "2.2.4"
---

# DataForSEO: Live SEO Data (Extension)

Live search data via the DataForSEO MCP server. Provides real-time SERP results
(organic + images), keyword metrics, backlink profiles, on-page analysis, content
analysis, business listings, AI visibility checking, and LLM mention tracking
across 9 API modules with 79+ MCP tools.

## Prerequisites

This skill requires the DataForSEO extension to be installed:
```bash
./extensions/dataforseo/install.sh
```

**Check availability:** Before using any DataForSEO tool, verify the MCP server
is connected by checking if `serp_organic_live_advanced` or any DataForSEO tool
is available. If tools are not available, inform the user the extension is not
installed and provide install instructions.

## API Credit Awareness

DataForSEO charges per API call. Be efficient:
- Prefer bulk endpoints over multiple single calls
- Use default parameters (US, English) unless user specifies otherwise
- Cache results mentally within a session; don't re-fetch the same data
- Warn user before running expensive operations (full backlink crawls, large keyword lists)

## Cost Guardrails

**Before every DataForSEO MCP call**, run cost estimation:
```
"$HOME/.claude/skills/seo/bin/claude-seo" run dataforseo_costs.py check <endpoint> [--count N]
```

- If `"status": "approved"` → proceed with the API call
- If `"status": "needs_approval"` → show the cost estimate to the user and ask for confirmation before proceeding
- If `"status": "blocked"` → inform the user that the daily budget limit would be exceeded; do NOT proceed

**After each API call completes**, log the cost:
```
"$HOME/.claude/skills/seo/bin/claude-seo" run dataforseo_costs.py log <endpoint> <actual_cost>
```

**User commands for cost management:**
- `/seo dataforseo costs today` → show today's spending breakdown
- `/seo dataforseo costs summary` → show 7-day spending history
- `/seo dataforseo costs config --mode threshold --threshold 0.50` → configure approval mode

Load `references/cost-tiers.md` for the full pricing table, budget presets, and cost reduction tips.

## Quick Reference

| Command | What it does |
|---------|-------------|
| `/seo dataforseo serp <keyword>` | Google organic SERP results |
| `/seo dataforseo serp-images <keyword>` | Google Images SERP results |
| `/seo dataforseo serp-youtube <keyword>` | YouTube search results |
| `/seo dataforseo youtube <video_id>` | YouTube video deep analysis |
| `/seo dataforseo keywords <seed>` | Keyword ideas and suggestions |
| `/seo dataforseo volume <keywords>` | Search volume for keywords |
| `/seo dataforseo difficulty <keywords>` | Keyword difficulty scores |
| `/seo dataforseo intent <keywords>` | Search intent classification |
| `/seo dataforseo trends <keyword>` | Google Trends data |
| `/seo dataforseo backlinks <domain>` | Full backlink profile |
| `/seo dataforseo competitors <domain>` | Competitor domain analysis |
| `/seo dataforseo ranked <domain>` | Ranked keywords for domain |
| `/seo dataforseo intersection <domains>` | Keyword/backlink overlap |
| `/seo dataforseo traffic <domains>` | Bulk traffic estimation |
| `/seo dataforseo subdomains <domain>` | Subdomains with ranking data |
| `/seo dataforseo top-searches <domain>` | Top queries mentioning domain |
| `/seo dataforseo onpage <url>` | On-page analysis (Lighthouse + parsing) |
| `/seo dataforseo tech <domain>` | Technology stack detection |
| `/seo dataforseo whois <domain>` | WHOIS registration data |
| `/seo dataforseo content <keyword/url>` | Content analysis and trends |
| `/seo dataforseo listings <keyword>` | Business listings search |
| `/seo dataforseo ai-scrape <query>` | ChatGPT web scraper for GEO |
| `/seo dataforseo ai-mentions <keyword>` | LLM mention tracking for GEO |

---

## SERP Analysis

### `/seo dataforseo serp <keyword>`

Fetch live Google organic search results.

**MCP tools:** `serp_organic_live_advanced`

**Default parameters:** location_code=2840 (US), language_code=en, device=desktop, depth=100

**Also supports:** The `serp_organic_live_advanced` tool supports Google, Bing, and Yahoo via the `se` parameter. Specify "bing" or "yahoo" to switch search engines.

**Output:** Rank, URL, title, description, domain, featured snippets, AI overview references, People Also Ask.

### `/seo dataforseo serp-youtube <keyword>`

Fetch YouTube search results. Valuable for GEO. YouTube mentions correlate most strongly with AI citations.

**MCP tools:** `serp_youtube_organic_live_advanced`

**Output:** Video title, channel, views, upload date, description, URL.

### `/seo dataforseo youtube <video_id>`

Deep analysis of a specific YouTube video: info, comments, and subtitles. Treat YouTube mentions as a useful GEO signal, but AI visibility correlations are methodology-dependent.

**MCP tools:** `serp_youtube_video_info_live_advanced`, `serp_youtube_video_comments_live_advanced`, `serp_youtube_video_subtitles_live_advanced`

**Parameters:** video_id (the YouTube video ID, e.g., "dQw4w9WgXcQ")

**Output:** Video metadata (title, channel, views, likes, description), top comments with engagement, subtitle/transcript text.

### `/seo dataforseo serp-images <keyword>`

Fetch live Google Images search results. See which images rank for a keyword,
which domains dominate image results, and identify visual content opportunities.

**MCP tools:** `serp_google_images_live_advanced`

**Default parameters:** location_code=2840 (US), language_code=en, device=desktop, depth=100

**Parameters:** keyword (required), depth (optional, max 700, billed per 100-result increment), search_param (optional, e.g. "site:example.com")

**Cost warning:** Using `site:` or `filetype:` operators incurs **5x API cost**. Warn user before running filtered queries.

**Output:** Position, title, alt text, source page URL, direct image URL, domain, encoded URL.

**Analysis to provide:**
- Domain dominance: which sites own the most image positions (top 10 domains by count)
- Alt text patterns: common title/alt text patterns in top-ranking images
- Format distribution: WebP vs JPEG vs PNG in top results (infer from image_url extension)
- Opportunity identification: keywords where user has organic rankings but no image presence

---


## Progressive Disclosure References (On-Demand)
- Detailed templates, extended examples, and deep-dive checklists have been moved to [references/detailed-guide.md](./references/detailed-guide.md) to keep context lean. Load that file via `view_file` only when needed.

## ⚠️ Gotchas (避坑指南)
- **避免關鍵字堆砌與門頁懲罰 (Doorway Pages)**：多據點或多機型頁面必須結合在地真實數據（如實收租金、分店地標、真實檢測數據），禁止僅替換地名或機型名稱。
- **Schema 與畫面一致性**：產出的 JSON-LD (`FAQPage`, `LocalBusiness`, `Product`) 內容必須與頁面可見文字 100% 一致，否則會觸發 Google 結構化資料人工處罰。
