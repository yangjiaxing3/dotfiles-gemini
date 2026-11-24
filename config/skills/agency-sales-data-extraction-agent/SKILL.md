---
name: agency-sales-data-extraction-agent
description: "Use when extracting MTD/YTD sales KPIs and forecasts from Excel sheets into pipelines. Not for payroll audits. Excel銷售指標提取與預測彙整"
---

# 銷售與營運指標 Excel 提取專家

專責從定期產出之分店銷售、月累計（MTD）、年累計（YTD）與業績預測 Excel 報表中，以確定性、冪等且可追溯的方式擷取數值並寫入管線。

## 關鍵規則

1. **只處理可見分頁，防範隱藏舊表覆蓋**
   - 遍歷工作簿時檢查 `sheet_state == "visible"`，跳過隱藏／極隱藏分頁內的歷史草稿。
2. **模糊列名對齊 ＋ 明確對照留痕**
   - 支援中英文常見表頭變體（如 `實收租金` / `revenue`、`目標` / `quota`、`分店編號` / `s_ino`），但必須記錄實際對應到哪一欄，嚴禁靜默錯配。
3. **明細夾雜「合計／小計／Total」必用 `continue` 跳過**
   - 遇小計／合計／註解／全空列時記錄統計後 **`continue` 跳過**，切勿直接當數據寫入（造成指標翻倍）或提早 `break`（漏抓後半部據點）。
4. **檔案內容雜湊冪等（Idempotency）**
   - 以 SHA-256 檔案雜湊＋目標期間作為匯入指紋，防止同一檔案重複匯入產生重複指標；不覆寫人工已鎖定紀錄。
5. **日期與貨幣正規化**
   - 優先讀取 Excel 原生日期物件與序列值，台灣民國年統一轉換為西元；移除 `$`, `NT$`, `,` 等符號前須先檢查負數括號 `(1,234)` -> `-1234`。
6. **安全忽略鎖定暫存檔**
   - 批次掃描目錄時自動略過 `~$` 開頭的 Excel 鎖定暫存檔。

## 標準提取流水線

```python
import hashlib
import re

SUBTOTAL_RE = re.compile(r"^(合計|小計|總計|total|subtotal)$", re.I)

def file_sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()

def parse_currency_cell(val) -> float | None:
    if val is None or val == "":
        return None
    if isinstance(val, (int, float)):
        return float(val)
    s = str(val).strip().replace(",", "").replace("NT$", "").replace("$", "")
    if s.startswith("(") and s.endswith(")"):
        s = "-" + s[1:-1]
    return float(s) if s else None
```

## When to Skip（不適用場景）
- 若任務重點是**個人薪資明細核對、勞健保代扣勾稽或傳票借貸審計**，請優先啟動 `xlsx` ＋ `spreadsheet-reconciliation`。

## ⚠️ Gotchas (避坑指南)
- **不可將空白儲存格與實值 `0` 混為一談**：指標明確為 `0` 時應記錄為 `0`（例如當月零違約／零退款），僅缺失值轉 `None`。
- **終端機輸出保護**：解析大表時僅回報匯入摘要（處理分頁數、成功筆數、跳過合計列數、失敗列號），禁印整份表格原文。
- **先探測再入庫**：版面結構不清時先跑 `.agents/skills/xlsx/scripts/xlsx_ingest_profiler.py` 取得表頭與合併範圍。
