# seo-cluster — Detailed Reference & Extended Examples

## Strategy Import

When invoked with `--from strategy`:

1. Look for the most recent `/seo plan` output in the current directory (search for
   files matching `*SEO*Plan*`, `*strategy*`, `*content-strategy*`)
2. Parse markdown tables for: keywords, page types, content pillars, URL structures
3. Validate extracted data: check for duplicates, missing keywords, incomplete entries
4. Enrich with SERP data: run SERP overlap analysis on extracted keywords
5. Build cluster plan using the imported keywords as the starting set (skip Step 1)

If no strategy file is found, prompt the user: "No existing SEO plan found in the
current directory. Run `/seo plan` first, or provide a seed keyword for fresh clustering."

---

## Execution Workflow

When `/seo cluster execute` is invoked:

### Check for claude-blog

```
Test: Does ~/.claude/skills/blog/SKILL.md exist?
```

**If claude-blog IS installed:**

1. Load `references/execution-workflow.md` for the full algorithm
2. Read `cluster-plan.json` from the current directory
3. Check for resume state: scan output directory for already-written posts
4. Execute in priority order: pillar first, then spokes by volume (highest first)
5. For each post, invoke the `blog-write` skill with cluster context:
   - Cluster role (pillar or spoke)
   - Position in cluster (cluster index, post index)
   - Target keyword and secondary keywords
   - Template type and word count target
   - Internal links to include (with anchors)
   - Links to receive from future posts (placeholder markers)
6. After each post is written, scan previous posts for backward link placeholders
   and inject the new post's URL
7. After all posts are written, generate the cluster scorecard

**If claude-blog is NOT installed:**

1. Generate detailed content briefs for each post in the cluster plan
2. Each brief includes:
   - Title and meta description
   - Primary keyword and secondary keywords
   - Template type and suggested structure (H2/H3 outline)
   - Word count target
   - Internal links to include (with anchor text)
   - Key points to cover
   - Competing pages to differentiate from
3. Write briefs to `cluster-briefs/` directory as individual markdown files
4. Inform user: "Install [claude-blog](https://github.com/AgriciDaniel/claude-blog)
   to auto-create content. Briefs saved to `cluster-briefs/`."

---

## Cluster Scorecard

Post-execution quality report. Run automatically after `/seo cluster execute` or
on demand via analysis of the output directory.

| Metric | Target | How Measured |
|--------|--------|-------------|
| Coverage | 100% | Posts written / posts planned |
| Link Density | 3+ per post | Count internal links per post |
| Orphan Pages | 0 | Posts with < 1 incoming link |
| Cannibalization | 0 conflicts | Check for duplicate primary keywords |
| Image Count | 1+ per post | Posts with at least one image |
| Pillar Links | 100% | All spokes link to pillar and vice versa |
| Cross-Links | 80%+ | Recommended spoke-to-spoke links implemented |
| Content Gaps | 0 | Planned posts that were skipped or incomplete |

---

## Map Regeneration

When `/seo cluster map` is invoked:

1. Read `cluster-plan.json` from the current directory
2. Scan output directory and update post statuses (planned vs written)
3. Regenerate `cluster-map.html` with updated statuses
4. Report: posts written vs planned, link completion percentage

---

## Output Files

All outputs are written to the current working directory:

| File | Description |
|------|-------------|
| `cluster-plan.json` | Machine-readable cluster plan (full data) |
| `cluster-plan.md` | Human-readable cluster plan summary |
| `cluster-map.html` | Interactive SVG visualization |
| `cluster-briefs/` | Content briefs (if no claude-blog) |
| `cluster-scorecard.md` | Post-execution quality report |

---

## Cross-Skill Integration

| Skill | Relationship |
|-------|-------------|
| `seo-plan` | Import source: strategy import reads seo-plan output |
| `seo-content` | Quality check: E-E-A-T validation of generated content |
| `seo-schema` | Schema markup: Article, BreadcrumbList, ItemList for cluster pages |
| `seo-dataforseo` | Data source: SERP data when DataForSEO MCP is available |
| `seo-google` | Reporting: generate PDF report of cluster plan and scorecard |

After cluster planning or execution completes, offer:
"Generate a PDF report? Use `/seo google report`"

---

## Error Handling

| Error | Cause | Resolution |
|-------|-------|------------|
| "No seed keyword provided" | Missing argument | Prompt user for seed keyword or URL |
| "Insufficient keyword variants" | Expansion yielded < 15 keywords | Run second expansion pass with PAA questions |
| "SERP data unavailable" | WebSearch and DataForSEO both failing | Retry after 30s; if persistent, use intent-only clustering with warning |
| "No strategy file found" | `--from strategy` but no plan exists | Prompt user to run `/seo plan` first |
| "cluster-plan.json not found" | Execute without planning | Prompt user to run `/seo cluster plan` first |
| "claude-blog not installed" | Execute attempted without blog skill | Generate content briefs instead; suggest installation |
| "DataForSEO budget exceeded" | Cost check returned "blocked" | Fall back to WebSearch; inform user |
| "Duplicate primary keywords" | Cannibalization detected | Merge affected posts or reassign keywords |
| "Orphan page detected" | Post missing incoming links | Add links from nearest cluster siblings |
| "Resume state corrupted" | Mismatch between plan and output | Rebuild state from output directory scan |

---

## Security

- All URLs fetched via `"$HOME/.claude/skills/seo/bin/claude-seo" run render_page.py <url> --mode auto` (SPA-aware SSRF protection via `url_safety`)
- No credentials stored or transmitted
- Output files contain no PII or API keys
- DataForSEO cost checks run before every API call

## FLOW Framework Integration

For prompt-guided keyword research and gap analysis, use `/seo flow find [url|topic]`: FLOW's 5 find-stage prompts complement the SERP-overlap clustering methodology with structured discovery prompts.
