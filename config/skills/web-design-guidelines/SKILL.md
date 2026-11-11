---
name: web-design-guidelines
description: "Use when auditing UI code against Web Interface Guidelines, UX ergonomics, and keyboard/screen-reader accessibility. 介面規範審查/UX與無障礙檢查"
version: "1.0.0"
---

# Web Interface Guidelines

Review files for compliance with Web Interface Guidelines.

## How It Works

1. Fetch the latest guidelines from the source URL below
2. Read the specified files (or prompt user for files/pattern)
3. Check against all rules in the fetched guidelines
4. Output findings in the terse `file:line` format

## Guidelines Source

Fetch fresh guidelines before each review:

```
https://raw.githubusercontent.com/vercel-labs/web-interface-guidelines/main/command.md
```

Use WebFetch to retrieve the latest rules. The fetched content contains all the rules and output format instructions.

## Usage

When a user provides a file or pattern argument:
1. Fetch guidelines from the source URL above
2. Read the specified files
3. Apply all rules from the fetched guidelines
4. Output findings using the format specified in the guidelines

If no files specified, ask the user which files to review.

## ⚠️ Gotchas (避坑指南)
- **禁止廉價 AI 模板感 (Anti-Slop)**：避免過度使用無意義的紫藍漸層、千篇一律的三欄卡片與脫離業務語境的假數字。
- **嚴禁 UI Emoji，統一使用乾淨 SVG 圖示**：審查 UI 時，凡發現頁面標題、徽章、按鈕或表格出現 Emoji 一律列為違規，須改為乾淨 SVG 或 `lucide-react` 圖示。
- **按鈕極簡化（2～4 字或純 Icon）與去冗餘說明**：操作按鈕文案強制精簡為 **2～4 個字**或純 SVG Icon 按鈕（必備 `title` 與 `aria-label`），禁止冗長句子按鈕與重複標題語意的副標題。
- **日期與表單無障礙**：所有 `<input type="date" lang="en" />` 強制加註 `lang="en"`；互動按鈕需具備明確 `title` 或 `aria-label` 與鍵盤焦點狀態。
