# seo-ecommerce — Detailed Reference & Extended Examples

## 3. Amazon Marketplace (DataForSEO)

Cross-marketplace intelligence comparing Google Shopping and Amazon.

### Cost Guardrail (MANDATORY)

```bash
"$HOME/.claude/skills/seo/bin/claude-seo" run dataforseo_costs.py check merchant_amazon_products_search
```

Amazon endpoints are in the `warn_endpoints` set -- always requires user approval.

### Workflow

```bash
# Amazon product search
"$HOME/.claude/skills/seo/bin/claude-seo" run dataforseo_merchant.py search "<keyword>" --marketplace amazon

# Cross-marketplace comparison
"$HOME/.claude/skills/seo/bin/claude-seo" run dataforseo_merchant.py compare "<keyword>"
```

### Cross-Marketplace Report

| Metric | Google Shopping | Amazon |
|--------|---------------|--------|
| Avg price | $ | $ |
| Median rating | X.X | X.X |
| Avg review count | N | N |
| Top seller share | % | % |
| Free shipping % | % | % |

---

## 4. Marketplace Keyword Gaps

Identify mismatches between organic and Shopping visibility.

### Workflow

1. Fetch organic rankings via seo-dataforseo:
   `dataforseo_labs_google_ranked_keywords` for domain
2. Fetch Google Shopping presence via Merchant API:
   `merchant_google_products_search` for top organic keywords
3. Cross-reference results

### Gap Types

| Gap Type | Meaning | Action |
|----------|---------|--------|
| **Organic Only** | Ranks organically but no Shopping ads | Create Google Merchant Center feed, bid on these keywords |
| **Shopping Only** | Shopping visibility but weak/no organic | Create content (buying guides, comparison pages) for these keywords |
| **Both Present** | Visible in both channels | Optimize: ensure price consistency, enhance schema |
| **Neither** | No visibility in either | Low priority unless high volume |

### Output Format

```
## Keyword Gap Analysis: example.com

### Opportunities: Organic → Shopping (12 keywords)
| Keyword | Organic Pos | Volume | CPC | Recommended Action |
|---------|------------|--------|-----|-------------------|

### Opportunities: Shopping → Organic (8 keywords)
| Keyword | Shopping Rank | Volume | CPC | Content Type Needed |
|---------|-------------|--------|-----|-------------------|
```

---

## 5. Product Schema Enhancement

Validate and generate Product schema following Google's current requirements.

### Confirmed Required Properties (Google Merchant)

Confirmed required fields are `name`, `image`, and `offers`; use `Offer`, not `AggregateOffer`, for merchant listings.

```json
{
  "@context": "https://schema.org",
  "@type": "Product",
  "name": "",
  "image": [""],
  "offers": {
    "@type": "Offer",
    "url": "",
    "priceCurrency": "USD",
    "price": "0.00",
    "availability": "https://schema.org/InStock"
  }
}
```

### Recommended Properties (Enhance Rich Results)

- `sku` -- product identifier
- `description`, `brand`, `offers.seller` -- recommended context fields
- `gtin13` / `gtin14` / `mpn` -- global trade identifiers
- `aggregateRating` -- star rating + review count
- `review` -- individual reviews (minimum 1)
- `color`, `material`, `size` -- variant attributes
- `shippingDetails` -- ShippingDetails with rate and delivery time (merchant-level shipping via `ShippingService` is also supported; shipping/returns can be set in Search Console without a Merchant Center account)
- `hasMerchantReturnPolicy` -- MerchantReturnPolicy with type and days
- `hasAdultConsideration` -- **required for adult-oriented products** (added 2026-05-20 to Product variant / Merchant listing); Google Search supports only the value `https://schema.org/SexualContentConsideration`

### Validation Rules

1. `price` must be a number string, not "$29.99" (no currency symbol)
2. `availability` must use full Schema.org URL enum
3. `image` should be array with >= 1 high-res image URL
4. `priceCurrency` must be ISO 4217 (USD, EUR, GBP)
5. If `brand` is present, `brand.name` must not be empty or "N/A"
6. Dates in `priceValidUntil` must be ISO 8601
7. If `aggregateRating` present: `ratingValue` and `reviewCount` required

### Schema Scoring

