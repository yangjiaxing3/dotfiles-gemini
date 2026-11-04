# migrate-to-e2e — Detailed Reference & Extended Examples

## 4. Pick the slice

A slice is what this session can finish green: one file, one folder, one
tag, or one feature area, usually one to five tests. Ask the user which.
When they leave it to you, suggest in this order:

1. Tests whose shared helpers are already ported.
2. Tests that break often in the old runner: retries, flaky history in CI,
   comments explaining a workaround for the runner. They gain the most.
3. Tests that need a capability the guide marks `missing` or "No
   equivalent", last.

Write the slice into the progress file's `Next` section before starting, so an
interrupted session leaves a trail.

## 5. Port the slice

Port the slice's shared helpers first, once, as plain `.ts` files (not
`.e2e.ts`, so the runner does not collect them), for example under
`tests/support/`. A subflow
becomes a function or a `test.extend` fixture; a page object becomes a
fixture (topic `writing-tests`). Record each in the progress file.

Then each test, one at a time:

- Keep its title, and open the file with a comment naming the source
  (`// Ported from __e2e__/flows/login.yml`), so reports and reviewers map
  one to the other.
- Translate literally first with the guide's tables, one awaited call per
  source step. Each source assertion maps to its own e2e assertion. A wait
  that fails on timeout (`waitForFunction`) becomes one more, so the e2e
  count is at least the inventory's.
- A test the source skips is ported in full and stays skipped, with the
  source's reason, so it can be turned back on in either suite. Its row
  says so; when the reason allows, run it unskipped once and note the
  result.
