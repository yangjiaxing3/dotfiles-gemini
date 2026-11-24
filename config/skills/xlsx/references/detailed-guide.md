# `/xlsx` v2.5 — 進階參考與多引擎實作細節

## 一、多引擎公式重算降級鏈 (`recalc.py`)

`recalc.py` 針對 `.xlsx` / `.xlsm` 採取以下自動降級鏈（支援 `--audit-only` 唯讀審計模式）：
1. **Windows Excel COM (`pywin32`)**：呼叫本機 Excel 16.0 `CalculateFullRebuild()`，與桌面 Excel 計算結果 100% 一致。
2. **`PSU3D0/formualizer`（Rust + Apache Arrow，選配）**：無頭跨平台重算引擎，原生支援 `XLOOKUP`、`LET`、`LAMBDA`、`FILTER` 等現代 Excel 365 語法。
3. **`vinci1it2000/formulas`（純 Python AST/DAG）**：無需 Office 或 Rust 依賴的備援公式解析器。
4. **`LibreOffice Headless` (`soffice`)**：Linux / macOS 無頭環境備援。

> **注意**：`recalc.py` 在寫入或重算階段會自動依據 `.xlsm` 副檔名設定 `keep_vba=True`；掃描則一律使用 `read_only=True` 雙軌比對公式與快取值，確保零公式錯誤且偵測 `uncached_formula_count`（未快取公式）。

## 二、`xlsx_ingest_profiler.py` 輸出欄位與審計指標

```json
{
  "file": "payroll_example.xlsm",
  "pii_masked": true,
  "sheets_count": 3,
  "sheets": [
    {
      "name": "薪資明細",
      "sheet_state": "visible",
      "merged_cells_count": 12,
      "hidden_rows_count": 2,
      "subtotal_total_rows": [45, 78],
      "header_candidate_rows": [{"row": 3, "non_empty_cols": 38}]
    }
  ],
  "formula_audit": {
    "total_formulas": 420,
    "uncached_formula_count": 0,
    "error_cells": [],
    "sum_hidden_row_risks": ["薪資明細!F78"],
    "sum_off_by_one_warnings": [],
    "pattern_break_warnings": []
  }
}
```

- **`sum_hidden_row_risks`**：同一分頁存在隱藏列時，若合計格使用 `SUM(...)` 而非 `SUBTOTAL(109, ...)`，在 Python 只加總可見列時會與 Excel 顯示總額出現差額，須在匯入程式顯式校驗。
- **`sum_off_by_one_warnings`**：偵測 `SUM(ColR1:ColR2)` 範圍下方 `R2+1` 緊接非零數值列且非「合計/小計」列，代表可能漏算新加列。
- **`pattern_break_warnings`**：同一公式欄突然出現 1–2 格純數字手打常數覆寫（Plug / Manual override）。

## 三、Node.js 無頭引擎說明

- **`hyperformula_eval.js`**：已內建自動尋找 `~/.gemini/config/skills/xlsx/node_modules`，支援 `node .agents/skills/xlsx/scripts/hyperformula_eval.js --file payload.json` 直接從專案根目錄呼叫，避免 Windows 命令列長 JSON 引號問題。
- **`@ironcalc/wasm`**：屬於 ESM / WebAssembly 模組（`wasm_bg.wasm` + `wasm.js`），適合瀏覽器與 ESM 前端沙盒內掛載計算，CommonJS Node 腳本預設使用 `HyperFormula v3.5.0`。

## 四、合併儲存格與雙軌清洗建議範例

```python
from openpyxl import load_workbook

def build_merged_lookup(ws) -> dict[tuple[int, int], object]:
    """將合併儲存格左上角值展開映射至整個合併區塊。"""
    lookup = {}
    for rng in ws.merged_cells.ranges:
        anchor = ws.cell(rng.min_row, rng.min_col).value
        for r in range(rng.min_row, rng.max_row + 1):
            for c in range(rng.min_col, rng.max_col + 1):
                lookup[(r, c)] = anchor
    return lookup
```

## 五、`openpyxl` 讀寫實務備忘
- 列／欄皆為 **1-based** 索引（`row=1, column=1` 為 `A1`）。
- 寫入大型檔案時使用 `write_only=True`；唯讀大檔讀取時使用 `read_only=True`。
- 現代函數如 `XLOOKUP`、`FILTER` 寫入前必先經過 `formula_engine_hub.py xlfn` 轉譯成 `_xlfn.` / `_xlfn._xlws.`。
