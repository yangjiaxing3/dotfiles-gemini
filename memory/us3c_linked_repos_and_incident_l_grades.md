# [Correct-Pattern] US3C 後台 ↔ DriverApp：異常單等級用 L1～L4，必須兩邊一起改

## 📌 Context

授權日：2026-08-23（jiaxing 明示）。
產品：`us3c-next`（後台）與 `us3cdriverapp`（司機端）共用 `machine_incidents` / `machine_inspections`。
官方 patrol HTML 只是 demo，**以我們的 L 等級為準**。

| Repo | 路徑 |
|---|---|
| `us3c-next` | `C:\Users\Jiaxing\Documents\GitHub\us3c-next` |
| `us3cdriverapp` | `C:\Users\Jiaxing\Documents\GitHub\us3cdriverapp` |

改異常單、巡視評等、或 `machine_incidents.severity` 時，**不必再問**即可讀寫 sibling，而且 **UI／UX 與寫入資料必須同一輪改完**。只改後台或只改 Driver 會讓開單失敗或兩邊用語打架。

仍禁止：無關專案、secrets 入庫、未確認的正式環境 SQL、force-push。

---

## 單一真相：兩套「S」不要再混

| 代號 | 用途 | 可否改成 L |
|---|---|---|
| **S2 / S3 步驟** | 巡視分組：S2 實體外觀與環境、S3 核心硬體與功能 | 否，步驟維持 S |
| **L1～L4 評等** | 檢查項結果 + 異常單嚴重程度 | 是，全面用 L |

| 等級 | 意思 |
|---|---|
| **L1** | 停機／安全異常 |
| **L2** | 服務異常，需維修 |
| **L3** | 日常維護 |
| **L4** | 正常／已排除或僅記錄 |

舊值 `S1`～`S4` 讀取時正規成 `L1`～`L4`。新寫入用 L。Driver 尚未改完前，DB CHECK 暫時同時允許 S 與 L（migration `20260823_02_incident_severity_l_grades.sql`）。正式環境套用前，後台新開單若寫 L 會被舊 CHECK 擋下。

後台已對齊：`IncidentSeverity = 'L1' \| 'L2' \| 'L3' \| 'L4'`、`normalizeIncidentSeverity`、`severityQueryValues`。檢查項畫面顯示 L，庫內 check_* 仍可暫存 S（`normalizeCheckGrade`）。

Driver 已於 2026-08-23 對齊：巡視選單與異常單 UI 用 L1～L4；`buildIncidentInsert` 寫 `L*`；`buildInspectionInsert` 的 check_* 仍寫 `S*`（後台檢查欄位型別）。步驟列 S1 感應打卡／S2 硬體巡檢／S3 功能測試／S4 其他回報維持 S。

---

## ❌ [Anti-Pattern 錯誤模式]

- 只改 `us3c-next` 異常單選單，Driver 巡視／開單還顯示並送 `S1`／`S2`。
- 把步驟 S2／S3 也改成 L，或把評等再叫回 S，兩邊又混在一起。
- 以為官方 HTML 的 S1／S2／S3 異常單用語還是權威。

---

## ✅ [Correct-Pattern 正確作法]

動到異常單或巡視評等時，**同一輪**改 Driver：

1. **UI／UX**：`S3_FunctionAndNotes.tsx`、`S2_QuickChecklist.tsx`、`IncidentReportSheet.tsx`、`PatrolWizardScreen.tsx` 的選單與文案改 L1～L4（步驟列「S1 感應打卡／S2 硬體巡檢」維持 S）。
2. **傳遞資料**：`driverapp/api/patrolPayload.ts`、`driverapp/api/server.ts` 寫入 `machine_incidents.severity` 用 `L1`～`L4`；推導與 `defaultsForGrade` 跟後台同一套。
3. **測試**：`patrol.spec.ts`、`PatrolWizard.test.tsx`、`patrol.test.ts` 斷言改 L；後台 `e2e-s2-incident-hq-tab.test.ts` 在 Driver payload 改完後一併改。
4. 兩邊都驗證：後台 `/machines` 異常 tab 看得到 Driver 剛開的 L 單。

後台對照：`src/features/machines/lib/rewardInspection.ts`、`types.ts` 的 `IncidentSeverity`、`MachineIncidentsTab.tsx`、`MachineInspectionTab.tsx`。
