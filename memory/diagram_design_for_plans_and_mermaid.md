# [Correct-Pattern] 凡 Plan 或文件涉及 Mermaid／架構圖，強制調用 `/diagram-design` Skill 繪製與驗證

## 📌 Context
適用於所有專案（Storeasy 家族、US3C NEXT 家族及所有未來專案）與所有 AI 客戶端（Antigravity、Cursor、Gemini CLI、Codex、Claude）。

---

## ❌ [Anti-Pattern 錯誤模式]
1. **在 Plan（如 `implementation_plan.md`、`*_diagram_plan.md`）中手寫巨型單一 `Mermaid` 區塊交差**：
   - 把超過 9 個節點、超過 12 條長文字邊全部塞進同一個 `flowchart TD` 或 `sequenceDiagram`，依賴 Mermaid 預設自動排版，導致線條交錯、文字擠壓重疊、缺乏信任邊界與視覺重點。
2. **圖表內容使用全英文標籤或 7–8px 迷你英文字體**：
   - 未將分區標題、節點說明、連線語義與底部圖例轉為**繁體中文**（`12px` `'Geist', 'Noto Sans TC', 'PingFang TC', 'Microsoft JhengHei'`）。
3. **覆寫相同檔名的 `.svg` 導致面板快取不更新**：
   - 在 Artifact 面板內嵌圖片時覆寫舊檔名，且未透過 Playwright 渲染 `@2x` 高解析度 PNG，導致瀏覽器顯示舊版快取圖片或外掛字型無法載入。

---

## ✅ [Correct-Pattern 正確作法]
凡撰寫或更新任何 **Plan / 架構規劃文件** 且涉及 `Mermaid`、架構圖、資料流圖、時序圖、狀態機或 ER 圖時，所有 Agents **強制自動載入並遵循 `diagram-design` Skill（`C:\Users\Jiaxing\.gemini\config\skills\diagram-design\SKILL.md`）**：

1. **強制執行複雜度門禁 (`mermaid_extract.py`)**：
   - 對 Plan 內的 Mermaid 區塊執行：
     `python C:\Users\Jiaxing\.gemini\config\skills\diagram-design\scripts\mermaid_extract.py <plan.md> --diagram all`
   - 嚴格確保單圖 **`nodes <= 9`**、**`edges <= 12`**（超出時必須依 Zone 收斂或拆分為 Overview + Detail 雙圖）。
2. **同步產出 `/diagram-design` Editorial HTML + SVG + `@2x` PNG 並內嵌至 Plan**：
   - 選擇對應語義模式（如跨專案邊界與寫入風險用 **Secure Paved Road → Architecture**；跨系統同步用 **Sequence**）。
   - 遵守 6 大強制連線鐵律：正交圓角 `r=8`（禁斜線）、標籤白底遮罩距離線條 `6–10px`、零重疊連線、同邊端點分散 `>=12px`、最多 2 個珊瑚橘 (`#eb6c36`) 焦點、底部獨立水平圖例列。
   - **內容強制繁體中文化**：除 Repo 檔名、資料表／欄位識別符 (`s_ino`, `quote_id` 等)、API 路徑與 Port 外，所有分區標題、節點名稱、連線標籤與圖例一律使用**繁體中文 (`12px` `Noto Sans TC`)**。
3. **執行雙重自動化驗證與破快取 PNG 渲染**：
   - 執行 `python C:\Users\Jiaxing\.gemini\config\skills\diagram-design\scripts\self_check.py <diagram.html>` 確保 `OK`。
   - 使用 Playwright (`deviceScaleFactor: 2`，解析度 `2560×1440`) 將 HTML 內 `<svg>` 渲染為**帶版本／語系後綴的新檔名 PNG**（如 `*-zhtw.png`），複製於 Artifact 目錄並以 `![標題](/absolute/path/*-zhtw.png)` 內嵌至 Plan，確保零快取殘留且字型 100% 清晰。
