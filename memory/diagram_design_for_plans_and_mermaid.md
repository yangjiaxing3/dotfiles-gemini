---
id: mem-diagram-design-for-plans-and-mermaid
brand: shared-eng
tier: L2_DECISION
status: active
valid_from: "2026-11-26"
scope_repos: []
---

# [Correct-Pattern] 凡所有 repo 的 `README.md`、Plan 或文件涉及架構圖，強制調用 `/diagram-design` 並兼顧人機雙讀

## 📌 Context
適用於跨品牌所有工程專案與所有 AI 客戶端（Antigravity、Cursor、Gemini CLI、Codex、Claude）。

---

## ❌ [Anti-Pattern 錯誤模式]
1. **將 `README.md` 寫成純給 AI 看的指令清單，或缺少視覺化架構圖**：
   - 開頭放「本文件專為 AI 設計」排他宣告，且只用密密麻麻的表格或純文字／裸 Mermaid 程式碼塊堆砌技術細節，導致一般業務、產品或跨部門同仁看不懂系統做什麼與怎麼運作。
2. **在 `README.md` 或 Plan 中手寫巨型單一 `Mermaid` 區塊交差**：
   - 把超過 9 個節點、超過 12 條長文字邊全部塞進同一個 `flowchart TD` 或 `sequenceDiagram`，依賴 Mermaid 預設自動排版，導致線條交錯、文字擠壓重疊、缺乏信任邊界與視覺重點。
3. **圖表內容使用全英文標籤或 7–8px 迷你英文字體**：
   - 未將分區標題、節點說明、連線語義與底部圖例轉為**繁體中文**（`12px` `'Geist', 'Noto Sans TC', 'PingFang TC', 'Microsoft JhengHei'`）。
4. **覆寫相同檔名的 `.svg` 導致面板快取不更新**：
   - 在 Artifact 面板內嵌圖片時覆寫舊檔名，且未透過 Playwright 渲染 `@2x` 高解析度 PNG，導致瀏覽器顯示舊版快取圖片或外掛字型無法載入。

---

## ✅ [Correct-Pattern 正確作法]
1. **人機雙讀 `README.md` 結構（適用於所有 repo）**：
   - 上半部給一般人 30 秒看懂：白話定位一句話、系統模組圖解、跨專案關係圖解、主要操作入口與角色權限說明。
   - 下半部給工程師與 AI Agent：技術棧、目錄結構、環境啟動、部署指令、跨專案契約與紅線（純 AI 交辦細則與工作流則放 `AGENTS.md` 與 `DECISIONS.md`）。
   - 圖表產物集中於 `docs/diagrams/<name>-vN-zhtw.{html,svg,png}`，並在 `README.md` 以 Markdown 相對路徑內嵌 `.png`（同時可附 `.html` / `.svg` 連結）。
2. **強制自動載入 `diagram-design` Skill 與複雜度門禁 (`mermaid_extract.py`)**：
   - 凡撰寫或更新任何 **`README.md`、`Plan` 或架構設計文件**且涉及系統架構、資料流、時序或狀態圖時，強制載入 `diagram-design` Skill（`C:\Users\Jiaxing\.gemini\config\skills\diagram-design\SKILL.md`）。
   - 若來源含 Mermaid 區塊，先執行：
     `python C:\Users\Jiaxing\.gemini\config\skills\diagram-design\scripts\mermaid_extract.py <file.md> --diagram all`
   - 嚴格確保單圖 **`nodes <= 9`**、**`edges <= 12`**（超出時必須依 Zone 收斂或拆分為 Overview + Detail 雙圖）。
3. **同步產出 `/diagram-design` Editorial HTML + SVG + `@2x` PNG**：
   - 選擇對應語義模式（如跨專案邊界與寫入風險用 **Secure Paved Road → Architecture**；跨系統同步用 **Sequence**）。
   - 遵守 6 大強制連線鐵律：正交圓角 `r=8`（禁斜線）、標籤白底遮罩距離線條 `6–10px`、零重疊連線、同邊端點分散 `>=12px`、最多 2 個珊瑚橘 (`#eb6c36`) 焦點、底部獨立水平圖例列。
   - **內容強制繁體中文化**：除 Repo 檔名、資料表／欄位識別符 (`store_id`, `quote_id` 等)、API 路徑與 Port 外，所有分區標題、節點名稱、連線標籤與圖例一律使用**繁體中文 (`12px` `Noto Sans TC`)**。
4. **執行三重自動化驗證與破快取 PNG 渲染**：
   - 執行 `python C:\Users\Jiaxing\.gemini\config\skills\diagram-design\scripts\self_check.py <diagram.html>` 確保 `OK`。
   - 執行 `python C:\Users\Jiaxing\.gemini\config\skills\diagram-design\scripts\verify-geometry.py <diagram.html>` 確保無標籤遮罩被後畫節點裁切。
   - 使用 Playwright (`deviceScaleFactor: 2`，等待 `document.fonts.ready`) 將 HTML 內 `<svg>` 渲染為**帶版本／語系後綴的新檔名 PNG**（如 `*-v1-zhtw.png`），存於 repo `docs/diagrams/`（供 `README.md` 相對路徑引用）或複製至 Artifact 目錄供 Plan 內嵌。
