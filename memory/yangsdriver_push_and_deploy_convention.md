---
id: mem-yangsdriver-push-and-deploy-convention
brand: storeasy
tier: L2_DECISION
status: active
valid_from: "2026-11-26"
scope_repos: [YangsDriver]
---

# YangsDriver 推送與部署規則約定 (`git push and deploy`)

- **[Anti-Pattern 錯誤模式]**：在已有 Firebase 專案設定、CLI 登入授權與目標資料庫環境時，卻回傳含有 `<YOUR_FIREBASE_PROJECT_ID>` 等尖括號佔位符的範例指令讓使用者自己貼上 PowerShell 執行（不僅在 PowerShell 中會觸發 `<` 重導向語法錯誤，也增加多餘手動負擔）。
- **[Correct-Pattern 正確作法]**：
  1. 在 `YangsDriver` 專案根目錄維護受 `.gitignore` 排除之本機 `firebase.json`（綁定具名 Firestore 資料庫與 `firestore.rules`）與 `.firebaserc`（`default = "<FIREBASE_PROJECT_ID>"`，真實專案 ID 僅存於本機未入版控之 `.firebaserc`），確保雙雙不入版控。
  2. 凡收到使用者下達 `git push and deploy`、`推上並部署` 等指令時，直接代為執行：
     - `python ~/.gemini/scripts/rule_lint.py --git-diff`、提交並 `git push origin main`。
     - 僅部署 Firestore 安全規則：`firebase deploy --only firestore:rules --non-interactive`（嚴禁跑全量 `firebase deploy`）。
  3. 若僅指示 `deploy`／`部署規則`，則直接執行 `firebase deploy --only firestore:rules --non-interactive`。
