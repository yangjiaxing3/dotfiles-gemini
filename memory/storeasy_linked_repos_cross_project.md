# [Correct-Pattern] Storeasy 聯動家族（6-Repo Nexus）：允許跨 repo 修改與驗證

## 📌 Context

授權日：2026-08-23（jiaxing 明示），2026-10-31 擴充為 6-Repo Nexus。
觸發：官網文章頁 404（例：`/news/mothers-day-收多易母親節活動首月只要520`）根因跨 FM CMS 與 `storeasynewwebsite` ISR；只改單一工作區無法完成驗證。

Storeasy 不是孤立 repo。FM 寫入成功 ≠ 官網已更新。文章、定價、Hero、revalidate、共享 Turso、工務 CDC、人資財會 CDC 都必須雙邊一起改、雙邊一起驗證。

---

## ❌ [Anti-Pattern 錯誤模式]

1. 把 Boundary Sentinel 的「禁止跨出當前工作區」套用到 Storeasy sibling repo，然後停下來問使用者要不要開 `storeasynewwebsite` 或 `StoreasyFinHR`。
2. 望文生義把 `Storeasyworkdivnew`（工務管理系統）誤當成排班/人資系統，而漏掉真正的財務與人事勞基法排班系統 **`StoreasyFinHR`**。

---

## ✅ [Correct-Pattern 正確作法]

當前工作區只要屬於 Storeasy 聯動家族，**不必再問**即可讀寫並驗證以下 6 個 sibling repo：

| Repo | 業務定位與核心職責 | 本機 Port (Backend / Frontend) | 路徑 |
|---|---|---|---|
| `StoreasyFMnew` | 收多易中台管理系統（據點 SoT `s_ino`、營運合約/來訪、空間定價、官網 CMS 與 Channel Manager） | `8000 / 5100` | `C:\Users\Jiaxing\Documents\GitHub\StoreasyFMnew` |
| `storeasynewwebsite` | 收多易迷你倉公開官方網站（Next.js 16 前台、據點頁、預約、3D 模擬器、部落格與 ISR 快取） | `— / 3000` | `C:\Users\Jiaxing\Documents\GitHub\storeasynewwebsite` |
| `storeasycws` | 收多易共同工作空間公開官網（與 FM 共用 Turso 實例、自有表前綴 `cws_`、依 `st_id` 第二字母 C/O/R 分流會議室/辦公室/借址登記） | `— / 3001` | `C:\Users\Jiaxing\Documents\GitHub\storeasycws` |
| `STOREASY_IT` | 收多易 IT 資產全生命週期管理系統（採購、入庫、部署、盤點、報廢；發布 Turso `it_assets` 快照表） | `8001 / 5173` | `C:\Users\Jiaxing\Documents\GitHub\STOREASY_IT` |
| `Storeasyworkdivnew` | 收多易**工務管理與工程數據中台**（工程報價單 AI 解析、採購工單 `workdiv_orders`、市場行情比價、廠商評鑑與據點工務映射；`workdiv` = 工務部，**嚴禁誤譯為排班/人資**） | `8002 / 5173` | `C:\Users\Jiaxing\Documents\GitHub\Storeasyworkdivnew` |
| `StoreasyFinHR` | 收多易**財務與人事管理系統**（台灣勞基法規引擎 `labor_rules`、OR-Tools 決定性排班求解器 `seed=42`、考勤與加班費、38 欄薪資結算閉環；表名前綴 `finhr_`） | `8003 / 5103` | `C:\Users\Jiaxing\Documents\GitHub\StoreasyFinHR` |

仍禁止：無關專案、secrets 入庫、生產 DB 破壞性操作、未確認的 force-push。

契約必讀：
- `StoreasyFMnew/docs/architecture/storeasy-two-project-context.md`
- `StoreasyFMnew/docs/architecture/shared-db-contract.md`
- `StoreasyFMnew/docs/architecture/multi-project-linkage-contract.md`
- `StoreasyFMnew/docs/architecture/domain-identifier-contract.md`
- `StoreasyFinHR/docs/architecture/finhr-family-context.md`

---

## 📌 Post-Mortem 補充（2026-10-17 & 2026-10-31：6-Repo Nexus 圖譜與契約紀律）

### ❌ [Anti-Pattern 錯誤模式]
1. **直接修改官網靜態檔案繞過後台 CMS**：當使用者要求修改官網文案（如首頁/FAQ 禁放規定、Hero Banner、全站公告、優惠活動、分店價目表）時，只看 `storeasynewwebsite` 本地靜態檔就直接硬改，忽略了 `StoreasyFMnew` 的 CMS 編輯與 `revalidateTag` 管線。
2. **跨專案 Companion PR 只做半套**：在 `StoreasyFMnew` 或 `StoreasyFinHR` 實作了後端 API 與 CDC 表，卻沒對齊消費端或契約。
3. **Graphify 全域圖譜 `XREF_` 丟失**：執行 `graphify update` / `extract` 後未注入 `~/.graphify/nexus-cross-links.json`，導致跨 repo 的 API / DB / CDC 契約邊在圖譜中消失。

### ✅ [Correct-Pattern 正確作法]
1. **凡修改官網內容，必先查驗 `StoreasyFMnew` CMS 管線**：
   - 必須走 **`FMnew 種子/API → Turso 共享表 → 官網 Data Fetcher (含 revalidateTag) → 離線靜態備援`** 完整鏈路，嚴禁讓 Page/UI 元件直接 import 靜態備援檔。
2. **執行跨專案契約防呆測試 (`src/lib/__tests__/cross-repo-contract.test.ts`)**：
   - 每次修改後必須執行 `npx tsx --test "src/lib/__tests__/cross-repo-contract.test.ts"`。
3. **維護 `~/.graphify/nexus-cross-links.json` 與 `global-graph.json`**：
   - 跨專案新增或修改 API / 共享表 / CDC 通道時，同步更新 `~/.graphify/nexus-cross-links.json` 與 `storeasynewwebsite/graphify-out/cross-links.json` 並注入 `~/.graphify/global-graph.json`。
