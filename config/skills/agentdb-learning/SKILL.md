---
name: agentdb-learning
description: "Use when configuring reinforcement learning plugins (Q-Learning, Actor-Critic) in AgentDB. AgentDB強化學習插件配置"
---

# AgentDB Learning Plugins

## What This Skill Does

Provides access to 9 reinforcement learning algorithms via AgentDB's plugin system. Create, train, and deploy learning plugins for autonomous agents that improve through experience. Includes offline RL (Decision Transformer), value-based learning (Q-Learning), policy gradients (Actor-Critic), and advanced techniques.

**Performance**: Train models 10-100x faster with WASM-accelerated neural inference.

## Prerequisites

- Node.js 18+
- AgentDB v1.0.7+ (via agentic-flow)
- Basic understanding of reinforcement learning (recommended)

---

## Quick Start with CLI

### Create Learning Plugin

```bash
# Interactive wizard
npx agentdb@latest create-plugin

# Use specific template
npx agentdb@latest create-plugin -t decision-transformer -n my-agent

# Preview without creating
npx agentdb@latest create-plugin -t q-learning --dry-run

# Custom output directory
npx agentdb@latest create-plugin -t actor-critic -o .$plugins
```

### List Available Templates

```bash
# Show all plugin templates
npx agentdb@latest list-templates

# Available templates:
# - decision-transformer (sequence modeling RL - recommended)
# - q-learning (value-based learning)
# - sarsa (on-policy TD learning)
# - actor-critic (policy gradient with baseline)
# - curiosity-driven (exploration-based)
```

### Manage Plugins

```bash
# List installed plugins
npx agentdb@latest list-plugins

# Get plugin information
npx agentdb@latest plugin-info my-agent

# Shows: algorithm, configuration, training status
```

---

## Quick Start with API

```typescript
import { createAgentDBAdapter } from 'agentic-flow$reasoningbank';

// Initialize with learning enabled
const adapter = await createAgentDBAdapter({
  dbPath: '.agentdb$learning.db',
  enableLearning: true,       // Enable learning plugins
  enableReasoning: true,
  cacheSize: 1000,
});

// Store training experience
await adapter.insertPattern({
  id: '',
  type: 'experience',
  domain: 'game-playing',
  pattern_data: JSON.stringify({
    embedding: await computeEmbedding('state-action-reward'),
    pattern: {
      state: [0.1, 0.2, 0.3],
      action: 2,
      reward: 1.0,
      next_state: [0.15, 0.25, 0.35],
      done: false
    }
  }),
  confidence: 0.9,
  usage_count: 1,
  success_count: 1,
  created_at: Date.now(),
  last_used: Date.now(),
});

// Train learning model
const metrics = await adapter.train({
  epochs: 50,
  batchSize: 32,
});

console.log('Training Loss:', metrics.loss);
console.log('Duration:', metrics.duration, 'ms');
```

---

## Available Learning Algorithms (9 Total)

### 1. Decision Transformer (Recommended)

**Type**: Offline Reinforcement Learning
**Best For**: Learning from logged experiences, imitation learning
**Strengths**: No online interaction needed, stable training

```bash
npx agentdb@latest create-plugin -t decision-transformer -n dt-agent
```

**Use Cases**:
- Learn from historical data
- Imitation learning from expert demonstrations
- Safe learning without environment interaction
- Sequence modeling tasks

**Configuration**:
```json
{
  "algorithm": "decision-transformer",
  "model_size": "base",
  "context_length": 20,
  "embed_dim": 128,
  "n_heads": 8,
  "n_layers": 6
}
```

### 2. Q-Learning

## Progressive Disclosure References (On-Demand)
- Detailed templates, extended examples, and deep-dive checklists have been moved to [references/detailed-guide.md](./references/detailed-guide.md) to keep context lean. Load that file via `view_file` only when needed.

## ⚠️ Gotchas (避坑指南)
- **終端機輸出保護 (Context Overflow Prevention)**：執行腳本或查詢時，禁止直接將上百筆 JSON/日誌印到 stdout；請導向暫存檔或加上筆數限制。
- **優先使用確定性腳本**：遇到格式轉換、字數統計或合規檢查，優先調用 `scripts/` 下的 Python 工具，不要依賴純語意猜測。
