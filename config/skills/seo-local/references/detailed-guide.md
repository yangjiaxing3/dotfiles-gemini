# seo-local — Detailed Reference & Extended Examples

  3. Any visible GBP data
  - Flag any discrepancies between these three sources
- Citation presence on Tier 1 directories (check via WebFetch or site: search patterns):
  - Google Business Profile signals on page
  - Yelp: `site:yelp.com "Business Name"`
  - BBB: `site:bbb.org "Business Name"`
  - Facebook business page references
- **Apple Maps / Apple business listings** awareness: claim and maintain Apple listings; treat Apple Business unified-platform launch/rename claims as TechRadar-sourced and verify against Apple primary before asserting.
- Bing Places awareness (powers ChatGPT, Copilot, Alexa -- recommend claiming and optimizing)
- Industry-specific directory recommendations: load `../seo/references/local-schema-types.md` for per-vertical citation sources
- Data aggregator awareness: Data Axle, Foursquare, Neustar/TransUnion (recommend submission for downstream distribution)

**Scoring guide:**
- Full: Consistent NAP across page/schema, Tier 1 citations detected, industry directories present
- Partial: NAP present but inconsistencies, some citations missing
- Low: NAP discrepancies, no detectable citations, no schema address

### 5. Local Schema Markup (10%)

Schema is NOT a direct ranking factor (John Mueller confirmed). But enables rich results (43% CTR increase, Webstix case study) and helps AI systems parse business information.

**Check for:**
- LocalBusiness schema presence (extract JSON-LD blocks)
- Required properties: `name`, `address` with PostalAddress sub-properties
- Recommended properties: `geo` (minimum 5 decimal places, Confirmed), `openingHoursSpecification`, `telephone`, `url`, `priceRange` (<100 chars), `image`, `aggregateRating`
- **Correct subtype for industry** -- load `../seo/references/local-schema-types.md`:
  - Restaurant using `Restaurant` not generic `LocalBusiness`
  - Legal using `LegalService` not deprecated `Attorney`
  - Auto dealer using `AutoDealer` not deprecated `VehicleListing`
  - Healthcare using `MedicalClinic`/`Hospital`/`Dentist` not generic `MedicalBusiness`
