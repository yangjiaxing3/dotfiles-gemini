---
name: seo-bing
description: "'Use when tasks involve seo bing: Bing Webmaster Tools + IndexNow extension. Microsoft Copilot citations are fed by the Bing in..."
version: "2.2.4"
compatibility: "Requires BING_WEBMASTER_API_KEY and (optionally) INDEXNOW_KEY in ~/.claude/settings.json env. Run extensions/bing-webmaster/install.sh to configure."
---

# seo-bing

The non-Google indexing surface. Google still rejects IndexNow (per
Gary Illyes, multiple SOTR episodes 2024-2025), so this skill is
specifically for **Amazon/Bing/Naver/Seznam.cz/Yandex/Yep indexing** and
**Microsoft Copilot AI citation** (which pulls from the Bing index).

## Prerequisites

- Run `extensions/bing-webmaster/install.sh` or `install.ps1`.
- A Bing Webmaster Tools API key.
- Optional: an IndexNow host key (32+ chars) published at the URL
  declared as `INDEXNOW_KEY_LOCATION`.

## Routing

| Command | Underlying script |
|---|---|
| `/seo bing links <url>` | `"$HOME/.claude/skills/seo/bin/claude-seo" run bing_webmaster.py links <url>` |
| `/seo bing compare <urlA> <urlB>` | `"$HOME/.claude/skills/seo/bin/claude-seo" run bing_webmaster.py compare <urlA> <urlB>`; both properties must be registered to the API account |
| `/seo bing submit <url>` (single URL) | `"$HOME/.claude/skills/seo/bin/claude-seo" run indexnow_submit.py --host ... --urls <url>` |
| `/seo bing submit-batch <file>` | `"$HOME/.claude/skills/seo/bin/claude-seo" run indexnow_submit.py --host ... --urls-file <file>` |
| `/seo bing verify-indexnow` | `"$HOME/.claude/skills/seo/bin/claude-seo" run indexnow_submit.py --host ... --verify-only` |

## When this skill applies

- The user is publishing new pages and wants Microsoft Copilot
  citation eligibility (Bing index ingestion).
- The user wants to nudge Amazon/Bing/Naver/Seznam.cz/Yandex/Yep indexing for fresh
  URLs.
- The user manages both properties and wants to compare their Bing link data.
  For an arbitrary competitor, route to DataForSEO, Moz, or Common Crawl.

## Cross-skill delegation

- For Google indexing (very different model, sitemap-driven, no
  IndexNow), use `seo-google indexing`.
- For multi-source backlink confidence weighting, fall back to
  `seo-backlinks` which already integrates Bing + Moz + CC.

## ⚠️ Gotchas (避坑指南)
- **避免關鍵字堆砌與門頁懲罰 (Doorway Pages)**：多據點或多機型頁面必須結合在地真實數據（如實收租金、分店地標、真實檢測數據），禁止僅替換地名或機型名稱。
- **Schema 與畫面一致性**：產出的 JSON-LD (`FAQPage`, `LocalBusiness`, `Product`) 內容必須與頁面可見文字 100% 一致，否則會觸發 Google 結構化資料人工處罰。
