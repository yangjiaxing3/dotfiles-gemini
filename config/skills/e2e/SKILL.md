---
name: e2e
description: "Use when running end-to-end Playwright browser verification across user journeys and visual states. 端到端E2E瀏覽器驗證與回歸測試"
---

> **Grok Bot 使用守則（本地加註，非上游內容）**：預設唯讀，沿用使用者的 `e2e-web-test` 規則：電腦版＋手機版兩種 viewport、只開頁／讀取／截圖／斷言；不送出任何表單、不建立／刪除／付款／出貨；不執行 `npx e2e feedback`；除非使用者明確逐次要求，不跑 bug bash、不錄影、不把畫面或錄影傳給第三方。
>
> **⚡ 輕量級結構化 E2E 與原生桌面分流守則 (`agent-browser` / `agent-desktop`)**：
> - **何時用本 `e2e` 套件**：專案已配置 `e2e.config.ts`、需要寫入持久化回歸測試檔 (`tests/*.e2e.ts`)、或需要執行多角色 `e2e explore` / `bug-bash`。
> - **何時改用 `agent-browser`（Web 端）**：在 `/multi-agent-mode` 或 `/subagent-driven-development` 開發迴圈中，僅需快速確認單次 UI 變更、檢查按鈕/徽章/文字狀態、或多 Agent 結構對比時，優先執行 `agent-browser open <url> && agent-browser snapshot -i > temp_snap.txt` 取得 `@ref` 無障礙結構樹，避免每次手寫完整測試腳本或連續截圖消耗 Token。
> - **何時改用 `agent-desktop`（Windows 原生桌面端）**：當目標是原生桌面應用（如 Flutter Windows 桌面版、AutoCAD、SketchUp、系統對話框），`e2e` 無原生桌面引擎，請直接使用 `agent-desktop snapshot --app <name>` 與 `agent-desktop click @ref`（詳見 `agent-desktop` 技能）。


# e2e: agentic end-to-end tests

e2e runs UI tests that mix agent goals with exact steps. `agent.act` drives
one goal; `agent.assert`, `agent.waitFor`, and `agent.extract` judge the
screen; `screen`, `app`, `browser`, and `expect` act and check exactly. UI
targets use `@e2e-dev/web` for browsers or `@e2e-dev/mobile` for iOS
simulators, Android emulators, and connected phones.

## Start here: pick the reference for the job

Read the one reference that matches the request before doing anything else.
Each stands on its own; a reference names another topic only for a side
trip. `npx e2e guide <topic>` prints the installed package's version of a
reference; prefer it when it differs from this copy.
The Rules and Feedback sections below still apply.

| When you are | Topic | Read |
| --- | --- | --- |
| Adding e2e to a project, writing `e2e.config.ts`, starting the app from the config, signing in to a model, setting up mobile targets | `setup` | [references/setup.md](references/setup.md) |
| Looking at the running app, checking a UI change, taking a screenshot or video, or trying a locator before writing it, over `e2e mcp` | `mcp` | [references/mcp.md](references/mcp.md) |
| Writing or fixing a test: fixtures, locators, actions, matchers, sign-in sessions, the `browser` fixture, API-only tests | `writing-tests` | [references/writing-tests.md](references/writing-tests.md) |
| Adding `agent.*` steps, picking a model, cutting cost, budgets, the replay cache | `agent` | [references/agent.md](references/agent.md) |
| Running tests: CLI flags, CI, reporters, trace pages, `report.json` for scripts, exit codes | `running` | [references/running.md](references/running.md) |
| Handling a failed run: error codes and their fixes, `--headed`, `--debug`, `--ai-trace` | `debugging` | [references/debugging.md](references/debugging.md) |
| Exploring an app toward a goal without a test file: `e2e explore`, its budgets and verdict | `explore` | [references/explore.md](references/explore.md) |
| Asked to bug bash, QA, or hunt for bugs across an app or a branch | `bug-bash` | [references/bug-bash.md](references/bug-bash.md) |

