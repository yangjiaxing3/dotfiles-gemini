# Lesson file

Agent Skills 的佈局照拓（Ta）與 kangarooking-skills：`SKILL.md` 寫流程，`references/` 放規格，`assets/` 放可填的模板。Cursor 從 `.agent/skills/sop-lesson` 載入，Grok 4.7 直接照這份規格寫 JSON。

拓的 `ta transform --recipe` 會把標註畫進 PNG，而且 `text` 要自備 `origin`。這份教學檔改成播放器配方：

- `rectangle` 的 `rect` 用 `{x, y, width, height}`，單位是截圖的 0–1。
- `callout` 對準某個 rectangle 的 `id`。方向只有 `left`、`right`、`top`、`bottom`。
- `eraser` 的 `targetIds` 刪掉這份結果裡已經存在的框。
- 一份配方裡只要出現 `rectangle`，這一步的框就以這些 rectangle 為準。
- 沒有 `rectangle` 時，只更新現有框的旁註，或用 eraser 刪框。
- 任一欄位大於 1，整份改視為像素，並要有 `image.width` 與 `image.height`。同一份不能混用 0–1 和像素。
- `type: "text"` 配 `origin` 會整份失敗。訊息是：旁註請寫成 callout，帶 targetId、text、side。不要另給文字座標。

## 範例

步驟 3，框住「測 iOS」，字放右側：

```json
{
  "version": 1,
  "operations": [
    {
      "type": "rectangle",
      "id": "ios-check",
      "rect": { "x": 0.0602, "y": 0.673, "width": 0.1185, "height": 0.091 },
      "zoom": true,
      "highlight": true
    },
    {
      "type": "callout",
      "id": "ios-check-label",
      "targetId": "ios-check",
      "text": "選 iPhone 檢測",
      "side": "right"
    }
  ]
}
```

步驟 2 的估價框靠近底部，`side` 寫 `top`。播放器會把「點估價」放在框的上方。

像素配方要補圖片尺寸，播放器再除回 0–1：

```json
{
  "version": 1,
  "image": { "width": 1170, "height": 2532 },
  "operations": [
    {
      "type": "rectangle",
      "id": "ios-check",
      "rect": { "x": 73, "y": 1706, "width": 132, "height": 227 }
    }
  ]
}
```

整套教材把 recipe 放進每個 step。見 `assets/lesson.template.json`。
