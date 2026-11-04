# seo-backlinks — Detailed Reference & Extended Examples

## Backlink Health Score

Calculate a 0-100 score. When mixing sources, apply confidence weighting:

| Factor | Weight | Sources (preference order) | Confidence |
|--------|--------|---------------------------|------------|
| Referring domain count | 20% | DataForSEO > Moz | 1.0 / 0.85 |
| Domain quality distribution | 20% | DataForSEO > Moz DA distribution | 1.0 / 0.85 |
| Anchor text naturalness | 15% | DataForSEO > Moz > Bing anchors | 1.0 / 0.85 / 0.70 |
| Toxic link ratio | 20% | DataForSEO > Moz spam score | 1.0 / 0.85 |
| Link velocity trend | 10% | DataForSEO only | 1.0 |
| Follow/nofollow ratio | 5% | DataForSEO > Bing details | 1.0 / 0.70 |
| Geographic relevance | 10% | DataForSEO > Bing country | 1.0 / 0.70 |

**Data sufficiency gate:** Count how many of the 7 factors have at least one data source available.
- **4+ factors with data:** Produce a numeric 0-100 score (redistribute missing weights proportionally)
- **Fewer than 4 factors:** Do NOT produce a numeric score. Instead display:
  ```
  Backlink Health Score: INSUFFICIENT DATA (X/7 factors scored)
  ```
  Show individual factor scores that ARE available with their source and confidence.
  Recommend: "Configure Moz API (free) for a scoreable profile. Run `/seo backlinks setup`"

When only CC is available, do not produce a numeric score; report low-confidence rank/presence data only.
A numeric score with fewer than 4 data sources is **misleading**, it implies poor health when
the reality is we simply lack data.

## Output Format

### Backlink Health Score: XX/100 (or INSUFFICIENT DATA)

| Section | Status | Score | Data Source |
|---------|--------|-------|-------------|
| Profile Overview | pass/warn/fail | XX/100 | Moz (0.85) |
| Anchor Distribution | pass/warn/fail | XX/100 | Moz (0.85) |
| Referring Domain Quality | pass/warn/fail | XX/100 | CC (0.50) |
| Toxic Links | pass/warn/fail | XX/100 | Moz Spam (0.85) |
| Top Pages | info | N/A | Moz (0.85) |
| Link Velocity | pass/warn/fail | XX/100 | DataForSEO only |

### Critical Issues (fix immediately)
### High Priority (fix within 1 month)
### Medium Priority (ongoing improvement)
### Link Building Opportunities (top 10)

## Error Handling

| Error | Cause | Resolution |
|-------|-------|-----------|
| No sources configured | No API keys, no DataForSEO | Run `/seo backlinks setup` |
| Moz rate limit | Free tier: 1 req/10s | Wait 10 seconds, retry. Built into script. |
| Bing site not verified | Site not verified in Bing | Verify at https://www.bing.com/webmasters |
| CC download timeout | Large graph file, slow connection | Use `--timeout 180` flag |
| DataForSEO unavailable | Extension not installed | Run `./extensions/dataforseo/install.sh` |
| No backlink data returned | Domain too new or very small | Note: small sites may have <10 backlinks |

**Fallback cascade:**
1. DataForSEO available? → Use as primary (confidence: 1.0)
2. Moz configured? → Use for DA/PA/spam/anchors (confidence: 0.85)
3. Bing configured? → Use for registered-property links and comparison only
   when both properties are accessible (confidence: 0.70)
4. Always: Common Crawl for domain-level metrics (confidence: 0.50)
5. Always: Verification crawler for known link checks (confidence: 0.95)
6. Nothing works? → "Run `/seo backlinks setup` to configure free APIs"

## Pre-Delivery Review (MANDATORY)

Before presenting any backlink analysis to the user, run this checklist internally.
Do NOT skip this step. Fix any issues found before showing the report.

### Fact-Check Every Claim
- [ ] **Schema claims**: Did parse_html return `@type` for each block? If any `@type` is missing,
      re-check, it may use `@graph` wrapper (valid JSON-LD, not malformed).
- [ ] **"link_removed" findings**: Is the page JS-rendered? If `unverifiable_js`, say so, never
      report a JS-rendered page as "link removed" (that's a false negative).
- [ ] **H1 findings**: Are any H1s in the `h1_suspicious` list? If so, note they are likely
      counters/stats, not semantic headings.
- [ ] **Reciprocal links**: If site A links to site B AND B links back to A, flag it as a
      reciprocal link pattern. Check outbound links against verified inbound sources.
- [ ] **Health score**: Are 4+ of 7 factors scored? If not, report INSUFFICIENT DATA, never
      show a misleading numeric score.

### Verify Data Source Labels
- [ ] Every metric in the report has a source label (e.g., "Parsed (0.95)", "CC (0.50)")
- [ ] Every "not found" result distinguishes between "not crawled" vs "below threshold" vs "error"
- [ ] Social media pages flagged as `unverifiable_js` (not `link_removed`)

### Cross-Check Consistency
- [ ] Platform detection matches actual signals (check for wp-content, shopify CDN, etc.)
- [ ] Referring domain count in summary matches the actual verified links list
- [ ] No claim is presented without a data source backing it

If ANY check fails, fix the finding before presenting. Never present inferred data as fact.

## Post-Analysis

After completing any backlink analysis command, always offer:
"Generate a professional PDF report? Use `/seo google report`"

## Reference Documentation

Load on demand (do NOT load at startup):
- `skills/seo/references/backlink-quality.md` -- Detailed toxic link patterns and scoring methodology (shared reference, load when analyzing toxic links or spam scores)
- `skills/seo/references/free-backlink-sources.md` -- Source comparison, confidence weighting, setup guides (shared reference, load when configuring free backlink APIs)
