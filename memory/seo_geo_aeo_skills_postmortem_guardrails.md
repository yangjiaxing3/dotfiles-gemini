# SEO / GEO / AEO Skills 執行覆盤與避坑鐵律 (2026-11-11 Post-Mortem)

> 適用於 `us3cwebsite-env`、`imcheck`、`storeasynewwebsite` 及所有執行 `seo-*`、`geo-content-optimizer`、`on-page-seo-auditor`、`technical-seo-checker`、`schema-markup-generator`、`stageshow` × `impeccable` 技能之專案。

<PatternExtract>
## 1. 首屏意圖對齊 vs GEO 摘要擺放 (Above-the-Fold Payoff vs. GEO Summary)
- **Anti-Pattern**: 執行 `geo-content-optimizer` 或 `ai-seo` 時，為了迎合 AI 爬蟲擷取，把 300 字 `data-answer-summary`、`.summary-grid` 狀態表與長篇說明橫幅全部塞在**價格表／核心互動工具的正上方**，把高交易意圖使用者最想看的「價格表與型號篩選器」擠出首屏，導致跳出率（Pogo-sticking）上升、核心交易字（如「iPhone 回收」）排名下滑。
- **Correct-Pattern**: **首屏優先交付使用者核心 Payoff（如價格表、估價器、門市查詢）**；將結構化狀態表（`.summary-grid`）與權威事實摘要（`data-answer-summary`）緊接配置於**價格表正下方**。只要維持純 SSR 同步輸出且與 JSON-LD `WebPage.description` / `ItemList` 對齊，Googlebot 與 AI 搜尋引擎擷取權重絲毫不減，同時兼顧 SXO 首屏轉化。

## 2. 多站點 SEO 主軸分工與防關鍵字蠶食 (Multi-Site Pillar Guard)
- **Anti-Pattern**: 在同一集團不同網站或同站多頁面無差別堆砌泛詞（例如在 US3C 的 `/promotion-recycle-phones` 混入「手機回收」搶食 `imcheck.com.tw` 主詞，或讓 `/blog/[slug]` 與 `/category/news/[category]/[slug]`、`/kiosk-...` 與 `/kiosk/kiosk-...` 雙路徑並存無 Canonical 收斂），觸發 GSC **「這是重複網頁；使用者未選取標準網頁」**。
- **Correct-Pattern**:
  1. **嚴守三大網站 SEO 主軸邊界**：
     - `imcheck.com.tw`：主攻**「手機回收、24H 智慧手機回收機、AI 手機檢測估價」**。
     - `us3c.com.tw`：主攻**「iPhone 回收、iPhone 回收價格表、MacBook/iPad 回收、直營門市收購、Apple Trade In 折抵比較」**（US3C 核心 iPhone 頁之 `WebPage.description` 與 `FAQPage` 嚴禁混入「手機回收」主詞，改以錨點外連導流 `imcheck.com.tw`）。
     - `Securaze / 企業資安頁`：主攻 **NIST SP 800-88 / ADISA 軍規資料物理抹除與企業資產清退**，提供 E-E-A-T 背書。
  2. **單一標準路由 (Canonical SSOT)**：所有資源僅允許唯一標準 URL 進入 `sitemap.xml` 與站內連結；歷史路徑、MDX 雙生路由、廣告專用頁（`noindex`）一律配置明確 `alternates.canonical` 或 `301` 永久轉址；RSS 自動生成文章必須以標題/Slug 去重後才准寫入 Sitemap。

## 3. 手機版 UX 折疊動畫與 Googlebot Mobile-First 可見性地雷
- **Anti-Pattern**: 結合 UI 技能做手機版手風琴收合（如 `.ss-collapse`）時，在收合態加上 `opacity: 0`、`visibility: hidden` 或條件式卸載 SSR DOM，導致 Google Mobile-First Indexing 判定為隱藏文字（Hidden Text）而降權或忽略索引。
- **Correct-Pattern**: 響應式折疊僅使用 CSS `grid-template-rows: 0fr -> 1fr` 搭配內層 `overflow: hidden`（或原生 `<details>`），**嚴禁對含 SEO/GEO 正文與 FAQ 的容器設 `opacity: 0`**，確保 SSR 100% 輸出且爬蟲可視。

