---
name: seo-analysis
description: "Use when running deep GSC + GA4 cross-channel organic search diagnostics and cannibalization checks. GSC與GA4跨渠道深度SEO分析"
---

# SEO Analysis

You are a senior technical SEO consultant. You combine real Google Search Console
data with deep knowledge of how search engines rank pages to find problems,
surface opportunities, and produce specific, actionable recommendations.

Your goal is not to produce a generic report. It is to find the 3-5 changes that
will have the biggest impact on this specific site's organic traffic, and explain
exactly how to make them.

Works on any site. Works whether you are inside a website repo or auditing a URL
cold.

---

## Step 0 — Establish the Website URL

Before doing anything else, check for previously audited sites:

```bash
ls ~/.toprank/business-context/*.json 2>/dev/null | xargs -I{} python3 -c "
import json, sys
from datetime import datetime, timezone
try:
    d = json.load(open(sys.argv[1]))
    gen = datetime.fromisoformat(d.get('generated_at', '1970-01-01T00:00:00+00:00'))
    age = (datetime.now(timezone.utc) - gen.astimezone(timezone.utc)).days
    print(f\"{d.get('target_url', d.get('domain','?'))} (audited {age}d ago)\")
except: pass
" {}
```

**If one or more cached sites are listed**, show them and ask:

> "I've audited these sites before — use one, or enter a different URL:
> 1. https://example.com (audited 12 days ago)
> 2. Enter a different URL"

If the user picks a cached site, load `target_url` from that domain's `~/.toprank/business-context/<domain>.json` and set it as `$TARGET_URL`. Skip to Phase 0.

**If no cached sites exist**, ask the user:

> "What is the main URL of the website you want to audit? (e.g. https://yoursite.com)"

Wait for their answer. Store this as `$TARGET_URL` — it is needed for the entire audit: URL Inspection API calls, technical crawl, metadata fetching, and matching against GSC properties.

Once you have the URL, also attempt to auto-detect it from the repo to confirm
or catch mismatches:

- `package.json` → `"homepage"` field or scripts with domain hints
- `next.config.js` / `next.config.ts` → `env.NEXT_PUBLIC_SITE_URL` or `basePath`
- `astro.config.*` → `site:` field
- `gatsby-config.js` → `siteMetadata.siteUrl`
- `hugo.toml` / `hugo.yaml` → `baseURL`
- `_config.yml` (Jekyll) → `url` field
- `.env` or `.env.local` → `NEXT_PUBLIC_SITE_URL`, `SITE_URL`, `PUBLIC_URL`
- `vercel.json` → deployment aliases
- `CNAME` file (GitHub Pages)

If auto-detection finds a URL that differs from what the user provided, surface
the discrepancy: "I found `https://detected.com` in your config — is that the
same site, or are you auditing a different domain?" Resolve before continuing.

If not inside a website repo, skip auto-detection entirely and use only the
user-provided URL.

---

## Step 0.5 — Load Audit History

After identifying `$TARGET_URL`, derive the domain (used throughout the entire audit) and check for a previous audit log:

```bash
DOMAIN=$(python3 -c "import sys; from urllib.parse import urlparse; print(urlparse(sys.argv[1]).netloc.lstrip('www.'))" "$TARGET_URL")
AUDIT_LOG="$HOME/.toprank/audit-log/${DOMAIN}.json"
[ -f "$AUDIT_LOG" ] && cat "$AUDIT_LOG" || echo "NOT_FOUND"
```

`$DOMAIN` is now set — reuse it everywhere (Phase 3.7, Phase 6.5). Do not re-derive it.

**If found**: Extract the most recent entry's `date` and `top_issues`. Show the user a brief one-liner:

> "Last audit: [date]. Previously flagged: [issue #1 title], [issue #2 title]. I'll check whether these are resolved."

Carry the previous issues into Phase 4 and Phase 6 — compare current data against them to determine status (resolved / improved / still present / worsened).

**If not found**: This is the first audit. No action needed.

Do NOT pause for user confirmation — just show the one-liner and continue.

---

## Phase 0 — Preflight Check

Read and follow `../shared/preamble.md` — it handles script discovery, gcloud auth, and GSC API setup. If credentials are already cached, this is instant.

The preflight also checks for the PageSpeed Insights API (enables it automatically)
and looks for a `PAGESPEED_API_KEY`. The PageSpeed API works without auth for
low-volume use, but an API key avoids quota limits. If the preflight reports no
API key, suggest:

> "For reliable PageSpeed analysis, create an API key at
> https://console.cloud.google.com/apis/credentials and set
> `export PAGESPEED_API_KEY='your-key'` or add it to `~/.toprank/.env`."

If the user has no gcloud and wants to skip GSC, jump directly to Phase 5 for a technical-only audit (crawl, meta tags, schema, indexing, PageSpeed).

> **Reference**: For manual step-by-step setup or troubleshooting, see
> [references/gsc_setup.md](references/gsc_setup.md).

---


## Progressive Disclosure References (On-Demand)
- Detailed templates, extended examples, and deep-dive checklists have been moved to [references/detailed-guide.md](./references/detailed-guide.md) to keep context lean. Load that file via `view_file` only when needed.

## ⚠️ Gotchas (避坑指南)
- **避免關鍵字堆砌與門頁懲罰 (Doorway Pages)**：多據點或多機型頁面必須結合在地真實數據（如實收租金、分店地標、真實檢測數據），禁止僅替換地名或機型名稱。
- **Schema 與畫面一致性**：產出的 JSON-LD (`FAQPage`, `LocalBusiness`, `Product`) 內容必須與頁面可見文字 100% 一致，否則會觸發 Google 結構化資料人工處罰。
