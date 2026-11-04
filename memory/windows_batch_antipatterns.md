# [PatternExtract] Windows Batch Scripts 安全啟動與解析陷阱 (Post-Mortem)

## 📌 Context
在建立或優化 Node.js / Python 專案的 `start.bat` 時，常會遇到 CMD 啟動視窗一閃而退、指令無法順利執行、或是因為系統權限不同導致路徑遺失的狀況。

---

## ❌ [Anti-Pattern 錯誤模式]

### 1. 遺失工作目錄 (Working Directory Lost)
直接使用相對路徑啟動腳本。如果使用者是以「系統管理員身分執行」或透過捷徑執行，預設目錄會變成 `C:\Windows\System32`，導致 `cd backend` 找不到資料夾。
```batch
cd backend && npm run dev
```

### 2. `||` 與 `&&` 的短路陷阱 (Short-Circuit Logic)
試圖在一行內處理虛擬環境的偵測與服務啟動。
```batch
call venv\Scripts\activate.bat 2>nul || echo Virtual env not found && uvicorn app.main:app --reload
```
**致命後果**：`A || B && C` 在 CMD 中會被解析為 `(A || B) && C`。如果 `activate.bat` 成功執行，因為 `||` 的關係，後面的 `&& uvicorn ...` 會直接被「跳過」不執行！伺服器永遠不會啟動。

### 3. `::` 註解引發語法崩潰 (Label Parsing Trap)
使用 `::` 作為註解，但內容包含了 `||`, `&&`, `<`, `>` 等特殊符號。
```batch
:: 使用 if exist 明確判斷，避免 && || 的短路陷阱
```
**致命後果**：`::` 其實是一個無效的「標籤 (Label)」，並不是真正的註解指令。CMD 解析器在遇到特殊符號時，會試圖將標籤與指令連接，導致拋出 `|| was unexpected at this time.` 的語法崩潰。

### 4. `start` 指令吞噬引號 (Start Command Quoting)
```batch
start cmd /k "cd frontend && npm run dev"
```
**致命後果**：`start` 指令會將「第一個用雙引號包起來的字串」視為**視窗標題 (Window Title)**。如果寫得不嚴謹，指令可能會被誤判。

---

## ✅ [Correct-Pattern 正確作法]

### 1. 強制鎖定工作目錄
腳本第一行必須加上強制切換到 `start.bat` 所在目錄的指令。
```batch
@echo off
cd /d "%~dp0"
```

### 2. 使用標準 `REM` 註解
**永遠不要使用 `::` 來寫包含任何程式邏輯或特殊符號的註解**，一律使用標準的 `REM`。
```batch
REM 使用 if exist 明確判斷，避免 && || 的短路陷阱
```

### 3. 使用 `if exist` 取代 `||` 短路，並用括號確保執行順序
```batch
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
) else (
    echo Virtual env not found, using global python
)
uvicorn app.main:app --reload
```
如果是放在 `start cmd /k` 的單行指令內：
```batch
start "Backend API" cmd /k "cd backend && (if exist venv\Scripts\activate.bat (call venv\Scripts\activate.bat) else (echo Not found)) && uvicorn app.main:app --reload"
```

### 4. 為 `start` 賦予明確的視窗標題
永遠為 `start` 的第一個參數給予明確的 `"標題"`，防止後續的指令引號被誤吞。
```batch
start "Admin Frontend" cmd /k "cd frontend && npm run dev"
```
