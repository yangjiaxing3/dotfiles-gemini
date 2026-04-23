---
description: "高風險操作攔截規則 — 刪除、洩密、外部通訊的強制確認機制"
globs: ["**/*"]
---

# 🚨 高風險操作攔截規則 (Safety-Critical)

此規則為最高優先級，覆蓋所有其他規則。

## 一、禁止自動執行的操作

以下操作**絕對不得**設定 `SafeToAutoRun: true`，必須強制等待使用者核准：

### 🗑️ 破壞性檔案操作
- `rm -rf`、`rmdir /s`、`del /f`、`Remove-Item -Recurse`
- 刪除 `.git`、`.env`、`node_modules`、`__pycache__`、`.venv` 等關鍵目錄
- `git reset --hard`、`git clean -fd`、`git push --force`
- `DROP TABLE`、`DELETE FROM`（無 WHERE 的資料庫操作）
- 任何涉及生產環境資料庫的操作

### 🔑 敏感資訊洩漏
- 禁止將 API Key、Token、密碼、Secret 寫入任何非 `.env` / `.gitignore` 保護的檔案
- 禁止在 `run_command` 中以明文傳遞密碼或 Token
- 禁止將包含敏感資訊的內容輸出至日誌或終端
- 禁止透過 `curl`、`Invoke-WebRequest` 等工具將本地資料發送至未知外部 URL

### 📧 外部通訊操作
- 禁止自動執行任何寄信指令（`sendmail`、`Send-MailMessage`、SMTP 操作）
- 禁止自動執行 `npm publish`、`pip upload`、`docker push` 等發布操作
- 禁止自動執行 webhook 呼叫或第三方 API 推送

## 二、必須觸發二次確認的情境

當偵測到以下情境時，**必須暫停並明確告知使用者風險**：

1. **批量檔案修改**：一次修改超過 10 個檔案時
2. **跨專案操作**：操作目標超出當前工作區根目錄時
3. **環境變數修改**：任何涉及 `.env` 檔案的寫入操作
4. **資料庫結構變更**：ALTER TABLE、CREATE INDEX 等 schema 變更
5. **套件安裝**：`pip install`、`npm install` 新增未出現在 requirements.txt / package.json 的套件

## 三、偵測到違規時的標準回應

當偵測到上述任何高風險操作時，必須輸出以下格式的警告：

```
⚠️ 高風險操作偵測 ⚠️
操作類型：[刪除/洩密/外部通訊/批量修改]
具體指令：[將要執行的指令]
影響範圍：[受影響的檔案/資料]
風險等級：[🔴 極高 / 🟠 高 / 🟡 中]
請確認是否繼續？
```
