---
description: "Python / FastAPI 後端開發規範，含分層架構、型別、日誌及後端安全"
globs: ["**/*.py"]
---

# Python / FastAPI 規範

## 基本要求

- Python ≥ 3.10，優先使用 FastAPI
- 所有函式必須標註型別
- 禁止裸 `except`，禁止用 `print` 當日誌

## 分層結構（強制）

```
api/        → 請求解析與回應封裝
service/    → 業務邏輯處理
repository/ → 資料庫存取
schema/     → 請求 / 回應資料驗證
model/      → ORM 模型定義
```

禁止在 api 層直接操作資料庫。

## 日誌規範

- 使用 `logging` 模組，區分 DEBUG / INFO / WARNING / ERROR
- 日誌中不得包含敏感資訊

## 後端安全

- 使用 Pydantic 進行參數驗證
- 權限校驗在 service 層完成
- 密鑰一律從環境變數讀取（`os.getenv()`）
- 敏感欄位回傳前需脫敏，密碼必須加密儲存

## 文件註解

- 使用 Python Docstring 格式撰寫函式註解
