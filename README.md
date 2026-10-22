# dotfiles-gemini — 全域 AI 工程規則與高階技能中樞 (`~/.gemini`)

本儲存庫為跨客戶端（Antigravity、Gemini CLI、Cursor、Claude、Codex）之**單一真相來源（Single Source of Truth）**全域設定與核心工程技能庫。

---

## 一、儲存庫核心架構

| 路徑 | 用途與說明 |
| :--- | :--- |
| [`GEMINI.md`](./GEMINI.md) | 全域工程規則總綱（繁體中文思維鎖定、KISS 原則、零區防禦 Boundary Sentinel、自動化循環修復協議、Ruflo Swarm V3 多代理路由矩陣、百級技能漸進式載入協議）。 |
| [`rules/`](./rules/) | 技術棧與領域專屬規則（依專案按需載入，如 `testing.md`、`safety-critical.md`、`crawler.md` 等）。 |
| [`hooks/`](./hooks/) | 客戶端前置與後置攔截腳本（PowerShell Hooks）。 |
| [`config/skills/xlsx/`](./config/skills/xlsx/README.md) | **`/xlsx` 財務審計與四大開源試算表公式引擎中樞**（整合 `xlwings/win32com`、`vinci1it2000/formulas`、`bradbase/xlcalculator`、`handsontable/hyperformula` 與 `@ironcalc/wasm`）。 |

---

## 二、`/xlsx` 四大頂尖開源試算表公式引擎（超越 `pycel`）

針對高複雜度 Excel 財務建模、跨表會計勾稽（如收多易 FinHR 零用金兩階段轉檔與跨店代墊資金流向調節）及動態陣列公式設計，[`config/skills/xlsx/`](./config/skills/xlsx/README.md) 整合了四大公式引擎：

1. **Windows 原生 Excel COM 引擎 (`pywin32` + `xlwings 0.37.7`)**
   - 由 [`config/skills/xlsx/recalc.py`](./config/skills/xlsx/recalc.py) 自動調用本機 Excel 16.0 執行 `CalculateFullRebuild()`，強制計算並寫入 `<v>` 快取值，掃描全表確保 `0` 個公式錯誤（`#REF!`, `#NAME?`, `#VALUE!`, `#DIV/0!`, `#N/A`）。
   - 內建 **OOXML `_xlfn.` 自動修復器**：自動為 `openpyxl` 寫入之 32 種現代 Excel 365 函數（`XLOOKUP`, `LET`, `LAMBDA`, `FILTER`, `UNIQUE`, `SORT` 等）補齊 `_xlfn.` / `_xlfn._xlws.` 前綴，徹底消除 `#NAME?` 崩潰。
2. **AST 編譯與 DAG 拓撲依賴圖引擎 ([`vinci1it2000/formulas`](https://github.com/vinci1it2000/formulas) `v1.3.4` + `networkx`)**
   - 由 [`config/skills/xlsx/scripts/formula_engine_hub.py`](./config/skills/xlsx/scripts/formula_engine_hub.py) (`dag` 子指令) 解析跨工作表依賴關係圖（Dependency Graph）、計算最大拓撲深度（Topological Depth）、識別高扇出熱點（Hotspots）並攔截循環參照（Circular References）。
3. **財務模型無頭單元測試引擎 ([`bradbase/xlcalculator`](https://github.com/bradbase/xlcalculator) `v0.5.0`)**
   - 由 `formula_engine_hub.py eval` 執行離線 What-If 參數注入測試（`--set Sheet1!A2=1050`），無須啟動桌面 Excel 即可驗證邊界條件。
4. **高速 Headless JS / Rust-Wasm 公式引擎 ([`handsontable/hyperformula`](https://github.com/handsontable/hyperformula) `v3.5.0` + `@ironcalc/wasm`)**
   - 由 [`config/skills/xlsx/scripts/hyperformula_eval.js`](./config/skills/xlsx/scripts/hyperformula_eval.js) 提供 **423 個原生 Excel 函數**之毫秒級求值，並可與 React + TypeScript 前端試算表無縫共用。

---

## 三、新機環境快速初始化（Setup）

```powershell
# 1. 建立 /xlsx Skill 專屬 Python 虛擬環境並安裝依賴
python -m venv --system-site-packages "$HOME\.gemini\config\skills\xlsx\.venv"
& "$HOME\.gemini\config\skills\xlsx\.venv\Scripts\pip.exe" install -r "$HOME\.gemini\config\skills\xlsx\requirements.txt"

# 2. 安裝 Node.js Headless 公式引擎 (HyperFormula & IronCalc Wasm)
Set-Location "$HOME\.gemini\config\skills\xlsx"
npm install --silent
```

---

## 四、常用驗證指令

```powershell
# 對任意 Excel 活頁簿執行自動 _xlfn 修復、Excel COM 重算與靜態反模式檢查
& "$HOME\.gemini\config\skills\xlsx\.venv\Scripts\python.exe" "$HOME\.gemini\config\skills\xlsx\recalc.py" path\to\workbook.xlsx

# 輸出活頁簿公式之 DAG 拓撲依賴圖與循環參照檢查報告
& "$HOME\.gemini\config\skills\xlsx\.venv\Scripts\python.exe" "$HOME\.gemini\config\skills\xlsx\scripts\formula_engine_hub.py" dag path\to\workbook.xlsx
```
