---
name: seo-cluster
description: "Use when tasks involve seo cluster: 'SERP-based semantic topic clustering for content architecture planning. Groups keywords by..."
license: MIT
version: "2.2.4"
---

# Semantic Topic Clustering

SERP-overlap-driven keyword clustering for content architecture. Groups keywords
by how Google actually ranks them (shared top-10 results), not by text similarity.
Designs hub-and-spoke content clusters with internal link matrices and generates
interactive cluster map visualizations.

**Scripts:** Located at the plugin root `scripts/` directory.

---

## Quick Reference

| Command | What it does |
|---------|-------------|
| `/seo cluster plan <seed-keyword>` | Full planning workflow: expand, cluster, architect, visualize |
| `/seo cluster plan --from strategy` | Import from existing `/seo plan` output |
| `/seo cluster execute` | Execute plan: create content via claude-blog or output briefs |
| `/seo cluster map` | Regenerate the interactive cluster visualization |

---

## Planning Workflow

### Step 1: Seed Keyword Expansion

Expand the seed keyword into 30-50 variants using WebSearch:

1. **Related searches**: Search the seed, extract "related searches" and "people also search for"
2. **People Also Ask (PAA)**: Extract all PAA questions from SERP results
3. **Long-tail modifiers**: Append common modifiers: "best", "how to", "vs", "for beginners", "tools", "examples", "guide", "template", "mistakes", "checklist"
4. **Question mining**: Generate who/what/when/where/why/how variants
5. **Intent modifiers**: Add commercial modifiers: "pricing", "review", "alternative", "comparison", "free", "top"

**Deduplication:** Normalize variants (lowercase, strip articles), remove exact duplicates.
Target: 30-50 unique keyword variants. If under 30, run a second expansion pass
with the top PAA questions as seeds.

### Step 2: SERP Overlap Clustering

This is the core differentiator. Load `references/serp-overlap-methodology.md` for
the full algorithm.

**Process:**
1. Group keywords by initial intent guess (reduces pairwise comparisons)
2. For each candidate pair within a group, WebSearch both keywords
3. Count shared URLs in the top 10 organic results (ignore ads, featured snippets, PAA)
4. Apply thresholds:

| Shared Results | Relationship | Action |
|---------------|-------------|--------|
| 7-10 | Same post | Merge into single target page |
| 4-6 | Same cluster | Group under same spoke cluster |
| 2-3 | Interlink | Place in adjacent clusters, add cross-links |
| 0-1 | Separate | Assign to different clusters or exclude |

**Optimization:** With 40 keywords, full pairwise = 780 comparisons. Instead:
- Pre-group by intent (4 groups of ~10 = 4 x 45 = 180 comparisons)
- Only cross-check group boundary keywords
- Skip pairs where both are long-tail variants of the same head term (assume same cluster)

**DataForSEO integration:** If DataForSEO MCP is available, use `serp_organic_live_advanced`
instead of WebSearch for SERP data. Run `"$HOME/.claude/skills/seo/bin/claude-seo" run dataforseo_costs.py check serp_organic_live_advanced --count N`
before each batch. If `"status": "needs_approval"`, show cost estimate and ask user.
If `"status": "blocked"`, fall back to WebSearch.

### Step 3: Intent Classification

Classify each keyword into one of four intent categories:

| Intent | Signals | Include in Clusters? |
|--------|---------|---------------------|
| Informational | how, what, why, guide, tutorial, learn | Yes |
| Commercial | best, top, review, comparison, vs, alternative | Yes |
| Transactional | buy, price, discount, coupon, order, sign up | Yes |
| Navigational | brand names, specific product names, login | No (exclude) |

Remove navigational keywords from clustering. Flag borderline cases for
manual review. Keywords can have mixed intent (e.g., "best CRM software" is
both commercial and informational) -- classify by dominant intent.

### Step 4: Hub-and-Spoke Architecture

Load `references/hub-spoke-architecture.md` for full specifications.

**Design the cluster structure:**

1. **Select the pillar keyword**: Highest volume, broadest intent, most SERP overlap with other keywords
2. **Group spokes into clusters**: Each cluster is a subtopic area (2-5 clusters per pillar)
3. **Assign posts to clusters**: Each cluster gets 2-4 spoke posts
4. **Select templates per post**: Based on intent classification:

| Intent Pattern | Template Options |
|---------------|-----------------|
| Informational (broad) | ultimate-guide |
| Informational (how) | how-to |
| Informational (list) | listicle |
| Informational (concept) | explainer |
| Commercial (compare) | comparison |
| Commercial (evaluate) | review |
| Commercial (rank) | best-of |
| Transactional | landing-page |

5. **Set word count targets:**
   - Pillar page: 2500-4000 words
   - Spoke posts: 1200-1800 words

6. **Cannibalization check**: No two posts share the same primary keyword. If SERP
   overlap is 7+, merge those keywords into a single post targeting both.

### Step 5: Internal Link Matrix

Design the bidirectional linking structure:

| Link Type | Direction | Requirement |
|-----------|-----------|-------------|
| Spoke to pillar | spoke -> pillar | Mandatory (every spoke) |
| Pillar to spoke | pillar -> spoke | Mandatory (every spoke) |
| Spoke to spoke (within cluster) | spoke <-> spoke | 2-3 links per post |
| Cross-cluster | spoke -> spoke (other cluster) | 0-1 links per post |

**Rules:**
- Every post must have minimum 3 incoming internal links
- No orphan pages (every post reachable from pillar in 2 clicks)
- Anchor text must use target keyword or close variant (no "click here")
- Link placement: within body content, not just navigation/sidebar

Generate the link matrix as a JSON adjacency list:
```json
{
  "links": [
    { "from": "pillar", "to": "cluster-0-post-0", "type": "mandatory", "anchor": "keyword" },
    { "from": "cluster-0-post-0", "to": "pillar", "type": "mandatory", "anchor": "keyword" }
  ]
}
```

### Step 6: Interactive Cluster Map

Generate `cluster-map.html` using the template at `templates/cluster-map.html`.

1. Read the template file
2. Build the `CLUSTER_DATA` JSON object from the cluster plan:
   ```javascript
   {
     pillar: { title, keyword, volume, template, wordCount, url },
     clusters: [{ name, color, posts: [{ title, keyword, volume, template, wordCount, url, status }] }],
     links: [{ from, to, type }],
     meta: { totalPosts, totalClusters, totalLinks, estimatedWords }
   }
   ```
3. Replace the `CLUSTER_DATA` placeholder in the template with the actual JSON
4. Write the completed HTML file to the output directory
5. Inform user: "Open `cluster-map.html` in a browser to explore the interactive cluster map."

---


## Progressive Disclosure References (On-Demand)
- Detailed templates, extended examples, and deep-dive checklists have been moved to [references/detailed-guide.md](./references/detailed-guide.md) to keep context lean. Load that file via `view_file` only when needed.

## ⚠️ Gotchas (避坑指南)
- **避免關鍵字堆砌與門頁懲罰 (Doorway Pages)**：多據點或多機型頁面必須結合在地真實數據（如實收租金、分店地標、真實檢測數據），禁止僅替換地名或機型名稱。
- **Schema 與畫面一致性**：產出的 JSON-LD (`FAQPage`, `LocalBusiness`, `Product`) 內容必須與頁面可見文字 100% 一致，否則會觸發 Google 結構化資料人工處罰。
