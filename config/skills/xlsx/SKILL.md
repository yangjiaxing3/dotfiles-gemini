---
name: xlsx
description: "Use when creating, analyzing, or formatting Excel (.xlsx/.csv) spreadsheets with formulas and financial number styles. Excel試算表報表匯出/公式與千分位格式"
license: Proprietary. LICENSE.txt has complete terms
---

# Requirements for Outputs

## All Excel files

### Zero Formula Errors
- Every Excel model MUST be delivered with ZERO formula errors (`#REF!`, `#DIV/0!`, `#VALUE!`, `#N/A`, `#NAME?`)

### Preserve Existing Templates (when updating templates)
- Study and EXACTLY match existing format, style, and conventions when modifying files
- Never impose standardized formatting on files with established patterns
- Existing template conventions ALWAYS override these guidelines

## Financial models

### Color Coding Standards
Unless otherwise stated by the user or existing template

#### Industry-Standard Color Conventions
- **Blue text (RGB: 0,0,255)**: Hardcoded inputs, and numbers users will change for scenarios
- **Black text (RGB: 0,0,0)**: ALL formulas and calculations
- **Green text (RGB: 0,128,0)**: Links pulling from other worksheets within same workbook
- **Red text (RGB: 255,0,0)**: External links to other files
- **Yellow background (RGB: 255,255,0)**: Key assumptions needing attention or cells that need to be updated

### Number Formatting Standards

#### Required Format Rules
- **Years**: Format as text strings (e.g., `"2024"` not `"2,024"`)
- **Currency**: Use `$#,##0` format; ALWAYS specify units in headers (`"Revenue ($mm)"`)
- **Zeros**: Use number formatting to make all zeros `"-"`, including percentages (e.g., `"$#,##0;($#,##0);-"`)
- **Percentages**: Default to `0.0%` format (one decimal)
- **Multiples**: Format as `0.0x` for valuation multiples (EV/EBITDA, P/E)
- **Negative numbers**: Use parentheses `(123)` not minus `-123`

### Formula Construction Rules

#### Assumptions Placement & Helper Columns
- Place ALL assumptions (growth rates, margins, tax rates, multiples, etc.) in separate assumption cells
- Decompose complex nested logic (>3 levels) into auditable **Helper Columns** (e.g., Net Principal $\rightarrow$ Tax Plug $\rightarrow$ Total Credit $\rightarrow$ Balance Check)
- Use explicit guard clauses (`=IF(L2="否", 0, ...)`) instead of blind `IFERROR(..., "")` that masks `#REF!` or `#NAME?` in financial reconciliations

#### Formula Error Prevention
- Verify all cell references are correct and check for off-by-one errors in ranges
- Test with edge cases (zero values, negative numbers, numeric strings in `SUMIFS`)
- Verify no unintended circular references via the DAG analyzer

# XLSX Creation, Multi-Engine Verification, and Analysis

## Installed GitHub Formula Engines (in `/xlsx` Skill Environment)

`openpyxl` writes formula strings (`<f>`) without evaluating cached values (`<v>` is `None`). This skill provides a dedicated virtualenv (`C:\Users\Jiaxing\.gemini\config\skills\xlsx\.venv`) and Node.js runtime integrating 4 top open-source engines:

1. **Windows Excel COM (`pywin32` / `xlwings 0.37.7`) — Primary Recalc & Dynamic Array Engine**:
   - Used automatically by [`recalc.py`](./recalc.py) on Windows (`CalculateFullRebuild()`) to compute cached values and scan all cells for zero errors.
   - Auto-fixes unprefixed modern Excel 365 functions (`XLOOKUP`, `LET`, `LAMBDA`, `FILTER`, `UNIQUE`, `SORT`) with OOXML `_xlfn.` prefixes so `openpyxl` files never trigger `#NAME?`.
2. **`vinci1it2000/formulas` (`v1.3.4`) + `networkx` — AST Compiler & DAG Topology Analyzer**:
   - Inspects cross-sheet dependency graphs, topological depth, hotspot ranges, and circular references:
     `& "C:\Users\Jiaxing\.gemini\config\skills\xlsx\.venv\Scripts\python.exe" "C:\Users\Jiaxing\.gemini\config\skills\xlsx\scripts\formula_engine_hub.py" dag file.xlsx`
3. **`bradbase/xlcalculator` (`v0.5.0`) — Financial Model Unit-Test & What-If Evaluator**:
   - Evaluates target cells with injected parameter overrides without opening desktop Excel:
     `& "C:\Users\Jiaxing\.gemini\config\skills\xlsx\.venv\Scripts\python.exe" "C:\Users\Jiaxing\.gemini\config\skills\xlsx\scripts\formula_engine_hub.py" eval file.xlsx "Sheet1!B10" --set "Sheet1!A2=500"`
4. **`handsontable/hyperformula` (`v3.5.0`, 423 functions) & `@ironcalc/wasm` — Headless JS/Wasm Engine**:
   - Evaluates 400+ Excel functions and array formulas in headless Node.js or React/TS web apps:
     `node "C:\Users\Jiaxing\.gemini\config\skills\xlsx\scripts\hyperformula_eval.js"`

## Reading and analyzing data

### Data analysis with pandas
```python
import pandas as pd

df = pd.read_excel('file.xlsx')
all_sheets = pd.read_excel('file.xlsx', sheet_name=None)
```

## CRITICAL: Use Formulas, Not Hardcoded Values

**Always use Excel formulas instead of calculating values in Python and hardcoding them.**

```python
# Good: Let Excel calculate the sum dynamically
sheet['B10'] = '=SUM(B2:B9)'
sheet['C5'] = '=(C4-C2)/C2'
```

## Progressive Disclosure References (On-Demand)
- Detailed templates, multi-engine CLI commands, OOXML `_xlfn.` rules, and deep-dive checklists live in [references/detailed-guide.md](./references/detailed-guide.md). Load via `view_file` when needed.

## ⚠️ Gotchas (避坑指南)
- **OOXML 現代函數 `#NAME?` 陷阱**：透過 `openpyxl` 直接寫入 `=XLOOKUP(...)`、`=LET(...)`、`=FILTER(...)` 會報 `#NAME?`。必須加上 `_xlfn.` 前綴（或執行 `recalc.py` 自動修復），或用 `xlwings` `Range.formula2` 寫入。
- **`SUMIFS` 純數字文字代碼 `<>` 強制轉型陷阱**：當科目或代碼為純數字文字（如 `"1112003"`）時，`SUMIFS(..., "<>"&K7)` 會將條件轉為數值導致 `文字 <> 數值` 恆真；應改用「總額減去相等項（集合補集法）」。
- **終端機輸出保護 (Context Overflow Prevention)**：執行腳本或查詢時，禁止直接將上百筆 JSON/日誌印到 stdout；請導向暫存檔或加上筆數限制。
- **優先使用確定性腳本**：產出 `.xlsx` 後必須執行 `recalc.py` 與 `scripts/formula_engine_hub.py` 驗證 0 錯誤，不要依賴純語意猜測。
