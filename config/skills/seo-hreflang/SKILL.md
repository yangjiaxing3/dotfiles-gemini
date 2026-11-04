---
name: seo-hreflang
description: "Use when tasks involve seo hreflang: 'Hreflang and international SEO audit, validation, and generation. Detects common mistakes..."
license: MIT
version: "2.2.4"
---

# Hreflang & International SEO

Validate existing hreflang implementations or generate correct hreflang tags
for multi-language and multi-region sites. Supports HTML, HTTP header, and
XML sitemap implementations.

## Validation Checks

### 1. Self-Referencing Tags
- Every page must include an hreflang tag pointing to itself
- The self-referencing URL must exactly match the page's canonical URL
- Missing self-referencing tags cause Google to ignore the entire hreflang set

### 2. Return Tags
- If page A links to page B with hreflang, page B must link back to page A
- Every hreflang relationship must be bidirectional (A→B and B→A)
- Missing return tags invalidate the hreflang signal for both pages
- Check all language versions reference each other (full mesh)

### 3. x-default Tag
- Recommended when a selector/fallback URL exists: designates the fallback page for unmatched languages/regions
- Typically points to the language selector page or English version
- Only one x-default per set of alternates
- Must also have return tags from all other language versions

### 4. Language Code Validation
- Must use ISO 639-1 two-letter codes (e.g., `en`, `fr`, `de`, `ja`)
- An **optional ISO 15924 script subtag** is the documented, official mechanism
  for script: `zh-Hant` (Traditional) / `zh-Hans` (Simplified). Script may
  combine with a region, e.g. `zh-Hans-US` is valid (language + script + region).
- Common errors:
  - `eng` instead of `en` (ISO 639-2, not valid for hreflang)
  - `jp` instead of `ja` (incorrect code for Japanese)
  - `zh` is valid but ambiguous for script-specific pages; prefer `zh-Hans` or `zh-Hant` when targeting a script

### 5. Region Code Validation
- Optional region qualifier uses ISO 3166-1 Alpha-2 (e.g., `en-US`, `en-GB`, `pt-BR`)
- Format: `language-REGION` (lowercase language, uppercase region)
- A **country code alone is invalid**, you cannot specify a region without a
  language (Google's own bad example is `be`, which is actually the Belarusian
  *language* code, not Belgium).
- Common errors:
  - `en-uk` instead of `en-GB` (UK is not a valid ISO 3166-1 region code)
  - `EU` / `UN` as a region (not valid ISO 3166-1 values)
  - `es-LA` (Latin America is not a country; use specific countries)
  - Region without language prefix

### 5b. Geo-targeting signal hierarchy
- Practical locale-signal heuristic: **ccTLD > hreflang annotations >
  server location/IP > addresses/language/currency/Business Profile**. Do not
  present this as a confirmed Google ranking order. hreflang is a
  **hint, not a directive**. Google **ignores** locational meta tags and
  HTML geotargeting attributes.
- The Search Console **International Targeting report and the manual
  country-targeting setting were removed in 2022**, do **not** recommend setting
  country targeting in GSC; hreflang is the remaining lever.

### 6. Canonical URL Alignment
- Hreflang tags must only appear on canonical URLs
- If a page has `rel=canonical` pointing elsewhere, hreflang on that page is ignored
- The canonical URL and hreflang URL must match exactly (including trailing slashes)
- Non-canonical pages should not be in any hreflang set

### 7. Protocol Consistency
- All URLs in an hreflang set must use the same protocol (HTTPS or HTTP)
- Mixed HTTP/HTTPS in hreflang sets causes validation failures
- After HTTPS migration, update all hreflang tags to HTTPS

### 8. Cross-Domain Support
- Hreflang works across different domains (e.g., example.com and example.de)
- Cross-domain hreflang requires return tags on both domains
- Use Google Search Console verification for monitoring or cross-site sitemap submission when needed
- Sitemap-based implementation recommended for cross-domain setups

## Common Mistakes

| Issue | Severity | Fix |
|-------|----------|-----|
| Missing self-referencing tag | Critical | Add hreflang pointing to same page URL |
| Missing return tags (A→B but no B→A) | Critical | Add matching return tags on all alternates |
| Missing x-default when fallback behavior is required | Medium | Add x-default pointing to fallback/selector page |
| Invalid language code (e.g., `eng`) | High | Use ISO 639-1 two-letter codes |
| Invalid region code (e.g., `en-uk`) | High | Use ISO 3166-1 Alpha-2 codes |
| Hreflang on non-canonical URL | High | Move hreflang to canonical URL only |
| HTTP/HTTPS mismatch in URLs | Medium | Standardize all URLs to HTTPS |
| Trailing slash inconsistency | Medium | Match canonical URL format exactly |
| Hreflang in both HTML and sitemap | Low | Choose one method (sitemap preferred for large sites) |
| Language without region when needed | Low | Add region qualifier for geo-targeted content |

## Implementation Methods

### Method 1: HTML Link Tags
Best for: Sites with <50 language/region variants per page.

```html
<link rel="alternate" hreflang="en-US" href="https://example.com/page" />
<link rel="alternate" hreflang="en-GB" href="https://example.co.uk/page" />
<link rel="alternate" hreflang="fr" href="https://example.com/fr/page" />
<link rel="alternate" hreflang="x-default" href="https://example.com/page" />
```

Place in `<head>` section. Every page must include all alternates including itself.

### Method 2: HTTP Headers
Best for: Non-HTML files (PDFs, documents).

```
Link: <https://example.com/page>; rel="alternate"; hreflang="en-US",
      <https://example.com/fr/page>; rel="alternate"; hreflang="fr",
      <https://example.com/page>; rel="alternate"; hreflang="x-default"
```

Set via server configuration or CDN rules.

### Method 3: XML Sitemap (Recommended for large sites)
Best for: Sites with many language variants, cross-domain setups, or 50+ pages.

See Hreflang Sitemap Generation section below.

### Method Comparison
| Method | Best For | Pros | Cons |
|--------|----------|------|------|
| HTML link tags | Small sites (<50 variants) | Easy to implement, visible in source | Bloats `<head>`, hard to maintain at scale |
| HTTP headers | Non-HTML files | Works for PDFs, images | Complex server config, not visible in HTML |
| XML sitemap | Large sites, cross-domain | Scalable, centralized management | Not visible on page, requires sitemap maintenance |


## Progressive Disclosure References (On-Demand)
- Detailed templates, extended examples, and deep-dive checklists have been moved to [references/detailed-guide.md](./references/detailed-guide.md) to keep context lean. Load that file via `view_file` only when needed.

## ⚠️ Gotchas (避坑指南)
- **避免關鍵字堆砌與門頁懲罰 (Doorway Pages)**：多據點或多機型頁面必須結合在地真實數據（如實收租金、分店地標、真實檢測數據），禁止僅替換地名或機型名稱。
- **Schema 與畫面一致性**：產出的 JSON-LD (`FAQPage`, `LocalBusiness`, `Product`) 內容必須與頁面可見文字 100% 一致，否則會觸發 Google 結構化資料人工處罰。
