# Windows `.git/index.lock` 自動安全解鎖守則

## `[Anti-Pattern 錯誤模式]`
- 遇到 `fatal: Unable to create '.../.git/index.lock': File exists.` 時，只用 `Get-Process git` 判斷是否有 git 進程在跑。
- 在 Windows 上啟用 `core.fsmonitor` 時，背景會長期常駐 `git fsmonitor--daemon run --detach`，導致 `Get-Process git` 永遠回傳非空而誤判為「有寫入型 git 進程正在執行」，因而白白跳過清理並回報卡住。

## `[Correct-Pattern 正確作法]`
當 `git add` / `git commit` / `git reset` 因 `.git/index.lock` 失敗時，**主動透過 PowerShell CLI 執行以下安全自動解鎖流程**（不無故停等使用者手動處理）：

1. **檢查真實寫入型進程（排除 `fsmonitor--daemon`）**：
   ```powershell
   $writers = Get-CimInstance Win32_Process -Filter "Name='git.exe'" |
     Where-Object { $_.CommandLine -and $_.CommandLine -notmatch 'fsmonitor--daemon' -and $_.CommandLine -match '\b(add|commit|reset|checkout|switch|merge|rebase|cherry-pick|stash)\b' }
   ```
2. **確認 `$writers` 為空（無真實寫入進程）且 `.git/index.lock` 存在後，直接安全刪除**：
   ```powershell
   Remove-Item -LiteralPath ".git/index.lock" -Force -ErrorAction Stop
   ```
3. **若刪除仍報檔案占用**：先執行 `git fsmonitor--daemon stop` 釋放監控控制代碼，再執行 `Remove-Item -LiteralPath ".git/index.lock" -Force -ErrorAction Stop`。
4. **例外中止條件**：若 `$writers` 非空（確實有其他 `add`/`commit`/`rebase` 進程正在運作），或移除兩次皆因系統權限／外部防毒鎖定失敗，才立即停止並向使用者回報占用來源。