For anything the references do not cover, the full documentation ships in
the `docs/` directory of the installed `e2e` package
(`node_modules/e2e/docs` in a single-package project); a link such as
`/reference/cli` is `docs/reference/cli.mdx`. Complete projects for Vite,
Next.js, Astro, Expo, SwiftUI, Jetpack Compose, Kotlin Multiplatform,
Flutter, and .NET MAUI are in https://github.com/tester-army/e2e/tree/main/examples.

## Quick start

A config with one web target and a model, and a test that drives one goal
and pins the outcome:

```ts
// e2e.config.ts
import type { E2EConfig } from 'e2e';
import { web } from '@e2e-dev/web';
import { gateway } from 'ai';

export default {
  targets: [
    {
      engine: web(),
      app: {
        url: 'http://127.0.0.1:3000',
        command: { executable: 'pnpm', args: ['dev'], log: '.e2e/logs/app.log' },
      },
    },
  ],
  // The model behind every agent.* step: an AI SDK instance; gateway() from 'ai' reads AI_GATEWAY_API_KEY or a Vercel OIDC token.
  agents: {
    default: {
      model: gateway('openai/gpt-6-luna-fast'),
      system: 'You are a thorough QA agent. Verify every outcome on screen.',
    },
  },
} satisfies E2EConfig;
```

```ts
// tests/billing.e2e.ts
import { test } from '@e2e-dev/web';
import { expect } from 'e2e';

test('a member upgrades to Pro', async ({ app, agent, screen, browser }) => {
  await app.open('/settings/billing');
  await agent.act('upgrade the workspace to the Pro plan');
  await expect(screen.getByRole('status')).toContainText('Pro');
  await expect(browser).toHaveURL('/settings/billing');
});
```

## Workflow: writing a test

1. Look at what exists: `e2e.config.ts` or `e2e.config.mts`, the `tests` glob
   (default `tests/**/*.e2e.ts`), `e2e` in `package.json`. Nothing there:
   follow `setup` when the user has requested e2e (see Rules).
2. Learn the screens before writing a test: routes, labels, roles, button
   text. Semantic locators need the accessible names the app renders, so read
   the components, open the page with `--headed`, or drive the live app over
   a connected `e2e mcp` server (topic `mcp`): `open_session`, `observe`,
   and `locate` show exact names and check a locator before you write it.
3. Write `tests/<feature>.e2e.ts`. Drive the flow with `agent.act`, one
   atomic goal per call, and pin each outcome right after with `expect` or
   `agent.assert`. A test with three goals makes three calls.
   Exact values go through `screen`: a sign-in form in a setup test, a field
   that must receive one specific string, a count that must be one number.
4. Run one file: `npx e2e run tests/<feature>.e2e.ts`. Agent steps need a
   model in the config and that provider's authentication (a saved
   subscription login, an API key); a local endpoint may need none. Tests
   without agent steps need no model.
5. Read the trace page the terminal names under each failed test
   (`.e2e/results/<test>/trace.md`): every step with what it did, the cache's
   decision, what the app logged, the agent's turns, and the screen at
   failure. Fix the locator, the expectation, or the app. Never add a sleep.

## Rules

- In a project without e2e, set it up when the user requests it. Otherwise
  ask before adding a test framework, and name any existing framework.
- Live MCP tools need the project's own `e2e mcp` server registered in the
  client (topic `mcp`); writing and running tests use the CLI directly.
- Run the CLI as `npx e2e ...` (or `pnpm exec e2e ...`).
- The config is `export default { ... } satisfies E2EConfig` with
  `import type { E2EConfig } from 'e2e'`. `targets` is required; a UI target
  names an engine and declares the app beside it: `{ engine: web(), app: { url, command } }`.
  A tools-only target can omit the engine and set `platform`.
