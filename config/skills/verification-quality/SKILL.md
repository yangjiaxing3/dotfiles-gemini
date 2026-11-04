---
name: verification-quality
description: "Use when running automated truth-scoring, post-implementation quality gates, and rollback checks. 交付品質驗證與自動回滾門禁"
version: "2.0.0"
---

# Verification & Quality Assurance Skill

## What This Skill Does

This skill provides a comprehensive verification and quality assurance system that ensures code quality and correctness through:

- **Truth Scoring**: Real-time reliability metrics (0.0-1.0 scale) for code, agents, and tasks
- **Verification Checks**: Automated code correctness, security, and best practices validation
- **Automatic Rollback**: Instant reversion of changes that fail verification (default threshold: 0.95)
- **Quality Metrics**: Statistical analysis with trends, confidence intervals, and improvement tracking
- **CI/CD Integration**: Export capabilities for continuous integration pipelines
- **Real-time Monitoring**: Live dashboards and watch modes for ongoing verification

> **Shipped vs. aspirational.** The *concrete, in-CI* verification stack — the 6 regression-guard jobs + the witness manifest + the tool-discoverability audit — is real and runs on every push. The truth-scoring / auto-rollback / WebSocket-dashboard surface described later in this doc is partly shipped (`ruflo verify` runs the witness checks) and partly design — treat the "CI Guards" section below as the authoritative current state.

## CI Guards — what's actually shipped (current state)

Ruflo's regression protection is three layers, all gated before publish. Authoritative reference: [`verification/README.md`](../../../verification/README.md).

