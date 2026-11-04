# Turso Hrana HTTP v2：float 不是 double

- **日期**：2026-09-11
- **專案**：STOREASY_IT
- **症狀**：CAD `import-cad` 解析成功，`db.commit()` 對 `floor_plans` INSERT 時 Turso 回 400：`unknown variant double, expected one of null, integer, float, text, blob`。
- **原因**：`scale_factor` 是 Python `float`，`TursoClient.hrana_value` 編成 `{"type":"double"}`。舊註解／asset publish 測試跟著寫錯。
- **[Anti-Pattern]**：把 libsql／舊文件的 `double` 標籤直接用在 Turso `/v2/pipeline`。
- **[Correct-Pattern]**：`TursoClient.hrana_value` 對 float 送 `{"type":"float","value": n}`。`AssetPublishService._hrana_value` 必須委派同一函式，不要再複製一份。
- **驗證**：本機 multipart 上傳新莊公園 DXF → floorplan id=2，179 格、161 綁定。
