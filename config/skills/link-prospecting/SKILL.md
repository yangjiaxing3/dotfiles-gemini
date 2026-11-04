---
name: link-prospecting
description: "Use when finding high-authority link prospects and drafting outreach from SERP and backlink signals. 外鏈潛在客戶開發與公關聯繫"
---

# OpenSEO Link Prospecting

## Goal

Find realistic pages, sites, and authors that might reference the user's page, product, study, guide, or tool. Use OpenSEO for prospect discovery, then use available web/search/browser tools for contact discovery.

## Required inputs

- `projectId`
- User domain or target URL
- Linkable asset, page, product, study, tool, or topic
- Optional competitors
- Optional market/location/language

## OpenSEO MCP tools

- `get_serp_results`: find ranking articles, listicles, resource pages, comparisons, and topical publishers.
- `get_backlinks_overview`: inspect competitor domain or page backlink/referring-domain patterns.
- `get_domain_overview`: qualify important prospect domains.
- `get_ranked_keywords`: understand what a prospect or competitor ranks for when topical fit matters.
- `search_local_businesses` and `get_local_serp_results`: use for local SEO link prospecting when nearby businesses, local competitors, or Maps/category signals can reveal partnership targets.
- `research_keywords`: expand prospecting queries.

## Contact discovery tools

After OpenSEO identifies good prospects, use available non-OpenSEO browsing or search tools for public contact discovery. Depending on the client, this may be web search, page fetches, browser automation, or a search API.

Look for:

- Author byline pages
- Contact pages
- Editorial guidelines
- About/team pages
- LinkedIn, X, Bluesky, or other professional profiles
- Newsletter or publication masthead pages
- Public email addresses in page HTML or visible page text
- Structured data such as `Person`, `Organization`, `sameAs`, or `email`

Only record contact details that were actually found. Include the source URL for any email, profile, or contact form.

## Prospecting query patterns

Build queries from the asset/topic:

- `<topic> resources`
- `best <category> tools`
- `<competitor> alternatives`
- `<topic> statistics`
- `<topic> guide`
- `<topic> examples`
- `<topic> templates`
- `<topic> software`
- `<topic> for <audience>`

Use `get_serp_results` in batches for the most relevant patterns. Send at most 10 queries per call.

## Workflow

1. Clarify the linkable asset and the reason someone would reference it.
2. Build 5-10 prospecting queries by default.
3. Call `get_serp_results` for those queries.
4. If competitors are provided, call `get_backlinks_overview` for the strongest competitor domains or pages first. Continue without backlink evidence if it is unavailable.
5. For local SEO, use `search_local_businesses` and `get_local_serp_results` around priority locations to identify nearby competitors, categories, and local SERP evidence before searching for local chambers, associations, campus resources, community pages, and directories.
6. Filter prospects:
   - Keep topical relevance and editorial pages.
   - Prioritize articles, directories, resource pages, comparisons, statistics pages, templates, and curated lists.
   - Deprioritize homepages, login pages, thin affiliate pages, spam, unrelated forums, and direct competitors unless a comparison angle is valid.
7. For each good prospect, define the outreach angle:
   - Broken/missing resource
   - Better current data
   - Useful tool/template
   - Alternative or comparison inclusion
   - Expert quote or supporting reference
8. For the strongest prospects, visit or search the prospect site to find the best contact path.
9. Draft outreach messages. If contact details were found, include the source. If not, list the next best contact-discovery path.

## Output format

Start with:

- Best outreach angle
- Highest-priority prospect type
- Any data limitations

Then include:

| Prospect URL | Site/domain | Source | Relevance | Suggested angle | Contact path | Priority |
| ------------ | ----------- | ------ | --------- | --------------- | ------------ | -------- |

Then provide 2-3 reusable outreach drafts:

- Resource/list inclusion
- Article update/reference suggestion
- Competitor alternative/comparison angle

## Guardrails

- Do not invent email addresses, social handles, or contact names.
- Do not say OpenSEO found contact details unless an OpenSEO tool returned them. Attribute contact discovery to the web/search/browser source used.
- If contact details are not available after a reasonable search, recommend specific discovery steps such as checking the author page, contact page, LinkedIn, X, or a reputable contact-enrichment tool.
- Avoid spammy mass outreach. Personalize by page and reason.
- Flag prospects that are direct competitors or likely paid placements.

## ⚠️ Gotchas (避坑指南)
- **避免關鍵字堆砌與門頁懲罰 (Doorway Pages)**：多據點或多機型頁面必須結合在地真實數據（如實收租金、分店地標、真實檢測數據），禁止僅替換地名或機型名稱。
- **Schema 與畫面一致性**：產出的 JSON-LD (`FAQPage`, `LocalBusiness`, `Product`) 內容必須與頁面可見文字 100% 一致，否則會觸發 Google 結構化資料人工處罰。
