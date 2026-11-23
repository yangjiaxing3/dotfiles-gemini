# [Correct-Pattern] 互動式網頁操作手冊三技能標準（`/eli5` × `/diagram-design` × `/e2e`）

## 📌 Context
於 `StoreasyFMnew`（PICKÉ 內湖新明館營運中樞 `frontend/public/manuals/picke/picke-ops-manual.html`）實證定案之新人／跨部門互動式網頁手冊製作範式，規則細節已拆至按需載入的 `~/.gemini/rules/docs-and-manuals.md`（Cursor 對應 `docs-and-manuals.mdc`），不塞爆個別專案的 `DESIGN.md` 與 `AGENTS.md`。

## ❌ [Anti-Pattern 錯誤模式]
1. **寫給第一線新人看的手冊卻滿篇工程術語**：出現 API、JWT、RBAC、SQLite 等字眼，或沒有生活類比。
2. **手工截圖隨便圈框或連正式 DB 示範**：污染正式環境，或紅框偏移、缺邊界檢查。
3. **只寫靜態 Markdown 或把幾十頁規範硬塞進專案 `DESIGN.md`／`AGENTS.md`**：造成每輪 Prompt 上下文膨脹，且一般業務同仁無法直接點擊搜尋與放大看圖。

## ✅ [Correct-Pattern 正確作法]
1. **`/eli5` 翻譯層**：四段式白話（這頁做什麼 → 生活類比 → 對齊 ①②③ 紅框步驟 → 常見狀況）。
2. **`/diagram-design` 導覽圖**：必備總覽＋核心流程雙圖（`nodes <= 9, edges <= 12`、`12px Noto Sans TC`、三檢查 `@2x` PNG）。
3. **`/e2e` 隔離實機截圖與紅框標註**：起隔離臨時 SQLite + Seed 示範資料 → Playwright `boundingBox()` 畫 ①②③ 紅框 → `consoleErrors=0` → 關服刪臨時庫。
4. **互動單檔交付**：固定左側可搜尋目錄 + 雙軌結構（5 分鐘角色速成 + 逐頁圖解）+ 點擊燈箱放大 + FAQ 折疊，承襲專案自身 CIS 實色系。
5. **拆層同步不膨脹**：前端排版與中文直覺寫在 `rules/react-typescript.md`，文件與手冊標準寫在 `rules/docs-and-manuals.md`，僅於 `GEMINI.md` / `engineering-core.mdc` 留一行指標。
