# Windows 背景執行緒 Ultralytics × Polars Rayon Access Violation 解決方案

- **Date**: 2026-11-17
- **Context**: `YoloMono` (`Windows 11 + Python 3.12 + PyTorch CPU + ONNXRuntime + Ultralytics 8.4`)

## [Anti-Pattern 錯誤模式]
- 在 Windows 同一個 Python 進程中，經過 `onnxruntime` / `OpenMP` 初始化並先後建立多條 `threading.Thread` 執行 `model.train()` 時，Ultralytics 於訓練收尾呼叫 `trainer.read_results_csv()` -> `polars.read_csv()` 會觸發 Polars Rust Rayon 預設多執行緒池初始化，極易發生原生 `Windows fatal exception: access violation`（非 Python `try/except` 可捕獲）。

## [Correct-Pattern 正確作法]
- 在後端訓練排程模組頂部與測試進入點 (`conftest.py`) 於任何載入 Ultralytics / Polars 之前固定設定：
  ```python
  os.environ.setdefault("POLARS_MAX_THREADS", "1")
  ```
- 若仍須防禦外部 CLI，在啟動測試或訓練服務前強制指定 `POLARS_MAX_THREADS=1`，可 100% 穩定執行全套背景訓練與驗證。
