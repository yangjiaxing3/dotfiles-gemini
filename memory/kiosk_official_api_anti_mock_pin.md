# Kiosk 官方 7 支 API 與取件碼禁假碼規範 (Skeptical Audit Pattern)

## [Anti-Pattern 錯誤模式]
1. **前端殘留 `Math.random()` 假隨機 PIN 碼 fallback**：
   - 在 `StorePickupCodeScreen.tsx` 或 `UnlockScreen.tsx` 中，當後端 `/api/kiosks/:id/pickup-code` 未回傳 `pwd` 時，使用 `Array.from({ length: 6 }, () => Math.floor(Math.random() * 10)).join('')` 產生隨機 6 位數顯示給現場外勤／店長。
   - **後果**：現場人員在 Kiosk 機台輸入亂數假密碼永遠無法開倉，且讓開發者誤以為「取件碼畫面有顯示數字＝已完成」。
2. **只讀 API 1 (`get_kiosk_machine_list.php`) 的靜態 `pwd` 或只查未同步的本地 DB 表，而未串接 API 2 (`get_r3_order.php`)、API 6 (`generate_logistics_pwd.php`)、API 7 (`logistics_pwd_cancel.php`)**：
   - 若機台當下尚未產生取件密碼，`get_kiosk_machine_list.php` 的 `pwd` 為空；若未呼叫 API 6 (`generate_logistics_pwd.php`)，外勤人員無法在現場動態申請密碼，也無法透過 API 7 (`logistics_pwd_cancel.php`) 註銷舊密碼重產新碼。

## [Correct-Pattern 正確作法]
1. **嚴格對位官方 7 支 API（`tab=t.agt1jidrjy40#heading=h.57gl23klpyxe`）**：
   - **API 1 (`get_kiosk_machine_list.php`)**：`POST application/x-www-form-urlencoded` + `checksum = MD5(yyyyMMdd + "sogo_on_web_2021")`。
   - **API 2 (`get_r3_order.php`)**：`POST` 帶 `recycling_machine_id` + `checksum`，即時取得機台 R3 待取訂單明細（`order_id`, `model_name`, `inquiry_no`, `order_price`）。
   - **API 3 (`securaze_deviceidquery_proxy.php`)** & **API 4 (`kiosk_deviceidquery_proxy.php`)**：`POST` 帶 `deviceids`（至少 6 碼）。
   - **API 5 (`get_appraisal_info`)**：`POST` 帶 `order_id` + `checksum = MD5(order_id + "us3ctk")`，並剝除外層 XML `<string>...</string>` 後解析 JSON。
   - **API 6 (`generate_logistics_pwd.php`)**：帶 `u_ino`, `u_name`, `recycling_machine_id`, `checksum`；若回傳 `status: "fail"` 且含 `existing_pwd`（`"此機台已有尚未使用的密碼，請先取消後再產生"`），應直接採用 `existing_pwd` 與 `existing_pickup_no` 顯示，並提供「註銷並重新產碼」按鈕。
   - **API 7 (`logistics_pwd_cancel.php`)**：帶 `u_ino`, `u_name`, `recycling_machine_id`, `code`, `checksum`，完整解析 `updated_by_pk`, `kiosk_pwd_log_no`, `cancellation_name`, `cancellation_name_id`, `cancellation_datetime`。
2. **全面禁止前端亂數 PIN fallback**：
   - 任何開倉／解鎖畫面（`StorePickupCodeScreen`、`UnlockScreen`、`OpenCabinetScreen`）絕對禁止使用 `Math.random()` 生成 PIN 碼；若 API 無法取得有效取件碼，必須明確顯示錯誤原因並將「已完成開倉／確認解鎖」按鈕設為 `disabled`。
