# xlsx — Detailed Reference, Multi-Engine Hub & Extended Examples

## Common Workflow
1. **Choose tool**: `pandas` for bulk tabular analysis, `openpyxl` for workbook construction/formatting, `xlwings`/`win32com` for live Excel COM interaction.
2. **Design DAG & Helper Columns**: Decompose complex multi-condition accounting/statistical formulas into clear intermediate columns.
3. **Save workbook**: Write `.xlsx` to disk.
4. **Recalculate & Lint formulas (MANDATORY IF USING FORMULAS)**:
   ```powershell
   & "C:\Users\Jiaxing\.gemini\config\skills\xlsx\.venv\Scripts\python.exe" "C:\Users\Jiaxing\.gemini\config\skills\xlsx\recalc.py" output.xlsx
   ```
5. **Inspect DAG Topology & Hotspots (for complex multi-sheet models)**:
   ```powershell
   & "C:\Users\Jiaxing\.gemini\config\skills\xlsx\.venv\Scripts\python.exe" "C:\Users\Jiaxing\.gemini\config\skills\xlsx\scripts\formula_engine_hub.py" dag output.xlsx
   ```
6. **Verify and fix any errors**:
   - Check `total_errors == 0` and `uncached_formula_count == 0`.
   - Review `static_analysis` for `unprefixed_modern_functions`, `blind_iferror_Warning_locations`, and `sumifs_inequality_coercion_check`.

---

## Multi-Engine Command Reference (`scripts/formula_engine_hub.py` & `hyperformula_eval.js`)

### 1. Recalculation + Auto `_xlfn.` Fixer (`recalc.py`)
- On Windows, automatically invokes native Excel 16.0 COM (`CalculateFullRebuild()`) to compute and persist `<v>` cached values for every formula cell.
- Automatically prefixes modern Excel 365 functions (`XLOOKUP` $\rightarrow$ `_xlfn.XLOOKUP`, `FILTER` $\rightarrow$ `_xlfn._xlws.FILTER`, `LET` $\rightarrow$ `_xlfn.LET`) before recalculation.
- Falls back to LibreOffice (`soffice --headless`) or `vinci1it2000/formulas` when Excel COM is unavailable.

### 2. Workbook DAG & Circular Reference Analyzer (`formula_engine_hub.py dag`)
```powershell
& "C:\Users\Jiaxing\.gemini\config\skills\xlsx\.venv\Scripts\python.exe" "C:\Users\Jiaxing\.gemini\config\skills\xlsx\scripts\formula_engine_hub.py" dag model.xlsx
```
Returns JSON containing:
- `total_formula_cells`, `dag_nodes`, `dag_edges`
- `is_acyclic_dag` and `circular_references`
- `max_topological_depth` (measures formula nesting/chain complexity)
- `sheet_dependencies` (e.g., `["01_整合轉換明細 -> 03_傳票借貸與跨店調節表"]`)
- `top_dependency_hotspots` (ranges/cells with highest fan-out)

### 3. Headless What-If Unit Testing (`formula_engine_hub.py eval`)
Powered by `bradbase/xlcalculator` (`v0.5.0`), allowing automated unit tests on Excel formulas by injecting cell overrides in memory:
```powershell
& "C:\Users\Jiaxing\.gemini\config\skills\xlsx\.venv\Scripts\python.exe" "C:\Users\Jiaxing\.gemini\config\skills\xlsx\scripts\formula_engine_hub.py" eval model.xlsx "Sheet1!D10" --set "Sheet1!A2=1050"
```

### 4. OOXML `_xlfn.` Formula Translator (`formula_engine_hub.py xlfn`)
```powershell
& "C:\Users\Jiaxing\.gemini\config\skills\xlsx\.venv\Scripts\python.exe" "C:\Users\Jiaxing\.gemini\config\skills\xlsx\scripts\formula_engine_hub.py" xlfn "=LET(x, XLOOKUP(A2, B:B, C:C), FILTER(D:D, D:D>x))"
```

### 5. High-Speed Node.js Headless Formula Engine (`scripts/hyperformula_eval.js`)
Powered by `handsontable/hyperformula` (`v3.5.0`, 423 functions) and `@ironcalc/wasm`:
```powershell
node "C:\Users\Jiaxing\.gemini\config\skills\xlsx\scripts\hyperformula_eval.js" '{"Sheet1": [[105, "=ROUND(A1/1.05, 0)", "=A1-B1", "=B1+C1"]]}'
```

---

## Creating and Editing Excel Files with `openpyxl`

```python
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment

wb = Workbook()
sheet = wb.active

sheet['A1'] = 'Gross Amount'
sheet['B1'] = 'Net Principal'
sheet['C1'] = 'Tax (5% Plug)'

sheet['A2'] = 105
sheet['B2'] = '=ROUND(A2/1.05, 0)'
sheet['C2'] = '=A2-B2'

wb.save('output.xlsx')
```

## Formula Verification Checklist

### Essential Verification
- [ ] **Zero errors after `recalc.py`**: `total_errors == 0` and `uncached_formula_count == 0`
- [ ] **DAG acyclic check**: `is_acyclic_dag == true` via `formula_engine_hub.py dag`
- [ ] **No blind `IFERROR`**: Use explicit guard conditions (`=IF(L2="否", 0, ...)`) so real structural errors are never silently swallowed
- [ ] **Avoid `SUMIFS` numeric-string `<>` coercion**: When comparing text-formatted numeric codes (like `"1112003"`), avoid `"<>"&Cell` in `SUMIFS`; subtract the equality match from the total instead
