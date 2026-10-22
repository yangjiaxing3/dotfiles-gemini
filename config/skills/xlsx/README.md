# `/xlsx` Skill — Multi-Engine Spreadsheet Formula & Financial Audit Hub

本目錄為全域 `/xlsx` Skill（`C:\Users\Jiaxing\.gemini\config\skills\xlsx`），整合 **GitHub 四大頂尖開源試算表公式引擎** 與 **Windows Excel 16.0 COM 原生重算驗證器**，專為高複雜度財務模型、會計審計工作底稿與 React/TypeScript 前端試算表打造。

---

## 一、已整合之四大公式引擎架構

| 引擎 | 版本 | 執行環境 | 核心職責與解決痛點 |
| :--- | :---: | :---: | :--- |
| **`pywin32` + `xlwings`** | `311` / `0.37.7` | `.venv` (Python 3.14) | 驅動本機 Excel 16.0 COM `CalculateFullRebuild()` 強制寫入 `<v>` 快取值，並支援 `Range.formula2` 原生寫入動態陣列公式。 |
| **[`vinci1it2000/formulas`](https://github.com/vinci1it2000/formulas) + `networkx`** | `1.3.4` | `.venv` (Python 3.14) | 解析跨工作表公式 AST 與有向無環圖（DAG），計算最大拓撲深度、找出高依賴熱點（Hotspots）並攔截循環參照（Circular References）。 |
| **[`bradbase/xlcalculator`](https://github.com/bradbase/xlcalculator)** | `0.5.0` | `.venv` (Python 3.14) | 離線財務模型單元測試（What-If Unit Testing）：無須開啟桌面 Excel 即可動態注入儲存格覆寫值並驗算目標公式。 |
| **[`handsontable/hyperformula`](https://github.com/handsontable/hyperformula) + `@ironcalc/wasm`** | `3.5.0` / `0.5.1` | Node.js `v24+` | 支援 **423 個標準 Excel 函數**之高速無頭（Headless）公式求值器，可與 React + TypeScript 網頁前端共用邏輯。 |

---

## 二、核心 CLI 工具使用指南

### 1. 多引擎自動重算、OOXML `_xlfn.` 修復與靜態防呆掃描 (`recalc.py`)
```powershell
& "C:\Users\Jiaxing\.gemini\config\skills\xlsx\.venv\Scripts\python.exe" "C:\Users\Jiaxing\.gemini\config\skills\xlsx\recalc.py" <path_to_workbook.xlsx>
```
- **自動補齊 `_xlfn.` 前綴**：防止 `openpyxl` 寫入 `XLOOKUP`、`LET`、`LAMBDA`、`FILTER`、`UNIQUE`、`SORT` 等 32 個現代 Excel 函數時出現 `#NAME?`。
- **靜態審計檢查**：自動掃描並警告盲目包覆 `IFERROR(..., "")` 及 `SUMIFS` 對純數字字串使用 `"<>"&Cell` 之型別強制轉換風險。

### 2. 活頁簿 DAG 依賴關係圖與拓撲深度分析 (`scripts/formula_engine_hub.py dag`)
```powershell
& "C:\Users\Jiaxing\.gemini\config\skills\xlsx\.venv\Scripts\python.exe" "C:\Users\Jiaxing\.gemini\config\skills\xlsx\scripts\formula_engine_hub.py" dag <path_to_workbook.xlsx>
```

### 3. 財務模型 What-If 單元測試 (`scripts/formula_engine_hub.py eval`)
```powershell
& "C:\Users\Jiaxing\.gemini\config\skills\xlsx\.venv\Scripts\python.exe" "C:\Users\Jiaxing\.gemini\config\skills\xlsx\scripts\formula_engine_hub.py" eval <path_to_workbook.xlsx> "Sheet1!D10" --set "Sheet1!A2=1050"
```

### 4. 現代 Excel 365 公式轉譯為 OOXML 安全語法 (`scripts/formula_engine_hub.py xlfn`)
```powershell
& "C:\Users\Jiaxing\.gemini\config\skills\xlsx\.venv\Scripts\python.exe" "C:\Users\Jiaxing\.gemini\config\skills\xlsx\scripts\formula_engine_hub.py" xlfn "=LET(x, XLOOKUP(A2, B:B, C:C), FILTER(D:D, D:D>x))"
```

### 5. Node.js `HyperFormula` 高速無頭公式求值 (`scripts/hyperformula_eval.js`)
```powershell
node "C:\Users\Jiaxing\.gemini\config\skills\xlsx\scripts\hyperformula_eval.js" '{"Sheet1": [[105, "=ROUND(A1/1.05, 0)", "=A1-B1", "=B1+C1"]]}'
```