## 4. `FAQPage` JSON-LD 與可見 HTML 雙軌脫鉤 (Schema Drift)
- **Anti-Pattern**: 執行 `on-page-seo-auditor` 改寫頁面上的 FAQ 標題與答案時，漏改同一檔案內手寫的 `<script type="application/ld+json">` `FAQPage` 節點，造成結構化資料與畫面文字不一致，違反 Google Rich Results 規範。
- **Correct-Pattern**: **嚴禁手寫兩份 FAQ**；強制抽取單一 FAQ 資料陣列（SSOT），同時驅動畫面 `<FaqAccordion />` 與 JSON-LD `FAQPage` 生成，並以測試驗證雙邊文字 100% 對齊。

## 5. 時間戳、效期與門市狀態標籤過度重複 (Say It Once / Anti-Stuffing)
- **Anti-Pattern**: 為追求新鮮度訊號（Freshness）或新店曝光，在同一頁的 H2 旁、提示橫幅、`.summary-grid` 與 `data-answer-summary` 重複印出 4～5 次 `最後更新：YYYY-MM-DD（有效至：YYYY-MM-DD）`，或在同一分店頁重複塞 6 次 `預計開幕 / 新開幕`。這不僅破壞排版（窄螢幕斷行），更稀釋 GEO 摘要的實體密度並讓到期日一過全頁顯得腐壞。
- **Correct-Pattern**: 遵循 `stageshow` **"Say it once"**：
  - **價格頁表頭**：單行簡潔 H2（`全系列 {品類} 回收價格表`）＋ 右側單一狀態膠囊（`共 N 款型號 | 最後更新 YYYY-MM-DD`）。
  - **有效期限**：僅保留在價格表正下方的 `.summary-grid` 與 JSON-LD `priceValidUntil`；`data-answer-summary` 只寫高穩定度的品牌權威事實，**不塞易過期的 `validUntil` 字串**。
  - **門市狀態（如「新開幕」）**：每個畫面／卡片區塊僅標示 1 枚徽章，營業狀態由 `store-status.ts` 依營業時間動態計算，嚴禁硬編碼攔截特定 `store.id`。

## 6. 動態數字元件格式化與雙層 Repo CI/CD 斷鏈防護
- **Anti-Pattern**:
  1. 使用 `<Count value={price} prefix="NT$ " />` 卻漏傳千分位 `format={formatTwd}`，導致 SSR 輸出 `NT$ 38500` 與內文 `$38,500` 格式分裂。
  2. 在雙 `package.json` 專案（如根目錄 + `us3c-next-poc/`）新增套件或改動 Canonical 規則後，未同步更新 `.github/workflows/sync-prices.yml` 的 `npm --prefix us3c-next-poc ci`，導致每日自動同步價格 Action 報 `ERR_MODULE_NOT_FOUND` 失敗，連帶造成全站報價過期。
  3. 在 Next.js `next.config.mjs` `redirects` 對帶字首的單段路由誤用 `:slug*`（如 `/kiosk-:slug*`），觸發 `path-to-regexp` 編譯錯誤。
- **Correct-Pattern**:
  1. 動畫數值元件必傳 `format={formatTwd}`。
  2. Next.js 帶字首路由轉址一律用單段 `:slug`（`/kiosk-:slug`）並立即跑 `next build` 實測。
  3. 凡新增子目錄依賴或調整 Sitemap/Canonical，強制同步檢查 `.github/workflows/*.yml`（確保 `npm --prefix <app> ci`）、雙邊 `public/sitemap.xml` 與測試斷言。

- **Tags**: #seo #geo #aeo #sxo #canonical #json-ld #faq-parity #mobile-first #ci-cd #us3c #imcheck #postmortem
</PatternExtract>
