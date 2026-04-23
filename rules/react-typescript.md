---
description: "React + TypeScript 前端開發規範，含元件設計、Hooks、效能及前端安全"
globs: ["**/*.tsx", "**/*.ts", "**/*.jsx"]
---

# React + TypeScript 規範

## 元件設計

- 僅用函式元件，禁止 class 元件
- 單一元件單一職責，展示與業務邏輯分離
- 可複用邏輯抽離為自訂 Hook（`use` 前綴）
- Props 必須定義 TypeScript 介面，用解構接收

## Hooks 規範

- 只在函式元件或自訂 Hook 頂層呼叫
- 禁止在條件 / 迴圈中呼叫
- 一個 Hook 只處理一種職責

## 效能要求

- 合理使用 `useMemo` / `useCallback`，避免不必要的重渲染
- 列表渲染必須提供穩定 `key`
- 大資料列表使用虛擬捲動
- 路由與元件支援懶載入

## 前端安全

- 禁止 `dangerouslySetInnerHTML`
- 防範 XSS / CSRF，不在前端儲存敏感資訊
- Token 推薦使用 HttpOnly Cookie

## 文件註解

- 使用 JSDoc 格式撰寫函式註解
