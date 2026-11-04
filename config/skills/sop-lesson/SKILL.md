---
name: sop-lesson
description: "'撰寫 US3C／iMCheck 的 SOP 教學檔並套用標註配方。Use when a Cursor agent should create, edit, or play an SOP lesson, callout, 旁註, annotation r..."
---

# SOP 教學檔

Cursor 讀到這個 skill 就可以做教材。教學檔是一份 lesson JSON。播放器負責畫框，並把旁註放在框旁邊。

## 先讀

1. 讀 [references/lesson-file.md](references/lesson-file.md)。
2. 以 [assets/lesson.template.json](assets/lesson.template.json) 當底稿。
3. 框的座標維持截圖自身的 0–1，原點在左上。旁註只寫 `targetId`、`text`、`side`。

## 怎麼交出

- 整套教材：寫入 lesson JSON，讓編輯頁的「匯入 JSON」吃進去。`steps/03.jpg` 會對到 `/sop-demo/03.jpg`。
- 只改一步：打開編輯頁側欄 **進階 · 給 Agent**，把該步的 `recipe` 貼進「Agent 配方（JSON）」，按套用。播放器路徑是 `/sop/<專案 id>`，編輯路徑是 `/sop/<專案 id>/edit`。日常畫框與改出現秒數請用畫布和時間軸，不要把配方面板當成時間編輯器。
- 套用前先在心裡跑過驗證：版本是 1、id 不重複、callout 的 targetId 指向這份配方裡已出現的 rectangle、旁註 40 字以內、文字只使用 US3C／iMCheck。任一項不合法，整份配方作廢，保留畫面上原來的框。

## 播放器會做的事

框先出現。480ms 後旁註淡入。`side` 是偏好方向；那一側離邊緣不到 0.18 時，字改放到空間比較大的一側。練習和播放都一樣。系統開了減少動態時，框和字同時出現。

標註樣式由播放器決定：直角、1.75px 紅框。配方裡的 color、lineWidth 可以留著，播放器會略過。

## ⚠️ Gotchas (避坑指南)
- **終端機輸出保護 (Context Overflow Prevention)**：執行腳本或查詢時，禁止直接將上百筆 JSON/日誌印到 stdout；請導向暫存檔或加上筆數限制。
- **零區防禦與 Port 禁令**：修改或執行指令前嚴守工作區邊界，嚴禁綁定或終止保留埠 (8000、5100、3000)。
