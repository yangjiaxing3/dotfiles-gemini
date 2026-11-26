---
id: mem-ui-no-emoji-no-eng-jargon-taiwan-zh
brand: shared-eng
tier: L2_DECISION
status: active
valid_from: "2026-11-04"
scope_repos: []
---

# 全域 UI 與文案鐵律（2026-11-04 使用者明訂）

> 適用於全集團所有內部系統與前端專案。

1. **禁止在 UI 使用 Emoji**：
   - 任何畫面標題、按鈕、標籤、狀態提示、Placeholder、Table 表頭一律**禁止出現 Emoji**（如 🤖、✨、📋、📜、🖼️、📷、💡、🧮、💬、✅、🔍、🏆 等）。
   - 若需要視覺圖示，僅可**少量、克制地使用乾淨的單色 SVG（或 `lucide-react` 線條圖示）**。

2. **禁止在 UI 暴露工程欄位名／資料庫識別碼**：
   - 嚴禁在一般使用者看得到的表單標籤、篩選器、表格標題或說明文字中直接顯示工程變數名稱（如內部店別代號、場地代號、`emp_code`、`Gross`、`Net`、`LIFF`、`origin` 等）。
   - 一律改為符合台灣人日常直覺的繁體中文用詞：
     - `store_id` / 店別代號 → **分店**
     - `site_id` / 場地代號 → **場地**
     - `emp_code` → **員工編號**
     - `Gross` / `Net` → **應發總額** / **實發總額**
     - `LIFF` → **LINE 帳號綁定**

3. **文字內容極簡直覺，消除工程腔與多餘導覽**：
   - 遵循 `/impeccable` 與 `/frontend-design` 的 Product Register 原則：文字簡潔直白、符合台灣職場習慣。
   - 移除重複解釋標題的長篇副標題、移除多餘的次級麵包屑導覽列、移除冗長的「台帳提示」方塊。

4. **Top Header Menu 分組收納與下拉選單規範**：
   - 頂部導覽列比照既有中台系統之 `AppLayout.tsx` 分組下拉選單（Dropdown Menu）與原生 `<select>` 視覺樣式，將相關頁面收納至邏輯清晰的頂層群組，保持頂部導覽乾淨俐落。
