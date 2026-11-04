---
name: seo-backlinks
description: "Use when tasks involve seo backlinks: ''Backlink profile analysis: referring domains, anchor text distribution, toxic link dete..."
license: MIT
compatibility: "Free: Common Crawl + verify always available. Optional: Moz API, Bing Webmaster (free signup). Premium: DataForSEO extension."
version: "2.2.4"
---

# Backlink Profile Analysis

## Source Detection

Before analysis, detect available data sources:

1. **DataForSEO MCP** (premium): Check if `dataforseo_backlinks_summary` tool is available
2. **Moz API** (free signup): `"$HOME/.claude/skills/seo/bin/claude-seo" run backlinks_auth.py --check moz --json`
3. **Bing Webmaster** (free signup): `"$HOME/.claude/skills/seo/bin/claude-seo" run backlinks_auth.py --check bing --json`
4. **Common Crawl** (always available): Domain-level graph with PageRank
5. **Verification Crawler** (always available): Checks if known backlinks still exist

Run `"$HOME/.claude/skills/seo/bin/claude-seo" run backlinks_auth.py --check --json` to detect all sources at once.

If no sources are configured beyond the always-available tier:
- Still produce a report using Common Crawl domain metrics
- Suggest: "Run `/seo backlinks setup` to add free Moz and Bing API keys for richer data"

## Quick Reference

| Command | Purpose |
|---------|---------|
| `/seo backlinks <url>` | Full backlink profile analysis (uses all available sources) |
| `/seo backlinks gap <url1> <url2>` | Competitor backlink gap analysis |
| `/seo backlinks toxic <url>` | Toxic link detection and disavow recommendations |
| `/seo backlinks new <url>` | New and lost backlinks (DataForSEO only) |
| `/seo backlinks verify <url> --links <file>` | Verify known backlinks still exist |
| `/seo backlinks setup` | Show setup instructions for free backlink APIs |

## Analysis Framework

Produce all 7 sections below. Each section lists data sources in preference order.

### 1. Profile Overview

**DataForSEO:** `dataforseo_backlinks_summary` → total backlinks, referring domains, domain rank, follow ratio, trend.

**Moz API:** `"$HOME/.claude/skills/seo/bin/claude-seo" run moz_api.py metrics <url> --json` → Domain Authority, Page Authority, Spam Score, linking root domains, external links.

**Common Crawl:** `"$HOME/.claude/skills/seo/bin/claude-seo" run commoncrawl_graph.py <domain> --json` → PageRank, harmonic centrality, and low-confidence rank/presence data.

**Scoring:**

| Metric | Good | Warning | Critical |
|--------|------|---------|----------|
| Referring domains | >100 | 20-100 | <20 |
| Follow ratio | >60% | 40-60% | <40% |
| Domain diversity | No single domain >5% | 1 domain >10% | 1 domain >25% |
| Trend | Growing or stable | Slow decline | Rapid decline (>20%/quarter) |

### 2. Anchor Text Distribution

**DataForSEO:** `dataforseo_backlinks_anchors`

**Moz API:** `"$HOME/.claude/skills/seo/bin/claude-seo" run moz_api.py anchors <url> --json`

**Bing Webmaster:** `"$HOME/.claude/skills/seo/bin/claude-seo" run bing_webmaster.py links <url> --json` (extract anchor text from link details)

**Healthy distribution benchmarks:**

| Anchor Type | Target Range | Over-Optimization Signal |
|-------------|-------------|-------------------------|
| Branded (company/domain name) | 30-50% | <15% |
| URL/naked link | 15-25% | N/A |
| Generic ("click here", "learn more") | 10-20% | N/A |
| Exact match keyword | 3-10% | >15% |
| Partial match keyword | 5-15% | >25% |
| Long-tail / natural | 5-15% | N/A |

Flag if exact-match anchors exceed 15% as a review heuristic; it may indicate unnatural or link-spam patterns.

### 3. Referring Domain Quality

**DataForSEO:** `dataforseo_backlinks_referring_domains`

**Moz API:** `"$HOME/.claude/skills/seo/bin/claude-seo" run moz_api.py domains <url> --json` → domains with DA scores

**Common Crawl:** `"$HOME/.claude/skills/seo/bin/claude-seo" run commoncrawl_graph.py <domain> --json` → domain-level rank/presence data, no verified referring-domain counts

