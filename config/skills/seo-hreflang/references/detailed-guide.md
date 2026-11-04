# seo-hreflang — Detailed Reference & Extended Examples

## Hreflang Generation

### Process
1. **Detect languages**: Scan site for language indicators (URL path, subdomain, TLD, HTML lang attribute)
2. **Map page equivalents**: Match corresponding pages across languages/regions
3. **Validate language codes**: Verify all codes against ISO 639-1 and ISO 3166-1
4. **Generate tags**: Create hreflang tags for each page including self-referencing
5. **Verify return tags**: Confirm all relationships are bidirectional
6. **Add x-default**: Set fallback for each page set
7. **Output**: Generate implementation code (HTML, HTTP headers, or sitemap XML)

## Hreflang Sitemap Generation

### Sitemap with Hreflang
```xml
<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
        xmlns:xhtml="http://www.w3.org/1999/xhtml">
  <url>
    <loc>https://example.com/page</loc>
    <xhtml:link rel="alternate" hreflang="en-US" href="https://example.com/page" />
    <xhtml:link rel="alternate" hreflang="fr" href="https://example.com/fr/page" />
    <xhtml:link rel="alternate" hreflang="de" href="https://example.de/page" />
    <xhtml:link rel="alternate" hreflang="x-default" href="https://example.com/page" />
  </url>
  <url>
    <loc>https://example.com/fr/page</loc>
    <xhtml:link rel="alternate" hreflang="en-US" href="https://example.com/page" />
    <xhtml:link rel="alternate" hreflang="fr" href="https://example.com/fr/page" />
    <xhtml:link rel="alternate" hreflang="de" href="https://example.de/page" />
    <xhtml:link rel="alternate" hreflang="x-default" href="https://example.com/page" />
  </url>
</urlset>
```

Key rules:
- Include the `xmlns:xhtml` namespace declaration
- Every `<url>` entry must include ALL language alternates (including itself)
- Each alternate must appear as a separate `<url>` entry with its own full set
- Split at whichever comes first: 50,000 URLs or 50MB uncompressed per sitemap file

## Output

### Hreflang Validation Report

#### Summary
- Total pages scanned: XX
- Language variants detected: XX
- Issues found: XX (Critical: X, High: X, Medium: X, Low: X)

#### Validation Results
| Language | URL | Self-Ref | Return Tags | x-default | Status |
|----------|-----|----------|-------------|-----------|--------|
| en-US | https://... | ✅ | ✅ | ✅ | ✅ |
| fr | https://... | ❌ | ⚠️ | ✅ | ❌ |
| de | https://... | ✅ | ❌ | ✅ | ❌ |

### Generated Hreflang Tags
- HTML `<link>` tags (if HTML method chosen)
- HTTP header values (if header method chosen)
- `hreflang-sitemap.xml` (if sitemap method chosen)

### Recommendations
- Missing implementations to add
- Incorrect codes to fix
- Method migration suggestions (e.g., HTML to sitemap for scale)

## Cultural Adaptation Assessment

When analyzing a multi-language site, go beyond technical hreflang validation to assess
whether the content is culturally adapted for each target market.

Load `references/cultural-profiles.md` for pre-built profiles (DACH, Francophone, Hispanic, Japanese).

**Assessment steps:**
1. Identify all language versions and their target markets
2. Load the relevant cultural profile(s)
3. Check CTAs match cultural expectations (direct vs indirect)
4. Check trust signals are locale-appropriate (certifications, legal pages)
5. Check for foreign brand references on localized pages
6. Check number/date/currency formatting consistency
7. Flag cultural adaptation issues as Medium severity

**Output:** Cultural Adaptation Score per language version (0-100) with specific findings.

## Content Parity Audit

**Command:** `/seo hreflang audit <directory-or-url>`

Audit content parity across all language versions of a site or local content directory.

Load `references/content-parity.md` for the full parity matrix and scoring methodology.

**What it checks:**
- Page existence across all declared languages
- Section structure equivalence (H2/H3 count)
- SEO element parity (title, meta, schema localization)
- Word count ratio validation (DE should be 25-35% longer than EN, JA 10-25% shorter)
- Freshness tracking (stale translations detected via timestamps)
- Cultural marker scanning (foreign brands, wrong legal references, untranslated elements)

**Output:** Parity matrix table with per-page scores and prioritized action items.

## Locale Format Validation

Load `references/locale-formats.md` for number, date, currency, address, and phone format
reference tables per locale.

**Checks:**
- Number format consistency (e.g., "1,000.00" should be "1.000,00" on de-DE pages)
- Date format matches locale expectations
- Currency symbols and placement correct for target market
- Phone numbers use international format with correct country code

## Reference Files

Load on-demand as needed (do NOT load all at startup):
- `references/cultural-profiles.md`: DACH, Francophone, Hispanic, Japanese cultural adaptation profiles
- `references/locale-formats.md`: Number, date, currency, address, phone format tables per locale
- `references/content-parity.md`: Content parity audit methodology and scoring

## Error Handling

| Scenario | Action |
|----------|--------|
| URL unreachable (DNS failure, connection refused) | Report the error clearly. Do not guess site structure. Suggest the user verify the URL and try again. |
| No hreflang tags found | Report the absence. Check for other internationalization signals (subdirectories, subdomains, ccTLDs) and recommend the appropriate hreflang implementation method. |
| Invalid language/region codes detected | List each invalid code with the correct replacement. Provide a corrected hreflang tag set ready to implement. |
| Cultural profile not available for language | Use the Default Profile checklist from cultural-profiles.md. Note that assessment is based on general guidelines, not a pre-built profile. |
| Content parity directory empty | Report that no content files were found. Suggest verifying the directory path or providing a URL for live site analysis. |
