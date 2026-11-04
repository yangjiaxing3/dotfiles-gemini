---
name: migrate-to-e2e
description: "Use when migrating legacy manual or brittle UI tests to structured E2E verification charters. 舊版測試遷移至結構化E2E驗證"
---

# Migrate a suite to e2e

A migration is never one change. Each session ports one slice, proves it,
and leaves both suites green: the old runner keeps every test it had, and
the new e2e tests pass beside it. A progress file, `MIGRATION.md`, records
what moved, what is left, and why, so the next session, yours or another
agent's, starts from it instead of from scratch. The user decides when an old test goes.

Two references do most of the work. Read them; do not restate them.

- The e2e skill for everything the runner does: `.agents/skills/e2e/SKILL.md`
  once `npx e2e init` or `npx skills add tester-army/e2e` ran, or
  `npx e2e guide <topic>` from the installed package. Topics named below
  (`setup`, `writing-tests`, `agent`, `mcp`, `running`, `debugging`) are its
  reference files.
- The migration guide for the source runner, and the engine page it ports
  to. The guide maps the runner's config, commands, and API to e2e, and
  says what e2e does not have yet (marked `missing` or "No equivalent")
  with today's workaround. Both ship in the installed package under
  `node_modules/e2e/docs/` with the same paths as `.mdx` files.

Detect the source runner, then read both docs in its row in full, before
the inventory and before writing any code. Each later step leans on them.

