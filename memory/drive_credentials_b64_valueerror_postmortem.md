# Drive GOOGLE_CREDENTIALS_B64 ValueError Regression (Post-Mortem)

<PatternExtract>
- **Anti-Pattern**: 在處理 Vercel / PowerShell 寫入的 `GOOGLE_CREDENTIALS_B64` 環境變數時，僅使用 `.translate(" \t\r\n\f\v").removeprefix("\ufeff")` 搭配 `base64.b64decode(..., validate=True)`。當環境變數帶有非首位或尾端 `\ufeff` BOM、外層引號 `"..."`、零寬空白 `\u200b` / 不換行空白 `\u00a0` 或缺漏 `=` padding 時，Python 標準庫 `base64._bytes_from_decode_data` 會在 `.encode('ascii')` 捕捉 `UnicodeEncodeError` 並轉拋 `ValueError('string argument should contain only ASCII characters')`，導致 Google Drive 認證失敗；同時下游 `_fetch_today_json` 未檢查 `(None, None)` 而白白 `time.sleep(90)` 並回報 `stale`，`cash` 因 `list_files` 靜默回傳 `[]` 而誤報 `no_cash_csv`。
- **Correct-Pattern**: 統一與 `sheet_service.py`、`worklist_io.py` 及 PR #95 (`7d5ee274`) 對齊，使用 `_B64_ALPHABET = re.compile(r"[^A-Za-z0-9+/=]")` 清除所有非 Base64 字母表字元（含任意位置之 `\ufeff` BOM 與引號），自動補齊 `=` padding（`rem in (2, 3)`），並將 `private_key` 中可能存在的字面 `\\n` 正規化為 `\n`；同時在 `_fetch_today_json` 遇到 `data is None and meta is None` 時立即短路返回，不執行 90 秒等待。
- **Tags**: #python #google-drive #base64 #vercel #cron #daily-imports #fixer
</PatternExtract>