- Import `test`, `describe`, the hooks, `expect`, `credentials`, and
  `secrets` from `e2e`. A test that uses the `browser` fixture imports `test`,
  `describe`, and the hooks from `@e2e-dev/web`: the same runtime functions,
  typed with `browser`.
- Config and tests are ES modules whatever `package.json` sets as `type`.
- Locators resolve when used. Actions wait for readiness and `expect` retries
  assertions. Reads such as `textContent()` wait for one match until the
  action timeout, then answer the current value; `count()` and `isVisible()`
  answer from the current screen. Nothing waits for a value to change, so use
  a matcher when a value has to settle.
- A locator that matches two nodes fails with `LOCATOR_AMBIGUOUS`; narrow it
  (topic `writing-tests`).
- Secrets never appear in test code. Declare accounts under `credentials` and
  every other sensitive value under `secrets` in the config; resolve with
  `credentials.user(name).password` or `secrets.get(name)` (separate
  namespaces: `secrets.get` never returns a password), and hand the opaque
  `Secret` only to `fill()` or `agent.act` params.
- Agent instructions: one goal per `act`, the wording on screen, real values
  in params. A goal is atomic: one outcome that one check confirms. Two
  outcomes worth checking are two goals, so split them into two `act` calls
  (topic `agent`). Bad: `'add a todo and mark it done'`. Good: `'add a
  todo'`, check, then `'mark the todo as done'`, check. Judge meaning, not
  phrasing: `toContain('Pro')`, not an exact sentence a model produced.
- Check each agent goal's outcome. A passing `act` with a recorded check can
  be cached and replayed without model calls (topic `agent`).
- Shape the agent for this app: `context` for vocabulary the screens use,
  `system` for how it works, tools for a test API, named personas under
  `agents`. When a step fails, tighten the goal first, then the context, then
  the agent.
- `.e2e/` is output (`report.json`, `results/`, `cache/`, `logs/`; the
  config's `output` moves the report and artifacts, never `cache/` or the
  app's log). Read it, never edit it.

## Feedback

When e2e itself gets in your way, offer to tell the e2e team: a command or
API that broke (`bug`), docs or this skill that misled you (`docs`), or a
capability you needed and did not find (`feature`). Once per problem, after
you worked around it or gave up. Never report:

- failures of the app under test, or its own behavior;
- a problem you saw once and could not see again;
- anything on an outdated e2e: the command refuses it, so upgrade and check
  the problem still happens first.

Search [existing issues](https://github.com/tester-army/e2e/issues) first
(`gh issue list -R tester-army/e2e --search "<words>"`); comment on a match
instead of sending a new report.

A `bug` needs `--repro`, steps that reproduce it every time without app
content. Without such steps, or when the bug needs your app to show, omit
`--repro`: the command then prints a prefilled GitHub issue and sends
nothing; show the user the link and tell them to add a minimal reproduction
and submit it. Never file the issue yourself.

Run it with `--dry-run` first, show the user what would be sent, and send
it only when they agree.

```bash
npx e2e feedback --type bug -m "<one or two sentences>" \
  --repro "<steps that reproduce it every time>" --error-code LOCATOR_AMBIGUOUS \
  --task "<what you were doing>" --expected "<...>" --actual "<error message>" \
  --approach "<what you tried>" --command "<e2e command>" --agent "<agent / model>"
```

Describe e2e's behavior only, briefly: never paste app content, page text,
test files, URLs of private apps, or credentials. Secret-named environment
variables and common token shapes are redacted, but do not rely on it. After
sending, give the user the reference id it prints.

## ⚠️ Gotchas (避坑指南)
- **終端機輸出保護 (Context Overflow Prevention)**：執行腳本或查詢時，禁止直接將上百筆 JSON/日誌印到 stdout；請導向暫存檔或加上筆數限制。
- **優先使用確定性腳本**：遇到格式轉換、字數統計或合規檢查，優先調用 `scripts/` 下的 Python 工具，不要依賴純語意猜測。
