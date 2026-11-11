---
name: dispatching-parallel-agents
description: "Use when splitting independent tasks across parallel Manager-Worker subagents to accelerate execution. 並行子代理分發與Manager-Worker協作"
---

# Dispatching Parallel Agents (Manager-Worker Pattern — Ruflo Swarm V3)

This skill enables the Agent to act as a "Manager" (`gemini-4-carbon`) that decomposes complex tasks into independent sub-tasks, and dispatches them to specialized "Worker Agents" via **Ruflo Swarm V3** for parallel execution.

## When to Use
- **Complex Multi-Component Tasks**: When a user request involves multiple distinct modules (e.g., "Fix the FastAPI backend endpoint AND redesign the React dashboard tab").
- **Independent Operations**: When sub-tasks do not strictly depend on each other's sequential file writes.
- **Efficiency**: To speed up execution by parallelizing work across orthogonal 2026 frontier models.

## Workflow

### 1. Analysis & Decomposition (The Manager — `gemini-4-carbon`)
- **Input**: User request + `graphify` dependency check.
- **Action**: Verify zero file-write collisions and decompose into independent `Task` objects:

```typescript
interface Task {
  id: string;
  description: string;
  context: string; // Specific file paths, AST nodes, and API contracts
  type: "frontend" | "backend" | "data_analysis" | "testing";
}
```

### 2. Intelligent Ruflo Swarm V3 Dispatching (The Workers)
- `type: "frontend"` -> **UI/UX & React/TS Task**
  - **Command**: `npx ruflo@latest agent spawn -t coder --model gemini-4-carbon` (for visual UI/UX & multimodal layout) or `--model qwen-3.8-max` (for complex React/TypeScript state refactoring)
- `type: "backend"` -> **Logic/CRUD & FastAPI/Turso Task**
  - **Command**: `npx ruflo@latest agent spawn -t coder --model DeepSeek-V4.1-Flash` (fast scoped logic) or `--model qwen-3.8-max` (cross-module schema & lifecycle refactoring)
- `type: "data_analysis"` -> **Architecture, Graph & Deep Reasoning Task**
  - **Command**: `npx ruflo@latest agent spawn -t analyst --model gemini-4-carbon` (with `DeepSeek-V4.1-Flash` CoT & TypeSafe `jev-1.13.0` calibration)
- `type: "testing"` -> **TDD & Adversarial Red-Team Review Task**
  - **Command**: `npx ruflo@latest agent spawn -t qa --model DeepSeek-V4.1-Flash` (for writing unit/integration tests) and `--model grok-4.7` (for adversarial edge-case & security auditing)

### 3. Aggregation, Verification & Escalation
- **Action**: Collect outputs from all parallel workers and verify API contracts (`tsc --noEmit`, `pytest`).
- **Error Escalation (Fixer Protocol)**: If any worker fails 2 times in a row on the same error, immediately halt that worker and escalate to **`qwen-3.8-max`** (`fixer-prompt`).

## Example Prompt for Manager Agent

```markdown
You are the Manager Agent (`gemini-4-carbon`). The user wants to: "Refactor the login API to return JWT and update the React login form to store it."

**Plan:**
1. **Backend Task**: Modify `api/auth.py` to issue JWTs. (Type: backend)
2. **Frontend Task**: Modify `components/LoginForm.tsx` to handle JWT storage. (Type: frontend)

**Execution (Ruflo Swarm V3 Dispatch):**
- `npx ruflo@latest agent spawn -t coder --model DeepSeek-V4.1-Flash -p "Modify api/auth.py..."`
- `npx ruflo@latest agent spawn -t coder --model qwen-3.8-max -p "Modify LoginForm.tsx..."`
- `npx ruflo@latest agent spawn -t qa --model grok-4.7 -p "Audit JWT security and edge cases..."`
```

## ⚠️ Gotchas (避坑指南)
- **防止並行寫入衝突 (File Lock Collision)**：並行派發的多個 Worker 絕對不可同時修改同一個檔案；共用型別或契約必須由 Manager 先行定案。
- **終端機輸出保護 (Context Overflow Prevention)**：執行腳本或查詢時，禁止直接將上百筆 JSON/日誌印到 stdout；請導向暫存檔或加上筆數限制。
