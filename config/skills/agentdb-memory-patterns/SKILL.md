---
name: agentdb-memory-patterns
description: "Use when implementing persistent session and long-term vector memory patterns for stateful AI agents. AgentDB持久化記憶架構設計"
---

# AgentDB Memory Patterns

## What This Skill Does

Provides memory management patterns for AI agents using AgentDB's persistent storage and ReasoningBank integration. Enables agents to remember conversations, learn from interactions, and maintain context across sessions.

**Performance**: 150x-12,500x faster than traditional solutions with 100% backward compatibility.

## Prerequisites

- Node.js 18+
- AgentDB v1.0.7+ (via agentic-flow or standalone)
- Understanding of agent architectures

## Quick Start with CLI

### Initialize AgentDB

```bash
# Initialize vector database
npx agentdb@latest init .$agents.db

# Or with custom dimensions
npx agentdb@latest init .$agents.db --dimension 768

# Use preset configurations
npx agentdb@latest init .$agents.db --preset large

# In-memory database for testing
npx agentdb@latest init .$memory.db --in-memory
```

### Start MCP Server for Claude Code

```bash
# Start MCP server (integrates with Claude Code)
npx agentdb@latest mcp

# Add to Claude Code (one-time setup)
claude mcp add agentdb npx agentdb@latest mcp
```

### Create Learning Plugin

```bash
# Interactive plugin wizard
npx agentdb@latest create-plugin

# Use template directly
npx agentdb@latest create-plugin -t decision-transformer -n my-agent

# Available templates:
# - decision-transformer (sequence modeling RL)
# - q-learning (value-based learning)
# - sarsa (on-policy TD learning)
# - actor-critic (policy gradient)
# - curiosity-driven (exploration-based)
```

## Quick Start with API

```typescript
import { createAgentDBAdapter } from 'agentic-flow$reasoningbank';

// Initialize with default configuration
const adapter = await createAgentDBAdapter({
  dbPath: '.agentdb$reasoningbank.db',
  enableLearning: true,      // Enable learning plugins
  enableReasoning: true,      // Enable reasoning agents
  quantizationType: 'scalar', // binary | scalar | product | none
  cacheSize: 1000,            // In-memory cache
});

// Store interaction memory
const patternId = await adapter.insertPattern({
  id: '',
  type: 'pattern',
  domain: 'conversation',
  pattern_data: JSON.stringify({
    embedding: await computeEmbedding('What is the capital of France?'),
    pattern: {
      user: 'What is the capital of France?',
      assistant: 'The capital of France is Paris.',
      timestamp: Date.now()
    }
  }),
  confidence: 0.95,
  usage_count: 1,
  success_count: 1,
  created_at: Date.now(),
  last_used: Date.now(),
});

// Retrieve context with reasoning
const context = await adapter.retrieveWithReasoning(queryEmbedding, {
  domain: 'conversation',
  k: 10,
  useMMR: true,              // Maximal Marginal Relevance
  synthesizeContext: true,    // Generate rich context
});
```

## Memory Patterns

### 1. Session Memory
```typescript
class SessionMemory {
  async storeMessage(role: string, content: string) {
    return await db.storeMemory({
      sessionId: this.sessionId,
      role,
      content,
      timestamp: Date.now()
    });
  }

  async getSessionHistory(limit = 20) {
    return await db.query({
      filters: { sessionId: this.sessionId },
      orderBy: 'timestamp',
      limit
    });
  }
}
```

### 2. Long-Term Memory
```typescript
// Store important facts
await db.storeFact({
  category: 'user_preference',
  key: 'language',
  value: 'English',
  confidence: 1.0,
  source: 'explicit'
});

// Retrieve facts
const prefs = await db.getFacts({
  category: 'user_preference'
});
```

### 3. Pattern Learning
```typescript
// Learn from successful interactions
await db.storePattern({
  trigger: 'user_asks_time',
  response: 'provide_formatted_time',
  success: true,
  context: { timezone: 'UTC' }
});

// Apply learned patterns
const pattern = await db.matchPattern(currentContext);
```


## Progressive Disclosure References (On-Demand)
- Detailed templates, extended examples, and deep-dive checklists have been moved to [references/detailed-guide.md](./references/detailed-guide.md) to keep context lean. Load that file via `view_file` only when needed.

## ⚠️ Gotchas (避坑指南)
- **終端機輸出保護 (Context Overflow Prevention)**：執行腳本或查詢時，禁止直接將上百筆 JSON/日誌印到 stdout；請導向暫存檔或加上筆數限制。
- **優先使用確定性腳本**：遇到格式轉換、字數統計或合規檢查，優先調用 `scripts/` 下的 Python 工具，不要依賴純語意猜測。
