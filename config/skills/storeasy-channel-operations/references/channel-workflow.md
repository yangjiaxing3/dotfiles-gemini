# Channel publishing reference
**最後更新：2026-07-13 — 依實際 UI 程式碼驗證修訂**

---

## Page ownership（頁面職責對照）

| 頁面 | 路由 | 應負責 | 不應再負責 |
|---|---|---|---|
| Storage Inventory（空倉查詢） | `/storage/inventory` | 瀏覽實體倉位、勾選倉位、加入發布草稿 | 直接設定優惠、直接推播上架 |
| Promotion Manager（優惠管理） | `/storage/promotions` | 定義折扣規則（類型/額度/效期/疊加條件）；SmartDataTable AI 選倉後順帶建立草稿 | 直接綁定 live 倉位、做最終發布決策 |
| Channel Manager（線上通路管理） | `/storage/channel` | **唯一 Release Composer**：檢視草稿、審批、觸發發布；建立合併倉 (Bundle) | 重複編輯文案或折扣規則 |
| 官網價格匯總 (Pricing Dashboard) | `/storage/pricing-dashboard` | 唯讀：顯示已發布的官網最終售價（原價/年繳優惠/額外優惠/最終價）、外連官網頁面確認 | **⛔ 不發布、不改價格**——僅讀取 `published-pricing` API |
| 全通路 SKU 配額 (Channel SKU Dashboard) | `/storage/channel-sku-dashboard` | 監控各通路 SKU 配額分配、偵測 Drift 狀態偏移 | 第二套發布入口 |
| Campaign Manager（行銷活動） | `/storage/marketing-campaigns` | 活動文案、SEO、CTA、日期、目標據點 | 倉位與通路發布 |
| Marketing Insights（行銷成效） | `/storage/promotion-analytics` | 依 release/campaign/promotion/channel/location 分析成效 | 使用無法追溯的指標 |

> **核心原則**：`PricingDashboard` 是事後**驗證**工具（讀取已發布結果），不是發布入口。
> 過去常被混淆是因為它叫「定價」，但它的資料來源是 `published-pricing` 只讀 API。

---

## 實際 UI 入口（從程式碼驗證）

### Storage Inventory 的關鍵功能

| UI 元素 | 行為 | API |
|---|---|---|
| 分店/狀態過濾器 | 過濾顯示的倉位（可租/已租/已訂/其他） | `GET /api/storage/inventory` |
| Checkbox（每列） | 勾選加入「發布草稿選取集」 | — |
| 底部浮動 Action Bar | 勾選 ≥1 個倉位後出現 | — |
| **「加入發布草稿」按鈕** | 建立 ChannelRelease DRAFT，跳轉 `/storage/channel` | `createChannelReleaseDraftOnly()` |
| 「預覽官網定價方案」按鈕 | 開啟 WebsitePricingPreviewModal（唯讀預覽） | — |

### Promotion Manager 的關鍵功能

| UI 元素 | 行為 | API |
|---|---|---|
| **「新增優惠」按鈕** | 開啟新增/編輯 Modal | — |
| SmartDataTable（Modal 內） | AI 自然語言挑選目標倉位 → 同步建立草稿 | `createChannelReleaseDraftOnly()` |
| 活動名稱列 / Edit 筆按鈕 | 開啟編輯 Modal | — |
| Toggle 開關 | 即時切換優惠 is_active | `PUT /api/promotions/{id}` |
| 「當前套用數量」數字 | 開啟 PromotionCoverageModal（查看覆蓋率） | — |

### Channel Manager 的關鍵功能

| UI 元素 | 行為 | API |
|---|---|---|
| Release 列表 | 顯示所有草稿/發布記錄（Store/Status/Channels/建立時間） | `listChannelReleases()` |
| **「建立合併倉」按鈕** | 開啟 CreateBundleModal，建立虛擬 Bundle 商品 | `POST /api/website-pricing/bundles` |
| 「查看 →」按鈕 | ⚠️ **待修復**：目前是殭屍按鈕（無 onClick，ChannelReleaseDraftModal 已 import 但未掛載） | — |
| 重新整理 | 重新抓取 Release 清單 | — |

