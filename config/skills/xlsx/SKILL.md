---
name: xlsx
description: "Use when creating, auditing, or ingesting Excel (.xlsx/.xlsm/.csv) workbooks with formulas and zero-PII profiling. Excel報表建表/xlsm解析/公式重算"
license: Proprietary. LICENSE.txt has complete terms
---

# `/xlsx` v2.5 — 企業試算表建置與髒實務 `.xlsm` 脫敏解析引擎

本技能涵蓋兩大嚴謹模式：**模式 A（讀取髒實務母檔 `.xlsx`/`.xlsm`）** 與 **模式 B（產出金融與財會公式活頁簿）**。跨分頁勾稽與差異歸因請協作呼叫 `spreadsheet-reconciliation`。

## 執行工具定位（跨專案必讀）

專案同步後，確定性腳本位於 `.agents/skills/xlsx/`（全域母源於 `~/.gemini/config/skills/xlsx/`）。已內建自動掛載全域 `.venv` 與 `node_modules`，可從任一專案直接執行：

```powershell
# 1) 模式 A 第一步：零個資結構探測（必跑，嚴禁把原始個資印到終端機）
python .agents/skills/xlsx/scripts/xlsx_ingest_profiler.py <path/to/file.xlsm>

# 2) 公式與快取值靜態稽核（--audit-only 絕不更動原檔）
python .agents/skills/xlsx/recalc.py <path/to/file.xlsx> --audit-only

# 3) 公式依賴圖 (DAG)、OOXML _xlfn. 轉譯、What-If 單元驗算
python .agents/skills/xlsx/scripts/formula_engine_hub.py dag <path/to/file.xlsx>
python .agents/skills/xlsx/scripts/formula_engine_hub.py xlfn "=XLOOKUP(A2, B:B, C:C)"
python .agents/skills/xlsx/scripts/formula_engine_hub.py eval <path/to/file.xlsx> "Sheet1!C10" --set "Sheet1!A2=5000"

# 4) 無頭計算驗證（Node.js HyperFormula v3.5.0）
node .agents/skills/xlsx/scripts/hyperformula_eval.js '{"Sheet1": [[105, "=ROUND(A1/1.05, 0)"]]}'
```

---

## 模式 A：台灣財會 `.xlsm` / `.xlsx` 嚴謹攝取守則

1. **先脫敏探勘，再寫解析程式**：一律先跑 `xlsx_ingest_profiler.py` 取得合併格範圍、隱藏列、表頭候選列、合計列與公式健檢，**嚴禁直接用 Python `print()` 傾印含姓名/薪資之工作表內容**。
2. **合併儲存格展開**：`openpyxl` / `pandas` 僅在合併區左上角儲存值，其餘格為 `None`；必須依 `merged_cells.ranges` 或目標區前填（`ffill`）處理，禁止遇 `None` 靜默斷尾。
3. **區分「實值 `0`」與「空白」**：不可用 `if not val:` 忽略 `0`；出勤、扣款、未達標獎金之實值 `0` 應保留，僅視 `None` 或空白字串為缺值。
4. **明細夾雜「合計／小計／總計」列**：掃到表尾或中段合計列必須用 **`continue` 跳過而非 `break` 中止**，避免漏讀後方門市或人員。
5. **隱藏列雙重計數陷阱**：台灣實務常把離職員工或作廢分頁「隱藏」而不刪除；讀取時須明確檢查 `ws.row_dimensions[r].hidden` 與 `ws.sheet_state == "visible"`，並留意 `SUM()` 與 `SUBTOTAL(109,)` 差異。
6. **民國年日期與 `.xlsm` 保護**：寫回 `.xlsm` 必須 `load_workbook(..., keep_vba=is_xlsm)`；民國日期（如 `115/10/01`）統一加 `1911` 轉西元。

---

## 模式 B：財務報表與模型建置守則

1. **強制使用動態公式**：所有合計、成長率、佔比、獎金拆分一律寫 Excel 公式（如 `=SUM(B2:B9)`），禁止在 Python 算完硬塞常數。
2. **零公式錯誤**：交付前必跑 `recalc.py` 確認 `#REF!`, `#DIV/0!`, `#VALUE!`, `#N/A`, `#NAME?` 數量為 `0`；現代 Excel 365 函數（`XLOOKUP`, `LET`, `FILTER`, `UNIQUE`）須經 `_xlfn.` 轉譯。
3. **金融慣例與模板優先**：若為更新既有範本，**原範本樣式優先**；新建模型採藍字 (`0000FF`) 硬編碼輸入、黑字 (`000000`) 公式、綠字 (`008000`) 跨頁參照、`$#,##0;($#,##0);"-"` 格式（負數括號、零值 `-`、年份純文字）。

## When to Skip（不適用場景）
- 純 PDF 文字/表格抽取請用 `pdf`；純資料庫 SQL 索引優化請用 `agency-engineering-database-optimizer`。

## Progressive Disclosure References (On-Demand)
- 完整多引擎降級鏈、`recalc.py` 輸出格式與合併儲存格展開實戰範例見 [references/detailed-guide.md](./references/detailed-guide.md)。

## ⚠️ Gotchas (避坑指南)
- **終端機個資與輸出防爆**：處理真實人事/財務活頁簿時，預設必開 `--mask-pii`，禁止印出超過 20 筆清單或任何個人薪資／姓名明文。
- **Windows 無 LibreOffice 時用 COM / `formulas`**：本機 Windows 重算由 `recalc.py` 自動依序嘗試 `Excel COM -> formualizer -> formulas`；若對第三方母檔做驗算，務必加 `--audit-only` 保護原始 `<v>` 快取與 VBA 不被改寫。
- **`openpyxl` `data_only=True` 不可存檔**：以 `data_only=True` 開啟後呼叫 `.save()` 會永久洗掉所有公式字串，僅限唯讀讀值。