| Layer | What | CI job(s) in `.github/workflows/v3-ci.yml` | ADR |
|---|---|---|---|
| **1 — install/behavioral smoke** | Exercise user-visible failure modes against a real build | `smoke-install-no-bsqlite` (npm install on platforms w/o prebuilds), `plugin-hooks-smoke` (#1859/#1862 — hook flag parsing), `mcp-protocol-smoke` (#1874 — HTTP MCP wire format), `memory-import-smoke` (#1883/#1884 — WSL path + key sanitization), `mcp-roundtrip-smoke` (#1889 paired-tool round-trip + #1863 cli-no-crash + ADR-095 G2 consensus-transport) | ADR-102 |
| **1 — discoverability gate** | Every MCP tool description must answer "use this over native when?" | `tool-descriptions-audit` — `scripts/audit-tool-descriptions.mjs`, baseline at `verification/mcp-tool-baseline.json` (monotone-decreasing: noGuidance / tooShort / duplicates) | ADR-112 |
| **2 — cryptographic witness** | Every documented fix's load-bearing marker must still be present in dist; Ed25519-signed, per-OS bundles | `witness-verify` (ubuntu/macos/windows) — `plugins/ruflo-core/scripts/witness/verify.mjs` against `verification/<os>/manifest.md.json` | ADR-103 |
| **3 — temporal history** | When was a regression introduced | `verification/<os>/history.jsonl` + `history.mjs` (`summary` / `regressions` / `timeline`) | ADR-103 |

### Run the guards locally

```bash
# Tool-description discoverability audit (ADR-112)
node scripts/audit-tool-descriptions.mjs                       # fails if any baseline count rises
node scripts/audit-tool-descriptions.mjs --update-baseline     # lock the new floor after a fix lands

# Behavioral smokes (each builds what it needs; safe to run individually)
node plugins/ruflo-core/scripts/test-hooks.mjs "node $PWD/v3/@claude-flow/cli/bin/cli.js"
node plugins/ruflo-core/scripts/test-mcp-protocol.mjs
node plugins/ruflo-core/scripts/test-memory-import.mjs
node plugins/ruflo-core/scripts/test-mcp-roundtrips.mjs        # #1889 paired-tool round-trip
node plugins/ruflo-core/scripts/test-cli-no-crash.mjs          # #1863 unhandled-exception class
node plugins/ruflo-core/scripts/test-consensus-transport.mjs   # ADR-095 G2 consensus transport

# Witness manifest — regenerate + verify
node scripts/regen-witness.mjs
node plugins/ruflo-core/scripts/witness/verify.mjs --manifest verification/macos/manifest.md.json

# Temporal history
node plugins/ruflo-core/scripts/witness/history.mjs --history verification/macos/history.jsonl summary
node plugins/ruflo-core/scripts/witness/history.mjs --history verification/macos/history.jsonl regressions
```

### Adding a new guard

1. **Behavioral smoke** → write `plugins/ruflo-core/scripts/test-<name>.mjs`. Pattern: static dist-scan first (fast, always completes), behavioral probe second with an internal timeout + a process-level watchdog so CI never hangs. Add a step to the relevant job in `v3-ci.yml`.
2. **Static gate with a baseline** → write `scripts/audit-<name>.mjs` that scans, counts violations, and fails if the count exceeds a monotone-decreasing baseline in `verification/<name>-baseline.json`. Support `--update-baseline`. Add a CI job; wire it into `witness-verify` `needs[]` if it should gate `publish`.
3. **Documented-fix marker** → append `{ id, desc, file, marker }` to `verification/witness-fixes.json`, run `node scripts/regen-witness.mjs`. The marker must be a substring the fix specifically creates (not a generic pattern like `'function'`).

## Prerequisites

- Ruflo installed (`npx ruflo@alpha`)
- Git repository (for rollback features)
- Node.js 18+ (for dashboard features)
- `@noble/ed25519` (for the witness verifier — a single runtime dep, `npm i @noble/ed25519`)

## Quick Start

```bash
# View current truth scores
npx ruflo@alpha truth

# Run verification check
npx ruflo@alpha verify check

# Verify specific file with custom threshold
npx ruflo@alpha verify check --file src$app.js --threshold 0.98

# Rollback last failed verification
npx ruflo@alpha verify rollback --last-good
```

---

## Complete Guide

### Truth Scoring System

#### View Truth Metrics

Display comprehensive quality and reliability metrics for your codebase and agent tasks.

**Basic Usage:**
```bash
# View current truth scores (default: table format)
npx ruflo@alpha truth

# View scores for specific time period
npx ruflo@alpha truth --period 7d

# View scores for specific agent
npx ruflo@alpha truth --agent coder --period 24h

# Find files$tasks below threshold
npx ruflo@alpha truth --threshold 0.8
```

**Output Formats:**
```bash
# Table format (default)
npx ruflo@alpha truth --format table

# JSON for programmatic access
npx ruflo@alpha truth --format json

# CSV for spreadsheet analysis
npx ruflo@alpha truth --format csv

# HTML report with visualizations
npx ruflo@alpha truth --format html --export report.html
```

**Real-time Monitoring:**
```bash
# Watch mode with live updates
npx ruflo@alpha truth --watch

# Export metrics automatically
npx ruflo@alpha truth --export .claude-flow$metrics$truth-$(date +%Y%m%d).json
```

#### Truth Score Dashboard

Example dashboard output:
```
📊 Truth Metrics Dashboard
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Overall Truth Score: 0.947 ✅
Trend: ↗️ +2.3% (7d)

Top Performers:
  verification-agent   0.982 ⭐

## Progressive Disclosure References (On-Demand)
- Detailed templates, extended examples, and deep-dive checklists have been moved to [references/detailed-guide.md](./references/detailed-guide.md) to keep context lean. Load that file via `view_file` only when needed.

## ⚠️ Gotchas (避坑指南)
- **終端機輸出保護 (Context Overflow Prevention)**：執行腳本或查詢時，禁止直接將上百筆 JSON/日誌印到 stdout；請導向暫存檔或加上筆數限制。
- **優先使用確定性腳本**：遇到格式轉換、字數統計或合規檢查，優先調用 `scripts/` 下的 Python 工具，不要依賴純語意猜測。
