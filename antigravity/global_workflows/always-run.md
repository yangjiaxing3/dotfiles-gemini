---
description: Always-run whitelist for safe, auto-executable commands. All steps auto-approved.
---

// turbo-all

# Always-Run 白名單機制 (Safe Auto-Execute)

本 Workflow 定義了一組「安全白名單」指令，當 Antigravity 需要執行這些指令時，**無需等待使用者手動批准**，直接自動執行。

## 適用場景

- 專案啟動 / 重啟 Server
- 查詢診斷類指令 (非破壞性)
- 測試與驗證腳本

---

## 1. 伺服器管理

```bash
# 啟動 FastAPI 開發伺服器
python api\app.py
```

```bash
# 清除 Port 8000 並重啟
Stop-Process -Id (Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue).OwningProcess -Force -ErrorAction SilentlyContinue; Start-Sleep -Seconds 2; python api\app.py
```

```bash
# 啟動 run_server.bat
.\run_server.bat
```

## 2. 資料庫診斷（唯讀）

```bash
# 檢查資料庫 Schema
python -c "import sqlite3; c=sqlite3.connect('data/prices_history.db'); print([col[1] for col in c.execute('PRAGMA table_info(price_history)').fetchall()])"
```

```bash
# 檢查表的記錄筆數
python -c "import sqlite3; c=sqlite3.connect('data/prices_history.db'); print('price_history:', c.execute('SELECT COUNT(*) FROM price_history').fetchone()[0])"
```

```bash
# 確認剩餘待爬蟲的空洞群組數
python -c "import sqlite3;c=sqlite3.connect('data/prices_history.db');r=c.execute(\"SELECT COUNT(DISTINCT c.family_id) FROM current_inventory c LEFT JOIN (SELECT family_id FROM price_history WHERE channel='BigGo家族基準') p ON c.family_id=p.family_id WHERE p.family_id IS NULL AND c.family_id IS NOT NULL\").fetchone();print(f'剩餘: {r[0]} 個')"
```

## 3. API 端點測試

```bash
# 執行 API 端點完整性測試
python tmp\test_api.py
```

```bash
# 快速 ping 測試
python -c "import urllib.request; r=urllib.request.urlopen('http://localhost:8000/api/v1/ping'); print(r.read().decode())"
```

## 4. 爬蟲監控

```bash
# 檢查爬蟲進度
python tmp\biggo_progress.py
```

```bash
# 查看 Server 日誌 (最後 50 行)
Get-Content logs\app.log -Tail 50
```

## 5. 檔案系統唯讀查詢

```bash
# 列出 data/ 目錄
Get-ChildItem data\ -Name
```

```bash
# 列出 ref/ 目錄
Get-ChildItem ref\ -Name
```

```bash
# 列出 checkpoints
Get-ChildItem data\checkpoints\ -Name -ErrorAction SilentlyContinue
```

## 6. Git 狀態查詢

```bash
# 檢視 git 狀態
git status --short
```

```bash
# 檢視最近 5 筆 commit
git log -n 5 --oneline
```

```bash
# 檢視目前的 diff
git diff --stat
```

---

## ⚠️ 不在白名單中的指令

以下類型的指令**永遠不會自動執行**，必須等待使用者批准：
- `DROP TABLE` / `DELETE FROM` 等資料庫修改語句
- `pip install` / `npm install` 等套件安裝
- `rm` / `Remove-Item` 等檔案刪除
- 任何涉及外部 API 呼叫的寫入操作
- `git push` / `git commit`