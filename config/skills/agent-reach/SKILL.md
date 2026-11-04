---
name: agent-reach
description: "'Use when researching 手機回收、BUNNIT、PTT/Threads 社群討論 or refreshing socialIntelFixture.json in US3C SEO dashboard. 手機回收社群輿情與Jev篩選'"
---

# Agent Reach → SEO 儀表板

> **SSOT：** 關鍵字歸屬以 [US3C 家族三站 SEO 矩陣分工與防競食戰略法典](https://github.com/yangjiaxing3/us3cwebsite-env/blob/main/.agent/memory/us3c_seo_matrix_rules.md) 為準。`imcheck.com.tw` 擁有泛詞「手機回收」（`手機回收`、`二手手機回收`、`手機回收機`、`24H手機回收機`、`手機線上估價`、`手機回收估價`）與機台據點頁。`us3c.com.tw` 擁有機型／品牌長尾（如 `iPhone 16 回收`）與門市據點詞。`711us3cwebsite` 只擁有超商詞（如 `7-11手機回收`）。與本檔衝突時以法典為準。

上游技能：[Panniantong/Agent-Reach](https://github.com/Panniantong/Agent-Reach)。本專案 **不把** 該 Python CLI 裝進 Vite 前端，也不把社群帳號寫進 HQ。

## 路由（本環境）

先跑 `src/lib/jev/reachHarness.ts` 的 Choice，再執行通道：

1. `CALL_WEB_SEARCH`：WebSearch + 官網（`bunnit.ideamt.com`）。
2. `CALL_OFFICIAL` / `CALL_PTT`：官網活動頁、pttweb。
3. `CALL_THREADS`：share 登入牆不當正文；公開 `/@帳號/post/` 可讀 og:description。
4. `CALL_TWITTER`：`.env.local` 的 `X_BEARER_TOKEN` → v2 recent search；無 token 或 API 失敗 → **0 則，不發明**。
5. 禁止發文、留言、點讚。

## 社群痛點 → 三站 GEO/AEO（一輪）

照 `docs/social-geo-aeo-plan.md` 的 critical path：

1. `npm run jev:harvest` — collect-public + 寫回 `socialIntelFixture.json`（items/clusters/meta）。
2. 保留 `problem_groups` / `geo_aeo` / `faq_drafts` 的題目 id；稅務 `humanOnly`。`site` 若仍寫 `kiosk-geo`，讀成 iMCheck 機台據點。泛詞「手機回收」與「手機回收機」的 owner 是 iMCheck，機型長尾與門市是 us3c，超商詞是 7-11 寄件專站。
3. `npm run jev:action-space` — 補 `jevHarvestLog.json` 的 `actionSpace.posted: false` 證據。
4. `npx vitest run tests/seo-social-intel.test.ts` — verify。

## 寫回 HQ

更新 `src/features/seo-dashboard/data/socialIntelFixture.json`（契約 `1.0.0`）：

- `operator_read`：內部觀察，跟已核對來源分開
- `clusters`：帶風向 / 真實問題 / 還被稱讚
- `items`：每筆要有 `platform`、`url`、`published`、`quote`
- `seo_actions`：每條建議標擁有者。`手機回收`／`手機回收機` 歸 iMCheck；機型頁長尾歸 `us3c.com.tw`；超商詞歸 `711us3cwebsite`

畫面在 `/seo-dashboard`「社群討論」，不併進 Ads 監督。

## Jev × Agent Reach（雙層）

Jev（TypeSafe System One）**不聊天、不生成回覆**，只回 Choice / Score / Noul。
Agent Reach 只當手腳與通道。程式 if/else 才抓網或點索引。**禁止發文／留言／點讚**。

```
1 路由   state → Jev Choice(channel) → if/else → Reach 抓公開頁
2 篩選   每則 → Jev Noul(keep) + Choice(stance) + Noul(tax) → 依 keep 排序
3 行動空間  Reach 把 DOM 編成 [1][2][3] → Jev 選 op + 索引
          CLICK／SELECT 不叫醒 LLM；只有 TYPE_TEXT 才准 MINI
          複雜度／越獄 → MINI / FRONTIER / HUMAN
```

- 金鑰只放 `.env.local` 的 `TYPESAFE_API_KEY`（後端／腳本）。**禁止** `VITE_`，**禁止 commit**。
- 即時判斷：`npm run jev:eval`、`npm run jev:harvest`、`npm run jev:action-space` → `POST https://api.typesafe.ai/v1/systemone`，model `jev-latest`。
- 沒金鑰或在瀏覽器：`src/lib/jev/reachHarness.ts` 的 schema-fallback，引擎標記不得寫成 `jev`。
- 官方技能：`.agent/skills/typesafe-ai/SKILL.md`。不要在 Vite 前端裝 LangChain / `@typesafe-ai/sdk`。
- X／YouTube／小紅書未授權就 `NO_ACTION`。Threads 登入牆不當已讀正文。
- 不要做「搶沙發回覆」：本環境沒有發文權，Jev 選 TYPE_TEXT 也只准搜尋框，不准發布。

## ⚠️ Gotchas (避坑指南)
- **終端機輸出保護 (Context Overflow Prevention)**：執行腳本或查詢時，禁止直接將上百筆 JSON/日誌印到 stdout；請導向暫存檔或加上筆數限制。
- **零區防禦與 Port 禁令**：修改或執行指令前嚴守工作區邊界，嚴禁綁定或終止保留埠 (8000、5100、3000)。
