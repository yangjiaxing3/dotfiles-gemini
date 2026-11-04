---
name: storeasy-channel-operations
description: "Use when implementing or reviewing StoreasyFMnew Channel Manager promotions, pricing sync, public-site propagation, or rollback. 通路促銷發布/價格同步"
---

# Storeasy 通路發布作業

`StoreasyFMnew`（後台）與 `storeasynewwebsite`（官網）是**同一套發布系統**。以目前程式碼與真實 API 回應為準；按鈕文字與 commit 訊息都不是契約。

## 先蒐證，再動手

1. 讀兩個 repo 的 `AGENTS.md`，保留各自的工作樹狀態。
2. 對要改的功能，逐一找出：UI 路由 → 請求 payload → 後端路由 → service → model → 官網讀取端 → 快取 → 驗證用的公開網址。
3. 依需要讀參考檔（都要對照 HEAD 重新確認）：
   - [references/channel-workflow.md](references/channel-workflow.md)：頁面職責、狀態機、閘門。
   - [references/known-risks.md](references/known-risks.md)：已知 P0/P1 風險與程式碼位置，**改 Channel Manager 或定價前必讀**。
   - [references/phase2-insights-rag.md](references/phase2-insights-rag.md)：Marketing Insights、MCP 證據與助理權限。

**後台寫入成功 ≠ 官網已更新。** 傳播、靜態資料輸出、快取失效、公開網址要分開驗證。

## 頁面職責（一個實體只能有一個發布者）

| 頁面 | 負責 |
| :--- | :--- |
| Campaign Manager | 活動內容、SEO、CTA、日期、目標分店 |
| Promotion Manager | 折扣金額與適用資格 |
| Product Editor | 單位文案、圖片、SEO 完整度 |
| **Channel Manager** | **唯一的發布協調者** |
| Pricing Dashboard | 發布後的實際價格、漂移、預覽、回滾 |
| Marketing Insights | 已驗證的活動/通路/據點指標 |
| AI 助理 | 預設唯讀；寫入需預覽、權限、稽核紀錄 |

多個頁面各自宣稱能發布同一實體的設計一律退回。

## 發布協定

狀態機：`draft → validating → ready_for_review → approved → publishing → verifying → live`
例外狀態：`validation_failed`、`publish_failed`、`verify_failed`、`rolling_back`、`rolled_back`、`paused`、`expired`、`drifted`。核准後任何修改都產生新的不可變版本並回到 `draft`。

核准前要驗證：RBAC、活動日期與狀態、折扣經濟性、實際可租庫存、所選單位歸屬、商品內容、明確的通路旗標、據點對應、價格來源、圖片、slug、預期網址。**遇到空通路、狀態不明、缺公開 ID、schema 不符一律擋下（fail closed）。**

執行時用**單一冪等發布指令**，保存：release ID、操作者、輸入雜湊、所選單位、活動與促銷版本、通路旗標、前後快照、核准紀錄、時間戳、outbox 步驟、外部回執。本地寫入用一個交易；外部/靜態檔/快取的副作用逐步打 checkpoint。

## 端到端驗證

1. 單元測試：狀態轉換與驗證規則。
2. 契約測試：前端 payload 對 Pydantic schema。
3. 整合測試：只上 Shop、只上據點、兩者皆上、下架、移除促銷、超賣拒絕、重試、回滾。
4. 觀察一次真實成功的後端回應。
5. 檢查官網 Shop 與據點頁：價格、促銷、CTA、canonical、快取新鮮度。
6. 分析數據要用穩定的 campaign/promotion ID，不能用標題推出來的替代 ID。

儀表板顯示 0 不代表沒有資料。宣稱「根據 MCP 洞察」時，必須附上查詢、頁面維度、基準、觀察期間、變因與成功門檻，否則不採信。

## ⚠️ Gotchas (避坑指南)

- **通路旗標被覆寫**：第二個 session/端點會把「只上據點」改回 Shop=true；任何次要端點都不得覆寫已提交的通路旗標。
- **空通路預設成 Shop**：導致真正的下架失敗；空通路必須視為「不發布」並擋下確認。
- **官網讀寫不同目錄**：促銷索引讀 `public/data`，同步卻寫 `src/data`，且可能匯出草稿；改同步腳本時兩端一起驗證。
- **清除促銷的型別不符**：前端送 `null`/空字串，後端要求字串；改清除流程時補契約測試。
