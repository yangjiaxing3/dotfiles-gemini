---
name: seo-unlighthouse
description: "'Use when tasks involve seo unlighthouse: Multi-page Lighthouse audit via the MIT-licensed Unlighthouse CLI. Free-tier alternat..."
version: "2.2.4"
compatibility: "Requires Node 18+ and the unlighthouse npm package. Run extensions/unlighthouse/install.sh to pre-warm."
---

# seo-unlighthouse

Run Lighthouse against every URL on a site (up to a configurable cap)
and aggregate the results. Useful when:

- PageSpeed Insights' free quota (25k QPD) isn't enough for a large site.
- You want offline / local CWV measurement (CI integration, restricted environments).
- You need a quick site-wide regression check after a deploy.

## Prerequisites

- Run `extensions/unlighthouse/install.sh` (no API key needed).
- Node 18+ on `$PATH`.

## Routing

| Command | Effect |
|---|---|
| `/seo unlighthouse <url>` | Mobile audit, up to 200 routes, JSON+HTML report in a temp dir |
| `/seo unlighthouse <url> --device desktop` | Desktop form factor |
| `/seo unlighthouse <url> --max-routes 50 --output-dir ./reports` | Cap + persist |

All flags forward to `scripts/unlighthouse_run.py` which handles
url_safety pre-flight and subprocess timeout management.

## Output handling

The wrapper reads `ci-result.json` from the Unlighthouse output dir and
returns it parsed. Aggregate fields:

- `score.performance` (median across audited routes)
- `score.accessibility`, `score.bestPractices`, `score.seo`
- Per-route breakdown is available in `<output_dir>/ci-result.json`

## Cross-skill delegation

- For single-URL field data (CrUX), use `seo-google psi` / `seo-google crux`.
- For LCP subpart decomposition on slow pages, use the
  `scripts/lcp_subparts.py` workflow (Phase C).

## ⚠️ Gotchas (避坑指南)
- **避免關鍵字堆砌與門頁懲罰 (Doorway Pages)**：多據點或多機型頁面必須結合在地真實數據（如實收租金、分店地標、真實檢測數據），禁止僅替換地名或機型名稱。
- **Schema 與畫面一致性**：產出的 JSON-LD (`FAQPage`, `LocalBusiness`, `Product`) 內容必須與頁面可見文字 100% 一致，否則會觸發 Google 結構化資料人工處罰。