- Learn exact names before writing a locator: `e2e mcp` with `open_session`,
  `observe`, and `locate` (topic `mcp`). When your client has no `e2e` MCP
  tools, run the test and read the screen listed on its trace page
  (topic `debugging`); do not build a bridge. The guide's notes on
  selectors list the edits most ports need: e2e matches whole strings and
  fails on several matches where the old runner took the first. When a
  query also matches a hidden copy (another layout's), add
  `{ visible: true }`. When two visible nodes match, such as a second
  toast over the first, pick the one the step means.
- A sleep or fixed wait becomes an assertion on the state it waited for.
- A per-platform branch becomes `{ platforms: [...] }` on a test, or an `if`
  on the `platform` fixture inside one.
- A workaround the source comments explain (a flaky `hideKeyboard`, a
  coordinate tap, a retry loop around a picker) is a workaround for the old
  runner. Try the plain step first; keep a workaround only when e2e needs it
  too, with its own comment saying why.
- Where the guide marks a step `missing` or "No equivalent", use its
  workaround. When there is none, the test stays in the old runner: mark it
  `stays` with the reason and offer to send
  `npx e2e feedback --type feature -m "<the gap>"` once: preview it with
  `--dry-run` and send it only when the user agrees (the e2e skill,
  Feedback).
- Do not change app code. A test that needs a test id the app lacks gets
  `agent.act` or a different locator; propose the app change to the user
  instead of making it. A defect check's planted bug (step 6) is
  the exception, reverted the same session.

`agent.act` comes after the literal port passes, never instead of it, and
only with a model configured. Propose it for a stretch the source kept
patching: coordinate taps, picker spins, long tap sequences through a
wizard. Pin the outcome right after with a locator assertion (topic `agent`).

## 6. Prove each port

A port is done when it is as strict as the source and passes every time.

1. Run it on every target the source covered:
   `npx e2e run <file> --repeat-each 3`, plus `--no-cache` when it has agent
   steps. Three of three on each target, or it is not done (topic
   `running`).
2. When the old suite can run here, run the source test on the same build.
   A failure both runners show is an app or environment bug: report it, do
   not port around it. A failure only e2e shows is the port's.
3. Check strictness against the source: an e2e assertion for every source
   assertion, so the count is at least the inventory's, and every end
   state the source checked is checked. Never
   weaken an assertion, widen a timeout without a reason, or drop a step to
   go green. A test that cannot pass honestly stays `blocked` with what
   failed.
4. Read the trace page of any failure before changing the test
   (topic `debugging`).

### Defect check (optional)

With `Defect check: on`, show both suites fail on the same bug:

1. With the user's agreement, plant a small bug in an end state the source
   asserts (a checkout showing the wrong total), in a file with no
   uncommitted changes. Note the file under `Next` until it is reverted.
2. Rebuild, confirm the app shows the bug, then run `Run old` on the slice
   (when it runs here) and `npx e2e run <files> --no-cache`.
3. Revert only that file (`git checkout -- <file>`), rebuild, and confirm
   `git diff -- <file>` is empty.
4. Both fail at the step that checks the planted state: record it. Only
   the old suite passes: record that the source was weaker. Only e2e
   passes: the port lost an assertion, so it is not done. Neither fails:
   pick another bug. A failure before that step is not a catch.
5. Fill the row's `Defect check` cell, for example `total +1: both fail`,
   or `old not run` when the old suite cannot run here.

## 7. Run both suites

Until the user retires a source test, both runners keep it.

- Ported tests stay in the old suite too. Delete a source test only when the
  user confirms, then mark it `retired`. Once neither a remaining source
  test nor e2e code uses a source helper, propose deleting it, and delete
  it when the user confirms.
- CI: propose adding the e2e suite beside the old job once a few ports are
  green, and make the change only when the user agrees, since it edits the
  old runner's workflow. Reuse its build, services, and devices. Two
  runners never drive one device or simulator at the same time; run them one after the other in the same job, or give each its own
  device. The e2e job runs every ported test, so a later change that breaks
  one fails the pull request (topic `running`, Continuous integration).
- When the last source test is retired or marked `stays`, the progress file says
  the migration is complete and which tests, if any, stay behind.

## 8. Keep the progress file

`MIGRATION.md`, beside the e2e config, is the migration's state. Update it
as you go, not at the end; an interrupted session must leave it true.

```md
# Migration to e2e

Source: Maestro, `__e2e__/flows/**` (guide: https://e2e.tester.army/docs/migrate/maestro.md, engine: https://e2e.tester.army/docs/mobile.md)
e2e: `e2e.config.ts`, tests `tests/**/*.e2e.ts`
Start dependencies: `pnpm e2e:mock-server`
Run old: `maestro test __e2e__`
Run new: `npx e2e run`
Harness: done, smoke `tests/login.e2e.ts` on ios and android
Defect check: on

| Source | e2e | Status | Assertions (source → e2e) | Passing | Defect check | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| flows/login.yml | tests/login.e2e.ts | ported | 3 → 3 | ios 3/3, android 3/3 | wrong screen: both fail | |
| flows/create-account.yml | | blocked | 6 → | | | date picker spin fails on android, trace in .e2e/results |
| flows/search-screen.yml | | todo | 4 → | | | |

## Shared helpers

| Source | e2e | Used by |
| --- | --- | --- |
| setupApp.yml | tests/support/app.ts `openSignedOut()` | login, create-account |

## Gaps

- `addMedia` has no e2e equivalent (guide: missing); feedback sent.

## Next

flows/composer.yml and flows/composer-self-label.yml (both need `signInAlice()`).
```

One row per source file. A file whose tests end in different statuses
gets one row per test, each with its own assertion count. A suite with
hundreds of tests keeps file rows: the table is read at the start of
every session.

Statuses: `todo`; `ported` (green in e2e, the source test still runs);
`retired` (the user confirmed, the source test is deleted); `blocked`
(tried, does not pass yet, with what failed); `stays` (stays in the old
runner on purpose, with why).

## 9. Hand over

Tell the user what this session moved and what it proved: the tests ported
and their pass counts per target, defect check results, the helpers ported,
what is blocked or stays and why, the gaps reported, and the next slice.
Ask which `ported` source tests may be retired. List every file you created or changed.

## Rules

- One slice per session. Leave both suites green: the old suite passes as it
  did, and every `ported` test passes.
- Never delete or edit a source test, helper, or the old runner's config
  without the user's confirmation.
- Port from what the repo shows. Run every command you put in the
  progress file at least once; one that cannot run here (the old runner not installed) says
  so in the progress file.
- A source step whose meaning is unclear, such as a tap on a disabled
  control or a coordinate tap that may miss, keeps its intent in the port.
  Note your reading in the progress file and ask the user.
- One sentence from the e2e skill or the guide beats a paragraph of your
  own. Name the topic or the guide's section.
- Never put a secret in a test, the config, or the progress file. Name the
  credential (topic `setup`).
- Do not commit on the user's behalf.
