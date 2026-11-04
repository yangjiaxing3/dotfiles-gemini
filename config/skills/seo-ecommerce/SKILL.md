---
name: seo-ecommerce
description: "Use when tasks involve seo ecommerce: 'E-commerce SEO analysis: Google Shopping visibility, Amazon marketplace intelligence, pr..."
license: MIT
compatibility: "Enhanced with DataForSEO Merchant API (optional)"
version: "2.2.4"
---

# E-commerce SEO Analysis

Comprehensive product page optimization, marketplace intelligence, and
competitive pricing analysis. Works standalone (on-page + schema) and with
DataForSEO Merchant API for live Google Shopping and Amazon data.

## Commands

| Command | Purpose | DataForSEO? |
|---------|---------|-------------|
| `/seo ecommerce <url>` | Full e-commerce SEO analysis of a product page or store | Optional |
| `/seo ecommerce products <keyword>` | Google Shopping competitive analysis | Required |
| `/seo ecommerce gaps <domain>` | Keyword gap: organic vs Shopping visibility | Required |
| `/seo ecommerce schema <url>` | Product schema validation and enhancement | No |

---

## 1. Product Page Analysis (No DataForSEO Needed)

Fetch and parse any product page for on-page SEO quality.

### Workflow

```
1. "$HOME/.claude/skills/seo/bin/claude-seo" run render_page.py <url> --mode auto → raw/rendered HTML
2. "$HOME/.claude/skills/seo/bin/claude-seo" run parse_html.py --url <url>   → SEO elements
3. Analyze product-specific signals (below)
```

### Product SEO Checklist

#### Title Tag
- [ ] Contains primary product keyword
- [ ] Includes brand name
- [ ] Under 60 characters (no truncation in SERPs)
- [ ] Format: `[Product Name] - [Key Feature] | [Brand]`

#### Meta Description
- [ ] Contains product keyword + benefit
- [ ] Includes price or "from $XX" (triggers rich snippet interest)
- [ ] Call-to-action present (Shop now, Buy, Free shipping)
- [ ] Under 155 characters

#### Heading Structure
- [ ] Single H1 matching primary product name
- [ ] H2s for: Features, Specifications, Reviews, Related Products
- [ ] No duplicate H1 tags across product variants

#### Product Images
- [ ] Alt text includes product name + distinguishing feature
- [ ] File names are descriptive (not `IMG_001.jpg`)
- [ ] WebP format served (with JPEG fallback)
- [ ] At least 3 images per product (hero, detail, lifestyle)
- [ ] Image dimensions >= 800px for Google Shopping eligibility
- [ ] Lazy loading on below-fold images only

#### Internal Linking
- [ ] Breadcrumb navigation: Home > Category > Subcategory > Product
- [ ] Related products section (cross-sell / upsell)
- [ ] Link back to category page with keyword-rich anchor
- [ ] Reviews section links to full review page (if separate)

#### Content Quality
- [ ] Unique product description (not manufacturer copy-paste)
- [ ] Word count >= 200 for product description body
- [ ] Specs table present (not just prose)
- [ ] User reviews on-page (UGC signals)

### Scoring

| Category | Weight | Criteria |
|----------|--------|----------|
| Schema completeness | 25% | Required + recommended Product fields |
| Title & meta | 15% | Keyword placement, length, format |
| Image optimization | 20% | Alt text, format, sizing, count |
| Content quality | 20% | Unique description, specs, reviews |
| Internal linking | 10% | Breadcrumbs, related products, categories |
| Technical | 10% | Page speed, mobile rendering, canonical |

---

## 2. Google Shopping Intelligence (DataForSEO Merchant API)

Live competitive analysis from Google Shopping results.

### Cost Guardrail (MANDATORY)

Before EVERY Merchant API call:
```bash
"$HOME/.claude/skills/seo/bin/claude-seo" run dataforseo_costs.py check merchant_google_products_search
```

- `"status": "approved"` -- proceed
- `"status": "needs_approval"` -- show cost, ask user
- `"status": "blocked"` -- stop, inform user

After each call:
```bash
"$HOME/.claude/skills/seo/bin/claude-seo" run dataforseo_costs.py log merchant_google_products_search <cost>
```

### Workflow

```bash
# Product search: who sells what at what price
"$HOME/.claude/skills/seo/bin/claude-seo" run dataforseo_merchant.py search "<keyword>" --marketplace google

# Seller analysis: merchant ratings and dominance
"$HOME/.claude/skills/seo/bin/claude-seo" run dataforseo_merchant.py sellers "<keyword>"

# Normalize results for analysis
"$HOME/.claude/skills/seo/bin/claude-seo" run dataforseo_normalize.py results.json --module merchant
```

### Analysis Outputs

#### Pricing Intelligence
- Price distribution: min, max, median, P25, P75
- Price outliers (> 2 standard deviations from median)
- Price-to-rating correlation
- Currency normalization to USD (or user-specified)

#### Seller Landscape
- Top 10 sellers by listing count
- Merchant rating distribution
- Free shipping prevalence
- New vs established sellers

#### Product Listing Quality
- Title keyword patterns in top listings
- Average rating and review count benchmarks
- Image count per listing
- Availability status distribution

Load `references/marketplace-endpoints.md` for full API parameter details.

---


## Progressive Disclosure References (On-Demand)
- Detailed templates, extended examples, and deep-dive checklists have been moved to [references/detailed-guide.md](./references/detailed-guide.md) to keep context lean. Load that file via `view_file` only when needed.

## ⚠️ Gotchas (避坑指南)
- **避免關鍵字堆砌與門頁懲罰 (Doorway Pages)**：多據點或多機型頁面必須結合在地真實數據（如實收租金、分店地標、真實檢測數據），禁止僅替換地名或機型名稱。
- **Schema 與畫面一致性**：產出的 JSON-LD (`FAQPage`, `LocalBusiness`, `Product`) 內容必須與頁面可見文字 100% 一致，否則會觸發 Google 結構化資料人工處罰。