### 官網價格匯總 (Pricing Dashboard) 的關鍵功能

| UI 元素 | 行為 |
|---|---|
| 三層 Accordion（城市/分店/倉位） | 展開/折疊階層 |
| Eye 圖示 | `window.open` 開啟 storeasynewwebsite 對應分店頁面（驗證用） |
| Checkbox（每列） + 浮動 Action Bar | 批量操作模式 |
| **「聚合並設定優惠」按鈕**（批量） | 開啟 PromotionAggregatorWizard | `POST /api/promotions/bulk-assign` |
| **「移除優惠」按鈕**（批量） | 批量移除倉位的優惠綁定 | `POST /api/promotions/bulk-assign` (promotion_id=null) |
| 優惠名稱 Badge | navigate → `../promotions`（跳回優惠管理編輯） |

> **⛔ Pricing Dashboard 完全沒有「發布」按鈕**。它顯示的是已發布結果，不是發布入口。

---

## Data ownership（資料所有權）

- `StorageInventory`：實體倉位的物理狀態（可租/已租/已訂）。
- `WebsitePricingUnit`：官網可見性旗標（is_published_shop / is_published_location）；Bundle 虛擬倉位（is_bundle=True + bundled_st_ids）。
- `Promotion`：折扣規則的生命週期（FIXED_AMOUNT / PERCENTAGE / FREE_DAYS）。
- `StoragePromotion`：倉位 ↔ 優惠的 many-to-many 連結表。
- `ChannelRelease`：發布動作的不可變快照（包含 unit_ids、promotion_id、channels、actor、狀態機）。
- `Location`：據點 URL mapping（供 PricingDashboard 外連官網用）。
- Website（storeasynewwebsite）：只是投影/消費者，不是庫存或折扣的 source of truth。

---

## Target workflow（標準發布流程）

```
1. [Promotion Manager] 建立優惠規則 → 狀態 is_active=true
2. [Storage Inventory] 過濾空倉 → 勾選目標倉位 → 「加入發布草稿」
       → 自動建立 ChannelRelease (DRAFT) → 跳轉 Channel Manager
3. [Channel Manager] 審視 DRAFT → 確認 store / channels / units
       → 觸發 APPROVED → 執行 PUBLISHING → 更新 WebsitePricingUnit flags → PUBLISHED
4. [Pricing Dashboard] 讀取 published-pricing API → 驗證最終售價與優惠是否正確
       → 點擊 Eye 圖示確認官網實際頁面
5. [Marketing Insights] 追蹤 release/campaign/promotion 轉換效果
```

---

## Channel semantics（通路語意）

- 空 channels = 未發布；絕對不預設為 Shop。
- Shop-only：`is_published_shop=true`，`is_published_location=false`。
- Location-only：`false`，`true`。
- 兩者皆是：`true`，`true`。
- 移除優惠必須是明確的 nullable/delete 操作，不能傳空字串。
- Bundle 虛擬倉位：`is_bundle=True`，`bundled_st_ids=["UD140","UU041"]`；預訂時鎖定所有實體倉。

---

## Known UI gaps（目前已知 UI 缺陷待修）

| 缺陷 | 位置 | 影響 |
|---|---|---|
| 「查看 →」殭屍按鈕 | ChannelManager Release 列表 | 無法查看草稿詳情，無法做 APPROVED/REJECT 審批操作 |
| `ChannelReleaseDraftModal` dead code | ChannelManager.tsx import | 已 import 但從未掛載，需補上 onClick 並正確掛載 |
| PricingDashboard 的 `PromotionAggregatorWizard` | 批量設定優惠 | 是否寫回 ChannelRelease 待確認（不可繞過審批直接發布） |

---

## Acceptance scenarios（驗收場景）

- 證明 Shop-only 不出現在據點價格表，Location-only 不出現在 `/public/products`。
- 驗證兩通路發布與快取失效後的完整下架。
- 在不刪除倉位的前提下移除優惠。
- 搶先佔用後的 preflight 競態拒絕。
- 相同 idempotency key 重試不重複建立。
- 官網傳播失敗後能 Resume。
- 精確回滾至發布前的旗標、優惠、價格、內容。