| Completeness | Score |
|-------------|-------|
| All required fields | 50/100 |
| + aggregateRating | 65/100 |
| + sku/gtin/mpn | 75/100 |
| + shippingDetails | 85/100 |
| + merchantReturnPolicy | 90/100 |
| + reviews (3+) | 100/100 |

---

## Cross-Skill Integration

| Skill | Integration Point |
|-------|------------------|
| **seo-schema** | Delegates Product schema generation; reuses validation logic |
| **seo-images** | Product image audit (alt text, format, dimensions), plus `DigitalSourceType: TrainedAlgorithmicMedia` IPTC label for AI-generated product images (Merchant Center requirement) |
| **seo-content** | Product description E-E-A-T and uniqueness analysis |
| **seo-dataforseo** | Organic keyword rankings for gap analysis |
| **seo-technical** | Core Web Vitals for product pages (LCP on hero image) |
| **seo-google** | GSC indexation + Performance data for product URLs (NOT Merchant Center feed validation, that is done in Merchant Center / the **Merchant API**; the legacy Content API for Shopping sunsets 2026-08-18) |

## UCP: Universal Commerce Protocol (live)

Google-initiated open standard (co-developed with Shopify, Etsy, Wayfair,
Target, Walmart; payment partners Visa/Mastercard/Stripe/Adyen/Amex) for
letting AI agents discover, negotiate, and transact with merchants without
one-off integrations. Google confirms a first reference implementation for
conversational buying in AI Mode in Search. Broader Universal Cart rollout
details are reported from Google I/O 2026 keynote coverage; not confirmed on a
Google-owned source. ucp.dev lists **2026-04-08** as the latest release in its
**date-based versioning** scheme, not `1.0`; two integration paths: **Native**
(default) and **Embedded** (approved merchants). Pairs with **AP2** (reportedly
moving toward FIDO governance). Canonical: developers.google.com/merchant/ucp
and ucp.dev.

Merchants already on **Google Merchant Center** with clean Product schema can
declare a UCP profile at `/.well-known/ucp` listing capabilities
(`dev.ucp.shopping.checkout`, `.fulfillment`, `.discount`). See
`references/ucp-universal-commerce-protocol.md` for audit criteria,
capability examples, and the relationship to AP2 (Agent Payments Protocol).

### Audit command

```bash
# Discover and validate the UCP profile
"$HOME/.claude/skills/seo/bin/claude-seo" run ucp_check.py https://store.example.com --json

# With endpoint reachability probes (HEAD each declared capability)
"$HOME/.claude/skills/seo/bin/claude-seo" run ucp_check.py https://store.example.com --probe-endpoints --json
```

The script returns: profile presence, version, declared capabilities,
structural issues (missing fields, unknown capability IDs), and (with
`--probe-endpoints`) per-endpoint reachability. SSRF-blocked endpoints are
reported explicitly. Missing profile is reported as opportunity, not failure.
UCP itself is live; what's early is broad merchant adoption. Flag a literal
`"version": "1.0"` as invalid (UCP versions are date-based, e.g. `2026-04-08`).

---

## Error Handling

| Error | Cause | Response |
|-------|-------|----------|
| No Product schema found | Page lacks JSON-LD | Analyze page content, generate recommended schema |
| DataForSEO credentials missing | Env vars not set | Run analysis without marketplace data, note limitation |
| Cost check blocked | Daily budget exceeded | Inform user, offer free-only analysis |
| Empty Shopping results | No products for keyword | Suggest broader keyword, check location settings |
| Amazon API timeout | Network/rate limit | Retry with backoff, fall back to Google-only |
| Invalid URL | Malformed input | Validate via `google_auth.validate_url()`, show error |
| Non-product page | URL is category/homepage | Detect page type, suggest `/seo ecommerce schema` instead |

---

## Output Template

```
## E-commerce SEO Report: [URL or Keyword]

### Overall Score: XX/100

### Product Page SEO
- Schema Completeness: XX/100
- Title & Meta: XX/100
- Image Optimization: XX/100
- Content Quality: XX/100
- Internal Linking: XX/100

### Marketplace Intelligence (if DataForSEO available)
- Google Shopping Listings: N products found
- Price Range: $XX - $XX (median: $XX)
- Top Seller: [name] (XX% market share)
- Amazon Comparison: [available/not checked]

### Top Recommendations
1. [Critical] ...
2. [High] ...
3. [Medium] ...

Generate a PDF report? Use `/seo google report`
```
