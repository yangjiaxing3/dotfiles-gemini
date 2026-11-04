---
name: session-handoff
description: "Use when wrapping up, pausing, or resuming a coding session to persist context in SESSION-HANDOFF.md. 開發交接/保存進度/结束session/handoff"
---

# Session Handoff

`SESSION-HANDOFF.md` 給下一個 AI 用；`README.md` 給人看。兩者不要混寫。

## 判斷模式

- **收尾**：使用者說 handoff、wrap up、今天先到這、結束 session。
- **接續**：使用者說 resume、continue、讀交接、接著做。
- 不明確時：對話剛開始 → 接續；正在收工 → 收尾。

## 收尾模式

1. 只收集高價值資訊：
   - 新增/修改的檔案（路徑）
   - 跑過的關鍵指令與**實際結果**（通過/失敗、數字）
   - 決策與**理由**
   - 踩過的坑，特別是會讓下一個人重蹈覆轍的
   - 未完成項目與下一步
2. 在專案根目錄建立或更新 `SESSION-HANDOFF.md`，控制在 300 行內，只保留最近兩輪的細節，更舊的濃縮成一行。
3. 下一步要能直接執行：寫出指令、檔案、驗收條件。
4. 只有對外行為改變且根目錄已有 `README.md` 時才更新 README。
5. 回報使用者：`SESSION-HANDOFF.md` 是否更新、`README.md` 是否更新。

```markdown
# SESSION-HANDOFF.md
> 最後更新：YYYY-MM-DD HH:mm (UTC+8)

## 目前目標
## 已完成（含驗證結果）
## 下一步（可執行指令 + 驗收條件）
## 踩過的坑
## 關鍵檔案索引
## 環境備註（版本、路徑、必要服務）
```

## 接續模式

1. 先讀 `SESSION-HANDOFF.md`（不存在就直說，改由 repo 與使用者需求重建脈絡）。
2. 讀專案規則檔：`AGENTS.md`、`.agents/AGENTS.md`、`GEMINI.md`、`CLAUDE.md`，有哪個讀哪個。
3. 讀根目錄 `README.md`（若有）。
4. 跑非破壞性檢查：`git status --short`、`git log --oneline -5`。
5. 回報：恢復的目標、目前 git 狀態、交接檔與實際狀態的差異、前三個下一步。

## 品質門檻

- 寫具體的路徑與行為，不寫流水帳。
- 不貼大段程式碼，用檔案路徑引用。
- 失敗與陷阱一定要留，那是交接最有價值的部分。

## ⚠️ Gotchas (避坑指南)

- **交接檔會過期**：接續時以 `git status` / `git log` 的實際狀態為準；若與交接檔不一致，先指出差異再動手。
- **不要寫入秘密**：token、密碼、連線字串只寫「存放位置」，不寫值。
- **多個 repo 聯動時**：每個被修改的 repo 都要列出 branch 與未提交狀態，避免下一位只看到其中一個。