| Source | Detect it by | Migration guide | Engine |
| --- | --- | --- | --- |
| Playwright | `playwright.config.*`, `@playwright/test` | [migrate/playwright](https://e2e.tester.army/docs/migrate/playwright.md) | [web](https://e2e.tester.army/docs/web.md) |
| Cypress | `cypress.config.*`, a `cypress/` folder | [migrate/cypress](https://e2e.tester.army/docs/migrate/cypress.md) | [web](https://e2e.tester.army/docs/web.md) |
| Selenium | `selenium-webdriver`, Selenium in a `pom.xml`, `build.gradle`, or `requirements.txt` | [migrate/selenium](https://e2e.tester.army/docs/migrate/selenium.md) | [web](https://e2e.tester.army/docs/web.md) |
| Detox | `.detoxrc*`, `detox` in `package.json` | [migrate/detox](https://e2e.tester.army/docs/migrate/detox.md) | [mobile](https://e2e.tester.army/docs/mobile.md) |
| Maestro | YAML flows opening with `appId:` and `---`, `.maestro/`, `maestro test` in a script or workflow | [migrate/maestro](https://e2e.tester.army/docs/migrate/maestro.md) | [mobile](https://e2e.tester.army/docs/mobile.md) |

WebdriverIO and Appium have no guide. Map their WebDriver calls with the
Selenium guide; map Appium's device commands with the Detox and Maestro
guides, on the mobile engine. Tell the user the mapping is partial. A
project with two source runners migrates one at a time, one section of the
progress file each.

## 1. Resume or start

Look for `MIGRATION.md` beside the e2e config, then at the repo root. When
one exists, this is a later session:

1. Read it, then the migration guide and engine page its `Source` line
   names. Its `Next` section names the slice this session takes, unless the
   user names another.
2. Check it against the repo before trusting it: every `ported` test still
   exists in both suites, every source file or test it lists still exists
   (except `retired` ones, deleted on purpose), and no new source file or
   test is missing from it (add those as `todo`). No `Defect check:` line: ask
   as in step 2. A planted bug noted under `Next`: revert it first (step 6).
3. Run the file's `Run new` command once. A ported test that fails now is
   the first thing to fix, before any new slice.
4. Unless the progress file's `Harness:` line says `done`, go to step 3, Build
   the harness. Otherwise go to step 4, Pick the slice.

No progress file means a first session: steps 2 and 3, then the rest.

## 2. Inventory the suite (first session)

Answer these from the repo; ask the user only what you cannot observe.

| Question | Where the answer is | What it decides |
| --- | --- | --- |
| Source runner | The detection table above | The two docs read before this table |
| Tests | Every spec, flow, or test file, with its titles, tags, and per-platform or per-browser branches. Count tests with the runner's own list or dry-run mode, not by grepping, which misses tests made in a loop. `npx playwright test --list` prints a test once for every project that runs it, so count a test listed under several projects once | The progress file's rows, one per source file. Count each file's assertions now so a port can be checked against the count: explicit ones (`expect`, `should`, `assertVisible`), plus, where the runner's steps are its checks (a Maestro `tapOn` fails when its target is missing), those steps |
| Shared code | Page objects, custom commands, subflows (`runFlow: file.yaml`), fixtures, hooks, `globalSetup` | Helpers to port once, before the first test that needs each |
| How it runs | The CI job that runs the suite and the scripts it calls: the build, the services and mock servers it starts, seed and reset calls, env files, devices or browsers, ports | The e2e harness. The CI job is usually the only complete description; read it line by line |
| Where e2e lives | A JavaScript or TypeScript project with a `package.json`: its root (in a monorepo, beside the source runner's config), tests in `tests/**/*.e2e.ts`. A native, Java, or Python project: an `e2e/` folder with its own `package.json` beside the app. Then the source runner's file pattern (`testDir`, `testMatch`, `specPattern`, the flow folder) | The e2e config's location and the progress file's. The two runners must not collect each other's files: when the patterns overlap, narrow one of them. Playwright suites often name files `*.e2e.ts` already, which leaves the directories as the only separation: no e2e test under a Playwright `testDir`, and no Playwright file under e2e's `tests` glob. Compare `npx playwright test --list` with `npx e2e list` |
| Can the old suite run here | The source runner installed, the build it needs, the services | Whether parity is checked against a live old run (step 6) or only against the source text |

Write `MIGRATION.md` now (format in step 8), every source file `todo`.

Ask whether each slice should also run against a planted defect (step 6)
and record the answer as `Defect check: on` or `off`.

## 3. Build the harness (once)

The harness is the config, the app launch, and one green test. It is done
once and the progress file says so; later sessions skip this step.

1. No e2e config: `npx e2e init --yes` (topic `setup`), with `--engine mobile`
   on a device project. Delete or rewrite the example test. One target per
   platform or browser the source suite covers.
2. Ask the user which model agent steps use, and configure it (topic
   `agent`). A literal port needs none: every test can be deterministic, and
   a config without a model runs those.
3. Port the orchestration the CI job does, reusing the repo's own scripts
   rather than writing new ones:
   - The one process that serves the app (a dev server, Metro for an Expo dev
     client) becomes the target's `app.command` with `readyUrl` (topic
     `setup`). The command gets only `PATH`, `HOME`, the temp-directory
     variables, and `command.env`, not the shell's environment, so pass
     what the server read from the old runner's environment in
     `command.env`.
   - e2e has no `services` key. Databases, queues, and mock servers start
     before the run with the command the CI job uses, or `app.command` runs
     a script that brings them up and then serves the app. Name the command
     in the progress file.
   - A reset or seed the source ran per test (`runScript` with `http.post`,
     `cy.task('db:reset')`, an API call in `beforeEach`) becomes `fetch` in a
     `beforeEach` or a fixture, so each test still starts from known data.
   - A seed helper that imports the app's own code (an ORM factory, a
     server module) is reused, not rewritten. The old runner may have
     compiled it to CommonJS; e2e loads every `.ts` file as an ES module.
     Importing it into a test can then fail with `__dirname is not
     defined`, with "does not provide an export named" for a CommonJS
     package, or with `ERR_UNSUPPORTED_DIR_IMPORT`. When it does, run the
     helper unchanged in a child process with the repo's own TypeScript
     runner (`ts-node`, `tsx`) and call it from a fixture. Do not edit the
     app's modules to make them load.
   - Env values become module constants; passwords and tokens go under
     `credentials` or `secrets` (topic `setup`). When the old config loaded
     an env file (`dotenv.config()`), load it the same way in the e2e
     config, so tests and helpers see the same values. `app.command` does
     not see them; pass the ones the server needs in `command.env`.
4. Port the simplest source test, often the sign-in or the launch, as the
   smoke test. It must pass on every target before any other port. When it
   cannot, the harness is wrong, not the test: fix the harness.
5. `init` adds a `test:e2e` script (`e2e run`) unless a script already has
   that name. When the name was taken, or `init` did not run, add one under
   a free name. Keep the old suite's scripts as they were.
6. Mark the harness done in the progress file, with the commands that start the
   dependencies, run the old suite, and run the new one.


## Progressive Disclosure References (On-Demand)
- Detailed templates, extended examples, and deep-dive checklists have been moved to [references/detailed-guide.md](./references/detailed-guide.md) to keep context lean. Load that file via `view_file` only when needed.

## ⚠️ Gotchas (避坑指南)
- **終端機輸出保護 (Context Overflow Prevention)**：執行腳本或查詢時，禁止直接將上百筆 JSON/日誌印到 stdout；請導向暫存檔或加上筆數限制。
- **優先使用確定性腳本**：遇到格式轉換、字數統計或合規檢查，優先調用 `scripts/` 下的 Python 工具，不要依賴純語意猜測。