- SAB-specific: `areaServed` with named cities (recommended, not in Google's official list but Schema.org supported)
- Multi-location: each location page has own LocalBusiness with unique `@id`, linked via `branchOf` to Organization on homepage
- Industry-specific schema patterns (per `../seo/references/local-schema-types.md`):
  - Restaurant: Menu + MenuSection + MenuItem + ReserveAction (note: Reservation/Order actions are not Google-supported rich results; value is machine-readable business data)
  - Healthcare: Physician (Person) + MedicalSpecialty + sameAs to NPI
  - Legal: LegalService + Person + Service (practice areas)
  - Home Services: Subtype + areaServed + Service
  - Real Estate: RealEstateAgent + Person + RealEstateListing
  - Automotive: AutoDealer + Car + Offer (separate dept schemas)

**Scoring guide:**
- Full: Correct subtype, all recommended properties, industry-specific patterns, valid JSON-LD
- Partial: LocalBusiness present but generic type or missing recommended properties
- Low: No local schema, or schema with errors/placeholder content

### 6. Local Link & Authority Signals (10%)

Links declining for local pack but remain **~26% of local organic ranking** (Whitespark 2026, #2 factor group). "Best of" list placements = **#1 AI visibility citation factor**.

**Check for:**
- Local backlink indicators detectable from page:
  - Chamber of Commerce mentions or links (high Trust Flow, ~80% more consumer visits, GlueUp)
  - BBB accreditation/badge (Google uses BBB for business verification)
  - Local news/press mentions
  - Community involvement signals (sponsorships, local events, partnerships)
- "Best of" list presence (top AI visibility factor per Whitespark 2026)
- Digital PR signals: 66.2% of PR practitioners now track AI citations as KPI (BuzzStream 2026)
- Brand mentions correlate **3x more strongly** with AI visibility than traditional backlinks (Ahrefs: 0.664 vs 0.218 correlation)
- Link velocity benchmark: 5-10 quality local links/month for small businesses (consensus)

**Scoring guide:**
- Full: Local authority signals visible (chamber, BBB, press), community involvement evident
- Partial: Some authority signals but limited local link indicators
- Low: No detectable local authority signals

---

## AI Search Impact on Local

**Do not duplicate seo-geo analysis.** Provide local-specific AI context and recommend `/seo geo <url>` for full analysis.

Key local AI facts:
- AI Overviews appear on up to 68% of local searches (Whitespark Q2 2025)
- ChatGPT converts at 15.9% vs Google organic at 1.76% (Seer Interactive)
- 3 of top 5 AI visibility factors are citation-related (Whitespark 2026)
- ChatGPT does NOT access GBP directly -- sources from Bing index, Yelp, TripAdvisor, BBB, Reddit
- Bing Places is critical: powers ChatGPT, Copilot, Alexa
- Third-party observed local AI interface changes (mobile US) may show only 1-2 businesses, 32% fewer shown (Sterling Sky)

**Recommendation**: Run `/seo geo <url>` for comprehensive AI search visibility analysis including citability scoring, llms.txt check, and brand mention audit.

---

## Reference Files

Load on-demand as needed:
- `../seo/references/local-seo-signals.md`: Ranking factors, review benchmarks, citation tiers, GBP feature status, algorithm updates
- `../seo/references/local-schema-types.md`: LocalBusiness subtypes by industry, schema patterns, citation sources per vertical

---

## Output

Generate `LOCAL-SEO-ANALYSIS-{domain}.md` with:

1. **Local SEO Score: XX/100** with dimension breakdown table
2. **Business type**: Brick-and-mortar / SAB / Hybrid
3. **Industry vertical detected** + industry-specific findings
4. **GBP optimization checklist** (detected signals vs missing)
5. **Review health snapshot** (rating, count, velocity indicators, response patterns)
6. **NAP consistency audit** (page vs schema discrepancies, cross-source comparison)
7. **Citation presence check** (Tier 1 directory status)
8. **Local schema status** (present/missing/malformed + ready-to-use fix)
9. **Location page quality** (if multi-location: unique content %, doorway risk, store locator)
10. **Top 10 prioritized actions** (Critical > High > Medium > Low)
11. **Limitations disclaimer**: What this analysis could NOT assess (geo-grid ranking, Domain Authority, comprehensive backlinks, GBP Insights data, real-time local pack position) and which paid tools can fill those gaps

---

## Quick Wins

1. Claim and optimize Apple Maps / Apple business listings; verify any Apple Business launch/rename claim against Apple primary first
2. Claim and optimize Bing Places (powers ChatGPT, Copilot, Alexa)
3. Fix any NAP discrepancies between page, schema, and GBP
4. Add LocalBusiness schema with correct industry subtype
5. Add `geo` coordinates with 5+ decimal precision
6. Ensure phone number uses `tel:` link for click-to-call
7. Add city + service keyword to title tag and H1

## Medium Effort

1. Create dedicated page for each core service (Whitespark: #1 local organic factor)
2. Build review generation strategy maintaining 18-day minimum cadence
3. Submit to three data aggregators (Data Axle, Foursquare, Neustar/TransUnion) for downstream distribution
4. Claim industry-specific directory listings (per vertical recommendations)
5. Add industry-specific schema patterns (Menu for restaurants, Physician for healthcare, etc.)
6. Implement hub-and-spoke internal linking for service/location pages

## High Impact

1. Build local digital PR strategy targeting "best of" lists (#1 AI visibility factor)
2. Develop unique, non-swappable content for each location page (>60% unique)
3. Establish presence on platforms ChatGPT sources from (Yelp, TripAdvisor, BBB, Reddit)
4. Pursue Chamber of Commerce and BBB membership (authority + verification signals)
5. Create community involvement content (sponsorships, local events, partnerships)

---

## DataForSEO Integration (Optional)

If DataForSEO MCP tools are available, use `business_data_business_listings_search` for live GBP/business-listing data extraction and citation auditing across directories, and `serp_organic_live_advanced` for real-time local pack positions.

---

## Error Handling

| Scenario | Action |
|----------|--------|
| URL unreachable (DNS failure, connection refused) | Report the error clearly. Do not guess site content. Suggest the user verify the URL and try again. |
| No local signals detected on page | Report that no local business indicators were found. Suggest the user confirm this is a local business and provide the GBP listing URL if available. |
| NAP not found in page HTML | Check schema and meta tags. If still absent, flag as Critical issue. Recommend adding visible NAP to footer and contact page. |
| Industry vertical unclear | Present the top two detected verticals with supporting signals. Ask the user to confirm before applying industry-specific recommendations. |
| Multi-location with 50+ location pages | Apply the quality gates from seo orchestrator: WARNING at 30+ pages (enforce 60%+ unique), HARD STOP at 50+ pages (require user justification before continuing). |

## FLOW Framework Integration

For prompt-guided local optimization, use `/seo flow local <url>`, FLOW's 11 local-stage prompts cover GBP optimization, meta descriptions, title tags, and structured local audit workflows.
