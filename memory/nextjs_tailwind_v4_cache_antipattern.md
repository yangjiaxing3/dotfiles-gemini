# [PatternExtract] Next.js 15 + Tailwind CSS v4 快取崩潰與樣式遺失陷阱 (Post-Mortem)

## 📌 Context
在使用 Next.js 15 搭配最新的 Tailwind CSS v4 時，常會發生網站前端突然「完全沒有載入 CSS 樣式」，導致畫面變成純 HTML 排版，甚至在重新啟動伺服器後依然無法恢復。

---

## ❌ [Anti-Pattern 錯誤模式]

### 1. 盲目重啟伺服器 (Blind Restart)
當發現 CSS 樣式沒有被正確編譯與載入時，直覺地在終端機按下 `Ctrl+C` 關閉程序並重新執行 `npm run dev`。
**致命後果**：由於 Next.js 的 `.next` 快取 (Cache) 系統非常頑固，如果在開發過程中 Tailwind v4 掃描或編譯發生了錯亂，這個錯誤的狀態會被**鎖死在 `.next` 快取中**。單純重啟伺服器並無法清除錯誤，導致 Tailwind v4 依然無法將樣式注入 `globals.css`。

### 2. 忽略 Zombie Process (殭屍程序佔用)
當 `start.bat` 或其他指令啟動失敗時，其實在背景中已經有 Node.js 程序悄悄佔用了 Port 3000。如果此時直接再跑一次 `npm run dev`，Next.js 會自動退讓，改用 Port 3001 或其他 Port，導致使用者依然訪問到舊的、無 CSS 的 Port 3000。

---

## ✅ [Correct-Pattern 正確作法]

### 1. 強制擊殺與徹底清除快取 (Kill & Clean Cache)
遇到任何 Tailwind v4 樣式未正確載入、或編譯卡死的狀況，標準的修復流程必須包含「刪除 `.next` 快取」，強迫 Tailwind 與 Turbopack 重新讀取與編譯。

在 Windows 環境下的標準救援指令如下：
```powershell
# 1. 找出佔用 3000 Port 的 PID
netstat -ano | findstr 3000

# 2. 強制關閉該 Node.js 程序
taskkill /F /PID <PID_NUMBER>

# 3. 徹底刪除 Next.js 快取資料夾 (在專案根目錄執行)
Remove-Item -Recurse -Force .next

# 4. 重新啟動開發伺服器
npm run dev
```

### 2. 提醒使用者強制重新整理 (Hard Refresh)
修復伺服器端後，由於瀏覽器端也可能快取了壞掉的 CSS 檔案，必須明確請使用者按下 `Ctrl + F5` (或 `Cmd + Shift + R`) 強制重新整理，確保取得重新編譯後的全新樣式。
