---
name: seo-geo
description: "Use when tasks involve seo geo: 'Optimize content for AI Overviews (formerly SGE), ChatGPT web search, Perplexity, and other AI..."
license: MIT
version: "2.2.4"
---

# AI Search / GEO Optimization (May 2026)

## Primary Source: Google's AI Optimization Guide

Google's official position, published under Search Central docs:

> "Optimizing for generative AI search is **still SEO** from Google's
> perspective. AEO and GEO are rebranded labels for the same work."

Read `references/google-ai-optimization-guide.md` for the full synthesis,
myth-busting list (`llms.txt`, chunking, AI-rephrasing, mention-farming,
all rejected by Google as ineffective), and the Who/How/Why test for
content quality.

Audits should frame GEO findings as **SEO fundamentals applied to AI-search
surfaces**, not as a separate optimization discipline. When community
recommendations contradict Google's primary source, defer to Google and note
the contradiction in the report.

## Key Statistics

| Metric | Value | Source |
|--------|-------|--------|
| AI Overviews reach | 2.5 billion+ monthly active users, reported from Google I/O 2026 keynote coverage; not confirmed on a Google-owned source; 200+ countries | Third-party I/O reporting |
| AI Overviews query coverage | ~50% of queries (third-party measurement; varies by country) | Industry data |
| AI Mode monthly users | 1B+, reported from Google I/O 2026 keynote coverage; not confirmed on a Google-owned source | Third-party I/O reporting |
| AI Mode model | custom version of Gemini 2.5 | Google |
| AI-referred sessions growth | 527% (Jan-May 2025) | SparkToro |
| ChatGPT weekly active users | 900 million | OpenAI |
| Perplexity monthly queries | 500+ million | Perplexity |

## Critical Insight: Brand Mentions > Backlinks

**Brand mentions correlate 3x more strongly with AI visibility than backlinks.**
(Ahrefs December 2025 study of 75,000 brands)

| Signal | Correlation with AI Citations |
|--------|------------------------------|
| YouTube mentions | ~0.737 (strongest) |
| Reddit mentions | High |
| Wikipedia presence | High |
| LinkedIn presence | Moderate |
| Domain Rating (backlinks) | ~0.266 (weak) |

**Only 11% of domains** are cited by both ChatGPT and Google AI Overviews for the same query, so platform-specific optimization is essential.

---

## GEO Analysis Criteria (Updated)

### 1. Citability Score (25%)

**Optimal passage length: 134-167 words** for AI citation. And **~44% of AI
citations come from the first 30% of a page** (SE Ranking study), front-load
your most citable, self-contained answer rather than burying it below the fold.

**Strong signals:**
- Clear, quotable sentences with specific facts/statistics
- Self-contained answer blocks (can be extracted without context)
- Direct answer in first 40-60 words of section
- Claims attributed with specific sources
- Definitions following "X is..." or "X refers to..." patterns
- Unique data points not found elsewhere

**Weak signals:**
- Vague, general statements
- Opinion without evidence
- Buried conclusions
- No specific data points

### 2. Structural Readability (20%)

**92% of AI Overview citations come from top-10 ranking pages**, but 47% come from pages ranking below position 5, demonstrating different selection logic.

**Strong signals:**
- Clean H1->H2->H3 heading hierarchy
- Question-based headings (matches query patterns)
- Short paragraphs (2-4 sentences)
- Tables for comparative data
- Ordered/unordered lists for step-by-step or multi-item content
- FAQ sections with clear Q&A format

**Weak signals:**
- Wall of text with no structure
- Inconsistent heading hierarchy
- No lists or tables
- Information buried in paragraphs

### 3. Multi-Modal Content (15%)

Content with multi-modal elements sees **156% higher selection rates**.

**Check for:**
- Text + relevant images
- Video content (embedded or linked)
- Infographics and charts
- Interactive elements (calculators, tools)
- Structured data supporting media

### 4. Authority & Brand Signals (20%)

**Strong signals:**
- Author byline with credentials
- Publication date and last-updated date
- **Recency**, content under 3 months old is ~3x more likely to be cited in AI answers; pages left stale 6+ months lose citation eligibility (SE Ranking, 1.3M-citation study). A scheduled refresh program is one of the highest-leverage GEO plays.
- Citations to primary sources (studies, official docs, data)
- Organization credentials and affiliations
- Expert quotes with attribution
- Entity presence in Wikipedia, Wikidata
- Mentions on Reddit, YouTube, LinkedIn

**Weak signals:**
- Anonymous authorship
- No dates
- No sources cited
- No brand presence across platforms

### 5. Technical Accessibility (20%)

**AI crawlers do NOT execute JavaScript.** Server-side rendering is critical.

**Check for:**
- Server-side rendering (SSR) vs client-only content
- AI crawler access in robots.txt
- llms.txt file presence and configuration
- RSL 1.0 licensing terms

---


## Progressive Disclosure References (On-Demand)
- Detailed templates, extended examples, and deep-dive checklists have been moved to [references/detailed-guide.md](./references/detailed-guide.md) to keep context lean. Load that file via `view_file` only when needed.

## ⚠️ Gotchas (避坑指南)
- **避免關鍵字堆砌與門頁懲罰 (Doorway Pages)**：多據點或多機型頁面必須結合在地真實數據（如實收租金、分店地標、真實檢測數據），禁止僅替換地名或機型名稱。
- **Schema 與畫面一致性**：產出的 JSON-LD (`FAQPage`, `LocalBusiness`, `Product`) 內容必須與頁面可見文字 100% 一致，否則會觸發 Google 結構化資料人工處罰。
