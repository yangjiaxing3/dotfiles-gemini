# seo-google — Detailed Reference & Extended Examples

## Indexing API

### `/seo google index <url>`

Notify Google of a URL update.

**Script:** `"$HOME/.claude/skills/seo/bin/claude-seo" run indexing_notify.py <url> --json`
**Reference:** `references/indexing-api.md`

The Indexing API is officially for JobPosting and BroadcastEvent/VideoObject pages.
Always inform the user of this restriction. Daily quota: 200 publish requests.

### `/seo google index-batch <file>`

Batch submit URLs from a file. Tracks quota usage.

**Script:** `"$HOME/.claude/skills/seo/bin/claude-seo" run indexing_notify.py --batch <file> --json`

---

## GA4 Traffic

### `/seo google ga4 [property-id]`

Organic traffic report: daily sessions, users, pageviews, bounce rate, engagement.

**Script:** `"$HOME/.claude/skills/seo/bin/claude-seo" run ga4_report.py --property <id> --json`
**Reference:** `references/ga4-data-api.md`
**Default:** 28 days, filtered to Organic Search channel group.

> **GA4 "AI Assistants" channel (live ~2026-05-13):** GA4 added a native *AI Assistants* Default Channel Group. Sessions referred by a recognized AI assistant get `medium=ai-assistant`. Google's recognized sources are **ChatGPT, Gemini, Claude, Deepseek, Copilot, Grok** and the channel **excludes** Google AI Overviews / AI Mode. **Verify Perplexity separately if needed**; unsupported sources may stay in Referral, and most AI sessions arrive referrer-less and fall into **Direct**, so this channel undercounts AI traffic. Forward-only, no backfill.

### `/seo google ga4-pages [property-id]`

Top organic landing pages ranked by sessions.

**Script:** `"$HOME/.claude/skills/seo/bin/claude-seo" run ga4_report.py --property <id> --report top-pages --json`

---

## YouTube (Video SEO)

Some third-party studies report a 0.737 correlation between YouTube mentions and AI visibility. Treat it as a methodology-dependent signal. Free, API key only.

### `/seo google youtube <query>`

Search YouTube for videos. Returns title, channel, views, likes, duration.

**Script:** `"$HOME/.claude/skills/seo/bin/claude-seo" run youtube_search.py search "<query>" --json`
**Reference:** `references/youtube-api.md`
**Quota:** 100 units per search (10,000 units/day free).

### `/seo google youtube-video <video_id>`

Detailed video info + tags + top 10 comments.

**Script:** `"$HOME/.claude/skills/seo/bin/claude-seo" run youtube_search.py video <video_id> --json`
**Quota:** 2 units (video details + comments).

---

## NLP Content Analysis

Google NLP entity/sentiment output for internal content-quality checks. Do not treat it as Google E-E-A-T scoring.

### `/seo google nlp <url-or-text>`

Full NLP analysis: entities, sentiment, content classification.

**Script:** `"$HOME/.claude/skills/seo/bin/claude-seo" run nlp_analyze.py --url <url> --json` or `--text "..."`
**Reference:** `references/nlp-api.md`
**Free tier:** 5,000 units/month. Requires billing enabled on GCP project.

### `/seo google entities <url-or-text>`

Entity extraction only (faster, less quota).

**Script:** `"$HOME/.claude/skills/seo/bin/claude-seo" run nlp_analyze.py --url <url> --features entities --json`

---

## Keyword Research (Google Ads)

Gold-standard keyword volume data. Requires Google Ads account.

### `/seo google keywords <seed>`

Generate keyword ideas from seed terms.

**Script:** `"$HOME/.claude/skills/seo/bin/claude-seo" run keyword_planner.py ideas "<seed>" --json`
**Reference:** `references/keyword-planner-api.md`
**Requires:** Ads developer token + customer ID in config (Tier 3).

### `/seo google volume <keywords>`

Search volume for specific keywords (comma-separated).

**Script:** `"$HOME/.claude/skills/seo/bin/claude-seo" run keyword_planner.py volume "<kw1>,<kw2>" --json`

---

## Supplementary

### `/seo google entity <query>`

Knowledge Graph entity check. Verifies brand presence.

