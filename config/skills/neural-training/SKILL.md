---
name: neural-training
description: "Use when running SONA/MoE neural pattern consolidation and adaptive routing training. 神經模式訓練與自適應路由"
---

# Neural Training Skill

## Purpose
Train and optimize neural patterns using SONA, MoE, and EWC++ systems.

## When to Trigger
- Training new patterns
- Optimizing agent routing
- Knowledge consolidation
- Pattern recognition tasks

## Intelligence Pipeline

1. **RETRIEVE** — Fetch relevant patterns via HNSW (150x-12,500x faster)
2. **JUDGE** — Evaluate with verdicts (success$failure)
3. **DISTILL** — Extract key learnings via LoRA
4. **CONSOLIDATE** — Prevent catastrophic forgetting via EWC++

## Components

| Component | Purpose | Performance |
|-----------|---------|-------------|
| SONA | Self-optimizing adaptation | <0.05ms |
| MoE | Expert routing | 8 experts |
| HNSW | Pattern search | 150x-12,500x |
| EWC++ | Prevent forgetting | Continuous |
| Flash Attention | Speed | 2.49x-7.47x |

## Commands

### Train Patterns
```bash
npx claude-flow neural train --model-type moe --epochs 10
```

### Check Status
```bash
npx claude-flow neural status
```

### View Patterns
```bash
npx claude-flow neural patterns --type all
```

### Predict
```bash
npx claude-flow neural predict --input "task description"
```

### Optimize
```bash
npx claude-flow neural optimize --target latency
```

## Best Practices
1. Use pretrain hook for batch learning
2. Store successful patterns after completion
3. Consolidate regularly to prevent forgetting
4. Route based on task complexity

## ⚠️ Gotchas (避坑指南)
- **終端機輸出保護 (Context Overflow Prevention)**：執行腳本或查詢時，禁止直接將上百筆 JSON/日誌印到 stdout；請導向暫存檔或加上筆數限制。
- **優先使用確定性腳本**：遇到格式轉換、字數統計或合規檢查，優先調用 `scripts/` 下的 Python 工具，不要依賴純語意猜測。
