---
name: migration-refactoring
description: "'把舊專案移植到現代框架。Use when porting HTML/GAS/PHP to React, or the user says 移植重構 / migration.'"
---

# 移植重構工作流 (Migration Refactoring Pipeline)

當使用者提及「移植重構」、「migration」、「port HTML to React」、「舊專案遷移」、或需要將既有 Git 倉庫中的 HTML/GAS/PHP 頁面移植到現代前端框架時，啟動此工作流。

**核心理念**：不是「重新寫」，是「深度繼承 + 系統性升級」。既有系統的業務邏輯與 UX 決策是多年迭代的產物，必須被尊重並完整理解後，才能進行技術棧的現代化。

---

## 前置條件 (Prerequisites)

| 項目 | 說明 | 範例 |
| --- | --- | --- |
| `SOURCE_REPO` | 原始專案 Git URL 或本地路徑 | `ref_workdiv/src/` 或 `https://github.com/org/legacy.git` |
| `TARGET_REPO` | 目標專案工作區路徑 | `c:\Users\...\NewProject` |
| `TECH_STACK` | 目標技術棧 | 依當前專案而定 (例: React 19 + Tailwind CSS) |
| `ICON_LIB` | 統一圖示庫 | `lucide-react` (禁止 MUI/FontAwesome) |
| `CSS_POLICY` | CSS 策略 | 遵循專案既有規範 (如已使用 Tailwind 則維持使用) |
| `DEV_PORT` | 開發伺服器鎖定 Port | `5175` |
| `LIVE_URL` | 原始線上版本 URL (若有) | `https://www.example.com/app` |

---

## Phase 0: 🛡️ 零區安全協議 (Boundary Sentinel)

1. 確認目標工作區路徑在安全邊界內。
2. 確認 `SOURCE_REPO` 已 clone 或可存取。
3. 確認 `TARGET_REPO` 的 Vite 開發伺服器可啟動（`npm run dev`）。

---

## Phase 1: 📦 深度溯源盤點 (Source Inventory & Deep Audit)

### Step 1.1: 原始檔案完整清冊
列出所有 HTML/模板檔案，產出 **Source File Inventory** 表（檔案名、行數、功能摘要、業務重要性、技術複雜度）。

### Step 1.2: 逐頁功能拆解
針對每個 HTML 頁面，產出：
1. **UI 結構樹** — 列出所有區塊/section
2. **互動元素清單** — 所有 button, modal, tab, form 的觸發行為
3. **資料流** — 頁面如何取得/送出資料 (fetch, google.script.run, WebSocket)
4. **第三方依賴** — 使用了哪些 CDN (Tailwind, MUI, Chart.js, Leaflet)
5. **業務邏輯亮點** — 核心商業計算、狀態機、條件判斷
6. **已知問題** — 硬編碼、無障礙缺失、效能瓶頸

### Step 1.3: 與目標專案的差異矩陣 & 反面模式掃描
- 檢查禁用圖示庫殘留 (`@mui|fontawesome|material-symbols`)
- 檢查原生 `alert/confirm/prompt`
- 檢查硬編碼 API URL 與 `box-sizing: border-box`
- 產出 `source_audit.md` Artifact。

---

## Phase 2: 🔬 領域研究與內容深化 (Contextual Research)

1. **原始線上版本深度研究**：若有 `LIVE_URL`，用瀏覽器驗證工具分段操作並截圖記錄導航結構、表單驗證、空狀態與 RWD 斷點。
2. **競品與市場分析**：研究同類頁面 UX 最佳實踐與 SEO 語意化標準。
3. **內容差距分析**：比對原始頁面與目標頁面的內容豐富度，產出 `context_research.md`。

---

## Phase 3: ⚖️ 多 Agent 辯證模式 (Multi-Agent Review Pipeline)

1. **Agent A (Ideation)**：基於 Phase 1 + Phase 2 提出 2~3 種移植架構方案（元件拆分、路由、CSS、狀態管理）。
2. **Agent B (Red Teaming)**：審查原始功能完整性、UX 回歸風險、技術債務與響應式覆蓋。
3. **Agent C (Synthesis)**：綜合正反意見產出 `implementation_plan.md` 並暫停等待使用者審核。

---

## Phase 4 & Phase 5: 🛠️ SDD 交付與全量 E2E 驗證

1. **Phase 4 執行順序**：CSS 基礎設施 → 共用元件 → 頁面元件（由低耦合至高耦合）→ 路由整合 → 反面模式掃描與修復。
2. **Phase 5 全量 E2E 驗證**：路由 HTTP 200 檢查、圖示合規掃描、無 `alert()` 掃描、真實瀏覽器視覺截圖與原始功能對照表。
3. 完整 Phase 4/5 檢查表與快速啟動範例請參閱 `references/detailed-guide.md`。

## ⚠️ Gotchas (避坑指南)
- **禁止只看標題就重寫**：必須逐行分析原始 JS 邏輯與空狀態/錯誤狀態設計，嚴禁遺漏既有業務規則。
- **終端機輸出保護 (Context Overflow Prevention)**：執行腳本或查詢時，禁止直接將上百筆 JSON/日誌印到 stdout；請導向暫存檔或加上筆數限制。
- **零區防禦與 Port 禁令**：修改或執行指令前嚴守工作區邊界，嚴禁綁定或終止保留埠 (`8000`、`5100`、`3000`)。
