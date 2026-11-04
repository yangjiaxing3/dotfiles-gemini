---
name: seo-maps
description: "Use when tasks involve seo maps: 'Maps intelligence for local SEO: geo-grid rank tracking, GBP profile auditing via API, review..."
license: MIT
compatibility: "DataForSEO MCP for Tier 1+, Google Maps API for Tier 2"
version: "2.2.4"
---

# Maps Intelligence (March 2026)

Maps platform analysis for local businesses. Works with external APIs to assess
how a business appears on Google Maps, Bing Places, Apple Maps, and OpenStreetMap.

**Boundary with seo-local:** This skill analyzes the business on maps PLATFORMS
(via APIs). seo-local analyzes local SEO signals on the WEBSITE (via HTML fetch).
Do not duplicate seo-local on-page analysis. Recommend `/seo local <url>` for
website-level checks.

---

## Quick Reference

| Command | What it does | Tier |
|---------|-------------|------|
| `/seo maps <url>` | Full maps presence audit (auto-selects tier) | 0+ |
| `/seo maps grid <keyword> <location>` | Geo-grid rank scan (7x7, 1 keyword default) | 1+ |
| `/seo maps reviews <business> <location>` | Cross-platform review intelligence | 1+ |
| `/seo maps competitors <keyword> <location>` | Competitor radius mapping | 0+ |
| `/seo maps nap <business-name>` | Cross-platform NAP verification | 0+ |
| `/seo maps schema <business-name>` | Generate LocalBusiness JSON-LD from data | 0+ |
| `/seo maps gbp <business> <location>` | GBP completeness audit | 1+ |

---

## Three-Tier Capability Detection

Before any analysis, detect the available capability tier:

### Tier 0 (Free)
**Detection:** DataForSEO MCP tools NOT available.
**Capabilities:** Overpass API competitor discovery, Geoapify POI search, Nominatim geocoding, static GBP checklist, schema generation, cross-platform NAP guidance.
**Load:** `../seo/references/maps-free-apis.md`

### Tier 1 (DataForSEO)
**Detection:** `business_data_business_listings_search` MCP tool IS available.
**Capabilities:** Everything in Tier 0 PLUS geo-grid rank tracking, live GBP profile audit, review intelligence (velocity, sentiment, distribution), GBP post activity, Q&A data, Tripadvisor/Trustpilot reviews.
**Load:** `../seo/references/maps-api-endpoints.md`

### Tier 2 (DataForSEO + Google Maps Platform)
**Detection:** Tier 1 available AND Google Maps API key in environment.
**Capabilities:** Everything in Tier 1 PLUS Google Places details, real-time business status, AI-powered place summaries, photo analysis.
**Note:** Google ToS restricts storage to `place_id` only. Lat/lng cached 30 days max.

**Always communicate the detected tier to the user** at the start of analysis.

---

## Geo-Grid Rank Tracking (Tier 1+)

Simulates Google Maps searches from multiple GPS coordinates to show ranking
variation across a geographic area. Requires DataForSEO.

**Load:** `../seo/references/maps-geo-grid.md` for algorithm, SoLV formula, heatmap format.
**Load:** `../seo/references/maps-api-endpoints.md` for Maps SERP endpoint details.

### Workflow

1. Geocode business address to get center lat/lng
2. Generate grid points (default: 7x7, 5km radius) using Haversine offset formula
3. **Display cost estimate and ask for confirmation before proceeding**
4. Fire DataForSEO Maps SERP API calls with `location_coordinate` per grid point
5. Find target business rank at each point
6. Calculate SoLV: `(top_3_count / total_points) * 100`
7. Render ASCII heatmap in output

### Cost Warning (REQUIRED)

Before every geo-grid scan, display:
```
Geo-Grid Scan: [keyword] at [location]
Grid: 7x7 (49 points) | Keywords: [N] | Est. cost: $[amount]
DataForSEO credits will be consumed. Proceed?
```

---

## GBP Profile Audit (Tier 1 preferred, Tier 0 manual)

Audits the 25 fields that affect Google Business Profile quality and ranking.

**Load:** `../seo/references/maps-gbp-checklist.md` for full checklist and scoring.

> **AI & 2026 context (third-party reported):** **Ask Maps**, reported by AP News
> as a Gemini conversational Maps feature launched 2026-03-12 (iOS/Android,
> US + India). **AI Mode** (1B+ MAU, reported from Google I/O 2026 keynote coverage; not confirmed on a Google-owned source)
> increasingly surfaces 1-2 business local AI interfaces in third-party terminology, and **agentic
> booking/calling** for local services (home repair, beauty, pet care) rolls out
> to all US users summer 2026 (Google can call businesses on the user's behalf).
> New 2026 GBP API additions: review media URLs, recurring local-post scheduling,
> review reply-state/moderation, and invitation Place ID. Source:
> blog.google/products-and-platforms/products/search/search-io-2026/ ·
> developers.google.com/my-business/content/latest-updates

### Tier 1 Workflow

1. Fetch business profile via DataForSEO My Business Info API (keyword or CID)
2. Map API response fields to 25-field checklist
3. Score each field: Present + Optimized = 2pts, Present = 1pt, Missing = 0pts
4. Apply industry-specific weight multipliers
5. Normalize to 0-100 scale

### Tier 0 Workflow

1. Fetch the business website via WebFetch
2. Extract any visible GBP signals (Maps embed, place references, review widgets)
3. Apply static checklist based on detectable signals
4. Mark undetectable fields as "Unknown (requires DataForSEO for live data)"

---


## Progressive Disclosure References (On-Demand)
- Detailed templates, extended examples, and deep-dive checklists have been moved to [references/detailed-guide.md](./references/detailed-guide.md) to keep context lean. Load that file via `view_file` only when needed.

## ⚠️ Gotchas (避坑指南)
- **避免關鍵字堆砌與門頁懲罰 (Doorway Pages)**：多據點或多機型頁面必須結合在地真實數據（如實收租金、分店地標、真實檢測數據），禁止僅替換地名或機型名稱。
- **Schema 與畫面一致性**：產出的 JSON-LD (`FAQPage`, `LocalBusiness`, `Product`) 內容必須與頁面可見文字 100% 一致，否則會觸發 Google 結構化資料人工處罰。
