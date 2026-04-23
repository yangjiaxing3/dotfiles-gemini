---
description: "Flutter / Dart 開發規範，含 Widget 設計、狀態管理、效能及專案結構"
globs: ["**/*.dart"]
---

# Flutter / Dart 規範

## Widget 設計

- 優先使用 StatelessWidget，只在需要局部狀態時用 StatefulWidget
- 單一 Widget 單一職責，拆分大型 build 方法為子 Widget
- 避免深層巢狀，善用 `const` 建構子提升效能

## 狀態管理

- 使用 Provider 進行跨層狀態傳遞（專案已採用）
- ChangeNotifier 只放業務邏輯，不放 UI 邏輯
- 避免在 build 方法中執行副作用

## 專案結構

```
lib/
├── core/       → 全域工具、常數、主題
├── models/     → 資料模型
├── providers/  → 狀態管理（ChangeNotifier）
├── screens/    → 頁面級 Widget
├── services/   → API 呼叫、本地儲存
└── widgets/    → 可複用 UI 元件
```

## 效能與安全

- 長列表使用 `ListView.builder`，避免一次建構所有項目
- 圖片使用 `cached_network_image` 做快取
- 敏感資訊使用 `flutter_secure_storage`，不存 SharedPreferences

## 命名慣例

- 檔案名：snake_case（`user_card.dart`）
- 類別名：PascalCase（`UserCard`）
- 常數與列舉值：lowerCamelCase（Dart 官方慣例）
