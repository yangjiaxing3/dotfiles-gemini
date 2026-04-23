---
description: "爬蟲與資料管線規範，含反爬策略、狀態同步、資料完整性"
globs: ["**/crawler/**", "**/price_crawler/**", "**/agents/**", "**/services/normalizer*", "**/services/price_history*", "**/services/state_manager*", "**/erp_cloud_sync*", "**/sync_manager*"]
---

# 爬蟲與資料管線規範

## 反爬策略

- 每次請求之間必須加入延遲（遵從 `config.yaml` 的 `delay` 設定）
- User-Agent 隨機輪替，避免被目標站封鎖
- CDP 模式（Apple 等）必須連接本機 Chrome，不使用 headless
- 遇到反爬偵測（CAPTCHA、403）時，記錄錯誤並跳過，不做暴力重試

## 狀態與斷點續爬

- 使用 SQLite 記錄爬取進度（checkpoint），支援中斷後恢復
- 黑名單機制：無效 ERP 識別碼加入 `blacklist.json`，後續自動跳過
- 狀態檔（DB、JSON、checkpoint）的同步使用 pull → merge → push 流程

## 資料完整性

- 價格為 0 或 null 的記錄必須過濾，不寫入最終資料庫
- 正規化流程（normalizer）必須保持冪等性：同樣輸入永遠產出同樣結果
- 匯出 Excel 前必須做資料校驗（筆數、欄位完整性）

## 日誌與監控

- 每個爬蟲 Agent 獨立 logger，以來源名稱區分
- 關鍵節點必須記錄：開始、完成、錯誤、跳過的筆數
- 禁止在日誌中暴露完整 URL 參數（可能含 session token）
