# Storeasy CWS 倉位號碼（跨專案記憶）

權威：`StoreasyFMnew/docs/architecture/domain-identifier-contract.md` §6。  
實作：`classify_cws_unit`、`summarize_cws_inventory` → `GET /api/spaces/summary`。  
UI：多功能空間租賃（`/spaces`）辦公室／借址分頁用第二字母分流雲端 `storage_inventory` 並計數可租／使用中。

僅當「分店類型」精確等於 `CWS` 時套用。

- 語法：`^[A-Z][A-Z]\d+$`（只 trim + uppercase，禁止去連字號再解析）
- 第 1 字母 = 店前綴（不是服務）
- 第 2 字母 = 唯一分流鍵
- 金標：`NR001` → `R` → `bizreg`（借址登記）
- CWS 第二字母：A `cws_locker` / W `flex_seat` / S `fixed_seat` / X `trial` / C `meeting_room` / O `office` / R `bizreg`
- 倉庫 U/D/B/P 禁止套到 CWS（`PD318` → unknown）
- `CWS-001`、`CWS001` → unknown
- 會議室訂單仍走 SMIS（`rl_ino`），不要用編碼 C 的倉位數去取代檔期訂單數
