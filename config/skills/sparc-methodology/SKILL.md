---
name: sparc-methodology
description: "Use when tackling complex system designs via SPARC (Specification, Pseudocode, Architecture, Refinement, Completion). SPARC五階段系統開發與實作計畫"
---

# Sparc Methodology Skill

## Purpose
SPARC development workflow: Specification, Pseudocode, Architecture, Refinement, Completion. A structured approach for complex implementations that ensures thorough planning before coding.

## When to Trigger
- new feature implementation
- complex implementations
- architectural changes
- system redesign
- integration work
- unclear requirements

## When to Skip
- simple bug fixes
- documentation updates
- configuration changes
- well-defined small tasks
- routine maintenance

## Commands

### Specification Phase
Define requirements, acceptance criteria, and constraints

```bash
[Task Routing Action] Route task to the appropriate specialized subagent. Task: "specification: [requirements]"
```

**Example:**
```bash
[Task Routing Action] Route task to the appropriate specialized subagent. Task: "specification: user authentication with OAuth2, MFA, and session management"
```

### Pseudocode Phase
Write high-level pseudocode for the implementation

```bash
[Task Routing Action] Route task to the appropriate specialized subagent. Task: "pseudocode: [feature]"
```

**Example:**
```bash
[Task Routing Action] Route task to the appropriate specialized subagent. Task: "pseudocode: OAuth2 login flow with token refresh"
```

### Architecture Phase
Design system structure, interfaces, and dependencies

```bash
[Task Routing Action] Route task to the appropriate specialized subagent. Task: "architecture: [design]"
```

**Example:**
```bash
[Task Routing Action] Route task to the appropriate specialized subagent. Task: "architecture: auth module with service layer, repository, and API endpoints"
```

### Refinement Phase
Iterate on the design based on feedback

```bash
[Task Routing Action] Route task to the appropriate specialized subagent. Task: "refinement: [feedback]"
```

**Example:**
```bash
[Task Routing Action] Route task to the appropriate specialized subagent. Task: "refinement: add rate limiting and brute force protection"
```

### Completion Phase
Finalize implementation with tests and documentation

```bash
[Task Routing Action] Route task to the appropriate specialized subagent. Task: "completion: [final checks]"
```

**Example:**
```bash
[Task Routing Action] Route task to the appropriate specialized subagent. Task: "completion: verify all tests pass, update API docs, security review"
```

### SPARC Coordinator
Spawn SPARC coordinator agent

```bash
npx @claude-flow/cli agent spawn --type sparc-coord --name sparc-lead
```


## Scripts

| Script | Path | Description |
|--------|------|-------------|
| `sparc-init` | `.agents/scripts/sparc-init.sh` | Initialize SPARC workflow for a new feature |
| `sparc-review` | `.agents/scripts/sparc-review.sh` | Run SPARC phase review checklist |


## References

| Document | Path | Description |
|----------|------|-------------|
| `SPARC Overview` | `docs/sparc.md` | Complete SPARC methodology guide |
| `Phase Templates` | `docs/sparc-templates.md` | Templates for each SPARC phase |

## Best Practices
1. Check memory for existing patterns before starting
2. Use hierarchical topology for coordination
3. Store successful patterns after completion
4. Document any new learnings

## ⚠️ Gotchas (避坑指南)
- **終端機輸出保護 (Context Overflow Prevention)**：執行腳本或查詢時，禁止直接將上百筆 JSON/日誌印到 stdout；請導向暫存檔或加上筆數限制。
- **優先使用確定性腳本**：遇到格式轉換、字數統計或合規檢查，優先調用 `scripts/` 下的 Python 工具，不要依賴純語意猜測。