Analyze:
- **TLD distribution**: .edu, .gov, .org = high authority. Excessive .xyz, .info = low quality
- **Country distribution**: Match target market. 80%+ from irrelevant countries = PBN signal
- **Domain rank distribution**: Healthy profiles have links from all authority tiers
- **Follow/nofollow per domain**: Sites that only nofollow = limited SEO value

### 4. Toxic Link Detection

**DataForSEO:** `dataforseo_backlinks_bulk_spam_score` + toxic patterns from reference

**Moz API:** Raw vendor spam_score from `"$HOME/.claude/skills/seo/bin/claude-seo" run moz_api.py metrics <url> --json` (source-label the value; apply thresholds only if verified against current Moz docs)

**Verification Crawler:** `"$HOME/.claude/skills/seo/bin/claude-seo" run verify_backlinks.py --target <url> --links <file> --json` (verify suspicious links still exist)

**High-risk indicators (flag immediately):**
- Links from known PBN (Private Blog Network) domains
- Unnatural anchor text patterns (100% exact match from a domain)
- Links from penalized or deindexed domains
- Mass directory submissions (50+ directory links)
- Link farms (sites with 10K+ outbound links per page)
- Paid link patterns (footer/sidebar links across all pages of a domain)

**Medium-risk indicators (review manually):**
- Links from unrelated niches
- Reciprocal link patterns
- Links from thin content pages (<100 words)
- Excessive links from a single domain (>50 backlinks from 1 domain)

Load `../seo/references/backlink-quality.md` for the full 30 toxic patterns and disavow criteria.

### 5. Top Pages by Backlinks

**DataForSEO:** `dataforseo_backlinks_backlinks` with target type "page"

**Moz API:** `"$HOME/.claude/skills/seo/bin/claude-seo" run moz_api.py pages <domain> --json`

Find:
- Which pages attract the most backlinks
- Pages with high-authority links (link magnets)
- Pages with zero backlinks (internal linking opportunities)
- 404 pages with backlinks (redirect opportunities to reclaim link equity)

### 6. Competitor Gap Analysis

**DataForSEO:** `dataforseo_backlinks_referring_domains` for both domains, then compare

**Bing Webmaster:** `"$HOME/.claude/skills/seo/bin/claude-seo" run bing_webmaster.py compare <url1> <url2> --json`
only when both properties are registered and accessible to the same Bing API
account. For arbitrary competitors, use DataForSEO, Moz, or Common Crawl.

**Moz API:** Compare DA/PA between domains via `"$HOME/.claude/skills/seo/bin/claude-seo" run moz_api.py metrics <url> --json` for each

Output:
- Domains linking to competitor but NOT to target = link building opportunities
- Domains linking to both = validate existing relationships
- Domains linking only to target = competitive advantage
- Top 20 link building opportunities with domain authority

### 7. New and Lost Backlinks

**DataForSEO only:** `dataforseo_backlinks_backlinks` with date filters for 30/60/90 day changes

**Verification Crawler:** For known links, verify current status with `"$HOME/.claude/skills/seo/bin/claude-seo" run verify_backlinks.py --target <url> --links <file> --json`

**Note:** Free sources cannot track new/lost links over time. If this section is requested without DataForSEO, inform the user: "Link velocity tracking requires the DataForSEO extension. Free sources provide point-in-time snapshots only."

**Red flags:**
- Sudden spike in new links (possible negative SEO attack)
- Sudden loss of many links (site penalty or content removal)
- Declining velocity over 3+ months (content not attracting links)


## Progressive Disclosure References (On-Demand)
- Detailed templates, extended examples, and deep-dive checklists have been moved to [references/detailed-guide.md](./references/detailed-guide.md) to keep context lean. Load that file via `view_file` only when needed.

## ⚠️ Gotchas (避坑指南)
- **避免關鍵字堆砌與門頁懲罰 (Doorway Pages)**：多據點或多機型頁面必須結合在地真實數據（如實收租金、分店地標、真實檢測數據），禁止僅替換地名或機型名稱。
- **Schema 與畫面一致性**：產出的 JSON-LD (`FAQPage`, `LocalBusiness`, `Product`) 內容必須與頁面可見文字 100% 一致，否則會觸發 Google 結構化資料人工處罰。