**Reference:** `references/supplementary-apis.md`
Uses Knowledge Graph Search API with API key.

### `/seo google safety <url>`

Web Risk API check for malware/social engineering flags.

**Reference:** `references/supplementary-apis.md`

### `/seo google quotas`

Display rate limits table. Read `references/rate-limits-quotas.md`.

---

## Reports

After any analysis command, offer to generate a PDF/HTML report.

### `/seo google report <type>`

Generate a professional PDF report with charts and analytics.

**Script:** `"$HOME/.claude/skills/seo/bin/claude-seo" run google_report.py --type <type> --data <json> --domain <domain> --format pdf`

| Type | Input | Output |
|------|-------|--------|
| `cwv-audit` | PSI + CrUX + CrUX History data | Core Web Vitals audit with gauges, timelines, distributions |
| `gsc-performance` | GSC query data | Search Console report with query tables, quick wins |
| `indexation` | Batch inspection data | Indexation status with coverage donut chart |
| `full` | All data combined | Comprehensive Google SEO report (all sections) |

**Workflow:**
1. Run data collection commands (pagespeed, gsc, inspect-batch, etc.)
2. Save JSON output to file: `"$HOME/.claude/skills/seo/bin/claude-seo" run pagespeed_check.py <url> --json > data.json`
3. Generate report: `"$HOME/.claude/skills/seo/bin/claude-seo" run google_report.py --type cwv-audit --data data.json --domain <domain>`

**Convention:** After completing analysis, suggest: "Generate a report? Use `/seo google report <type>`"

---

## Rate Limits

| API | Per-Minute | Per-Day | Auth |
|-----|-----------|---------|------|
| PSI v5 | 240 QPM | 25,000 QPD | API Key |
| CrUX + History | 150 QPM (shared) | Unlimited | API Key |
| GSC Search Analytics | 1,200 QPM/site | 30M QPD | Service Account |
| GSC URL Inspection | 600 QPM | 2,000 QPD/site | Service Account |
| Indexing API | 380 RPM | 200 publish/day | Service Account |
| GA4 Data API | 10 concurrent | ~25K tokens/day | Service Account |

## Cross-Skill Integration

- **seo-audit**: Spawns `seo-google` agent for live CWV + indexation data (conditional)
- **seo-technical**: Uses pagespeed_check.py for real CWV field data
- **seo-performance**: CrUX field data supplements Lighthouse lab data
- **seo-sitemap**: GSC sitemap status shows submitted counts, errors, and warnings; use URL Inspection for indexation truth
- **seo-content**: GSC query data informs keyword targeting
- **seo-geo**: Use GSC Generative AI performance reports and AI Overviews/AI Mode/Discover gen-AI include/exclude controls where available

## Output Format

- CWV metrics: traffic-light rating (Good / Needs Improvement / Poor)
- Performance reports: tables with sortable columns
- Always include data freshness note
- Save reports as `GOOGLE-API-REPORT-{domain}.md`
- Markdown/LLM templates in `assets/templates/`: `cwv-audit-report.md`, `gsc-performance-report.md`, `indexation-status-report.md`; distinct from `google_report.py`'s PDF pipeline

## Technical Notes

- INP replaced FID on March 12, 2024. Never reference FID.
- CLS values from CrUX are string-encoded (e.g., "0.05"). Scripts handle parsing.
- CrUX 404 = insufficient traffic, not an auth error.
- Search Analytics data has 2-3 day lag.
- `round_trip_time` replaced `effectiveConnectionType` in CrUX (Feb 2025).
- Custom Search JSON API is closed to new customers (2025).

## Error Handling

| Scenario | Action |
|----------|--------|
| No credentials configured | Run `/seo google setup`. List Tier 0 commands that work with just an API key. |
| Service account lacks GSC access | Report error. Instruct: add `client_email` to GSC > Settings > Users > Add. |
| CrUX data unavailable (404) | Report insufficient Chrome traffic. Suggest PSI lab data as fallback. |
| GA4 property not found | Report error. Show how to find property ID in GA4 Admin > Property Details. |
| Indexing API quota exceeded | Report 200/day limit. Suggest prioritizing most important URLs. |
| Rate limit (429) | Wait and retry with exponential backoff. Report which API hit the limit. |
