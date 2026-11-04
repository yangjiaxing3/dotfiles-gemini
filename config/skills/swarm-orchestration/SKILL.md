---
name: swarm-orchestration
description: "Use when coordinating 3+ file cross-module refactors using hierarchical multi-agent swarm topologies. 跨模組多檔案Swarm群體協作重構"
---

# Swarm Orchestration Skill

## Purpose
Multi-agent swarm coordination for complex tasks. Uses hierarchical topology with specialized agents to break down and execute complex work across multiple files and modules.

## When to Trigger
- 3+ files need changes
- new feature implementation
- cross-module refactoring
- API changes with tests
- security-related changes
- performance optimization across codebase
- database schema changes

## When to Skip
- single file edits
- simple bug fixes (1-2 lines)
- documentation updates
- configuration changes
- quick exploration

## Commands

### Initialize Swarm
Start a new swarm with hierarchical topology (anti-drift)

```bash
[Swarm Initialization Action] Initialize parallel agent swarm with parameters: --topology hierarchical --max-agents 8 --strategy specialized
```

**Example:**
```bash
[Swarm Initialization Action] Initialize parallel agent swarm with parameters: --topology hierarchical --max-agents 6 --strategy specialized
```

### Route Task
Route a task to the appropriate agents based on task type

```bash
[Task Routing Action] Route task to the appropriate specialized subagent. Task: "[task description]"
```

**Example:**
```bash
[Task Routing Action] Route task to the appropriate specialized subagent. Task: "implement OAuth2 authentication flow"
```

### Spawn Agent
Spawn a specific agent type

```bash
npx @claude-flow/cli agent spawn --type [type] --name [name]
```

**Example:**
```bash
npx @claude-flow/cli agent spawn --type coder --name impl-auth
```

### Monitor Status
Check the current swarm status

```bash
[Swarm Status Action] Check the status of parallel subagents --verbose
```

### Orchestrate Task
Orchestrate a task across multiple agents

```bash
[Task Orchestration Action] Orchestrate task: "[task]" with settings: --strategy adaptive
```

**Example:**
```bash
[Task Orchestration Action] Orchestrate task: "refactor auth module" with settings: --strategy parallel --max-agents 4
```

### List Agents
List all active agents

```bash
[Agent List Action] List active subagents --filter active
```


## Scripts

| Script | Path | Description |
|--------|------|-------------|
| `swarm-start` | `.agents/scripts/swarm-start.sh` | Initialize swarm with default settings |
| `swarm-monitor` | `.agents/scripts/swarm-monitor.sh` | Real-time swarm monitoring dashboard |


## References

| Document | Path | Description |
|----------|------|-------------|
| `Agent Types` | `docs/agents.md` | Complete list of agent types and capabilities |
| `Topology Guide` | `docs/topology.md` | Swarm topology configuration guide |

## Best Practices
1. Check memory for existing patterns before starting
2. Use hierarchical topology for coordination
3. Store successful patterns after completion
4. Document any new learnings

## ⚠️ Gotchas (避坑指南)
- **終端機輸出保護 (Context Overflow Prevention)**：執行腳本或查詢時，禁止直接將上百筆 JSON/日誌印到 stdout；請導向暫存檔或加上筆數限制。
- **優先使用確定性腳本**：遇到格式轉換、字數統計或合規檢查，優先調用 `scripts/` 下的 Python 工具，不要依賴純語意猜測。
