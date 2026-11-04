---
name: social-listening-brief
description: "'社群聲量／competitor social listening brief。Use when the user asks about BUNNIT、iMT、手機回收討論、Threads/PTT/媒體風向、加碼期 vs 常態痛點，或要把社群聲量納入 S..."
---

# social-listening-brief

把「有人在討論什麼」收成 **可被 SEO／行銷儀表板引用的 brief**，不是即時爬蟲、不是聲量排名。

HQ 畫面：核心業務 → 行銷工具 → **社群聲量**（fixture／人工 brief）。  
本機樣本：`docs/marketing/social-listening/bunnit-phone-recycle-2026-09-20.md`  
Threads one-shot（2026-09-20 21:25 台北）：`docs/marketing/social-listening/threads-sample-2026-09-20.md`  
契約：`src/lib/social-listening-fixture.ts` 與 `scripts/seo-loop/fixtures/social-listening.sample.json`

`us3c-seo-loop` 把本技能當 **可選 Stage 1b**。沒有 brief 就標「無社群 brief」，**不要**用 GSC／Ads 數字假裝社群聲量。

## 與 Agent-Reach 的關係（可選收集器，不是 HQ 真相源）

[Panniantong/Agent-Reach](https://github.com/Panniantong/Agent-Reach) 是 **Agent 讀網／搜社群的能力層**（Jina 讀網頁、X／Reddit／小紅書等）。us3c-next **不 vendor、不安裝、不在 HQ 打 live scrape**。

| 這次 brief 來源 | Agent-Reach 現況 | v1 怎麼做 |
|---|---|---|
| Threads（脆，主戰場） | 不在支援表 | 人工補貼文重點，或登入瀏覽器 **one-shot（唯讀）** 的 permalink；share URL 不當 API。不是 live crawl／連續監測 |
| PTT iOS | 不在支援表 | 沿用 brief 已寫的列 |
| 今周刊／NOWnews／官網 | 可用「讀任意網頁」補 permalink | 有 URL 才寫 `source_url`；搜尋筆數 ≠ 聲量 |
| X／Twitter | 有通道（常要 Cookie） | brief 寫主戰場不是 X；本 PR 不抓 |

之後若要用 Agent-Reach **刷新** brief：先 `agent-reach doctor` 看通道，再讀公開頁，產出仍必須過本檔 schema。**搜尋命中數不可寫成 `quote_count`／`volume`。** 沒裝 CLI 就維持 fixture。

## 何時使用

- 使用者提到 BUNNIT、iMT、脆／Threads、PTT、今周刊／NOWnews 與「手機回收」風向
- 要判斷加碼期帶風向 vs 加碼後真實問題（滿機、排隊、重測刷價）
- SEO／GEO 文案需要競品討論依據，但不能發明引用次數
- 行銷儀表板要掛 Competitor Social / SERP Intent 列

不要用本技能去：即時抓 Threads／X、寫攻擊競品文案、把 US3C 與 BUNNIT 混成同一品牌。

## 輸入

| 欄位 | 必填 | 說明 |
|---|---|---|
| `topic` | 是 | 討論主題，例如「手機回收」「舊 iPhone 回收」「自助回收機」 |
| `platforms` | 是 | 實際讀過的平台。沒讀過就不要列。常見：`threads`、`ptt`、`nownews`、`businesstoday`、`official_web` |
| `promo_window` | 建議 | 加碼／檔期起訖。未知就留空，不要猜日期 |

可選：`competitor`（預設 BUNNIT/iMT）、`captured_at`、既有 brief 路徑。

## 輸出 schema（一列一證據）

每列都要有這些欄位。**不要**加 `quote_count`、`mentions`、`volume`、`share_of_voice`。brief 沒寫的數字不要補。

| 欄位 | 型別 | 說明 |
|---|---|---|
| `topic` | string | 這列在講的主題 |
| `platform` | string | 證據所在平台／媒體 |
| `sentiment` | `positive` \| `negative` \| `mixed` | 這則證據的語氣，不是全站分數 |
| `promo_flag` | boolean | 是否落在加碼／檔期敘事 |
| `pain_tags` | string[] | 只從證據出現的痛點勾選，例如 `滿機`、`長排隊`、`操作摩擦`、`估價不穩` |
| `source_url` | string | 可核對的網址或 brief 寫到的來源域。沒有文章 permalink 就用出版來源，不要發明 slug |
| `captured_at` | string | ISO 日期（含時區更佳） |
| `usable_for_seo` | boolean | 能否拿去寫對照 FAQ／關鍵字；負評只准拿來產品差異，不准當攻擊文案 |

Brief 本體另附：`entity`、`promo_window`、`clusters[]`（主題叢集，不是引用次數）、`narrative`。

## Entity 規則（強制）

**BUNNIT / iMT ≠ US3C / iMCheck / Securaze。**

- BUNNIT、iMT（Idea MT）是競品／對手機台敘事
- US3C、iMCheck、Securaze 是我方品牌與檢測／抹除棧
- SERP、FAQ、Title 不可把對手實體詞寫成我方；也不可把我方隱私抹除能力掛到 BUNNIT 名下
- 競品負評 → 對照「超商寄件免排隊、吞吐、價格口徑、隱私抹除」；不要複製攻擊句

## 執行步驟

1. 讀輸入的 topic／platforms／promo_window。
2. 先找 `docs/marketing/social-listening/` 是否已有同主題 brief。有就沿用，不要重編造數字。
3. 只摘有來源的列。Threads share link 無法當 API。沒有 permalink 或人工貼文重點就不要列 Threads 原文列。登入瀏覽器 one-shot（唯讀）拿到的 permalink 可以列，但仍不是 live crawl／連續監測。
4. 標時間窗。加碼期媒體敘事 ≠ 常態口碑。
5. 輸出符合上表的 JSON 列 + 短 narrative。沒有證據的欄位留空或省略痛點，不要填假的。
6. 若要進 SEO：只把 `usable_for_seo=true` 的痛點丟給 `us3c-seo-loop` Stage 3/5 當意圖缺口，不當作 GSC 曝光。

## 禁止

- 禁止發明引用次數、按讚、轉發、share of voice
- 即時爬 Threads／X（本 repo v1 沒有這條管線）
- 把 fixture 數字寫成「即時聲量」
- 把 BUNNIT 討論寫進 US3C 官網 Title 當自己的實體詞

## ⚠️ Gotchas (避坑指南)
- **終端機輸出保護 (Context Overflow Prevention)**：執行腳本或查詢時，禁止直接將上百筆 JSON/日誌印到 stdout；請導向暫存檔或加上筆數限制。
- **零區防禦與 Port 禁令**：修改或執行指令前嚴守工作區邊界，嚴禁綁定或終止保留埠 (`8000`、`5100`、`3000`)。
