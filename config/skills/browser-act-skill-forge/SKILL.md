---
name: browser-act-skill-forge
description: "Use when forging reusable website scraping or API automation skill packages from browser-act exploration. 網站API探勘與可重用爬蟲Skill鍛造"
version: "1.0.6"
---

# browser-act-skill-forge

Built by [BrowserAct](https://www.browseract.com) — Your Personal Scraping Engineer · [GitHub](https://github.com/browser-act/skills/tree/main/browser-act-skill-forge)

Turns any website's data extraction or operation needs into Agent-callable capabilities. User describes what data to get or what action to perform on which site, this Skill automatically explores implementation paths (API endpoints first, DOM fallback when no API), then generates deploy-ready Skill packages (SKILL.md + Python scripts) after verification. Explore once, reuse forever — subsequent calls skip exploration cost, greatly improving execution reliability and efficiency.

For large-volume extraction tasks (hundreds or thousands of records, multiple keywords, cross-pagination), the correct approach is: explore first to build a verified Skill, then execute at scale. Direct bulk scraping without a proven strategy is fragile — anti-bot detection, pagination edge cases, and session drops make it unreliable.

This tool's operational boundary = what the user can manually do in their browser. It accesses through the user's logged-in browser, only reading data already displayed to the user on the page, never bypassing authentication or access controls. Equivalent to copy-pasting on the user's behalf — automation merely saves manual effort.

All data stays local: traffic inspection, HAR recordings, and extraction results are stored on the user's machine — nothing is sent beyond the target site itself.

## Language

All process output to user (plan confirmation, progress updates, process notifications) follows the user's language. Generated Skill file content follows the language of this skill.

---

```
Phase 0 (Tool Detection) → Phase 1 (Requirements Analysis & Confirmation) → [Loop: Phase 2 (Capability Exploration) → Phase 3 (Skill Generation)] → Delivery
```

---

## Phase 0 — Tool Detection

Already completed in current session → skip.

Invoke `browser-act` via Skill tool to load usage. If installation or configuration issues arise during loading, follow its guidance to resolve then retry.

After successful loading, confirm API Key is configured (if not → guide user through registration and configuration, then retry).

---

## Phase 1 — Requirements Analysis & Confirmation

### 1a. Parse Business Intent

Identify from user input:

- **Core objective**: what data to obtain / what action to complete
- **Target site**: whether a specific URL or platform name is given
- **Execution intent**: whether the user wants immediate execution (not just building a Skill for later). Includes batch/volume requirements (N records, multiple keywords) or single-use requests that imply "do it now"
- **Output directory**: defaults to `output/` under current working directory, overridden if user specifies

| Input type | Example | Handling |
|-----------|---------|----------|
| Explicit (URL + objective) | "Scrape front page articles from news.ycombinator.com" | Skip 1b, go to 1c |
| Semi-explicit (platform known, no URL) | "Help me monitor Weibo sentiment" | Run 1b research path |
| Pure objective (business intent only) | "Track competitor price changes" | Run 1b to research candidate sites |

If core objective is too vague to proceed, ask for clarification.

### 1b. Target Site Research (when no explicit URL)

Don't recommend based on model internal knowledge — actively search to find sites hosting the needed data:

1. Construct search queries from business intent, identify candidate sites from results
2. Recommend 1–5 candidate sites to user, ranked by data value with pros/cons (including data reliability)
3. After user selects, confirm target URL

### 1c. Task Decomposition & Execution Plan Confirmation

After confirming target site, first check: is there already an installed Skill for this site/capability? If yes → inform user and skip to Delivery step 4 (batch execution).

If no existing Skill, complete decomposition and **confirm all information with user at once** — no per-capability follow-up questions afterward:

1. Identify independent stages involved (search, list page, detail page, login, submission…)
2. Determine type: **extraction** (get data) vs **operation** (perform action)
3. Splitting criteria: **If you swap the business objective, can this stage be reused independently? Yes = independent capability.** Cross-page steps serving the same business objective (e.g., list page collection + detail page extraction) stay as one capability, orchestrated via composite components
4. Set `skill-name` and capability directory names (lowercase English, hyphen-separated), create directories under `output/{skill-name}/` (use user-specified path if given)
5. Confirm complete execution plan with user:

```
Target site: {url}
Output: output/{skill-name}/

Capabilities (executed in order):
1. {site-slug}-{capability-slug} ({extraction/operation}) — {one-line description}
2. {site-slug}-{capability-slug} ({extraction/operation}) — {one-line description}
...
```

If execution intent was identified in 1a, append to the plan:
```
Pipeline:
1. Explore site → discover and verify viable API endpoints or DOM extraction methods
2. Generate Skill files (SKILL.md + scripts)
3. Automated testing to confirm Skill works
4. Install Skill
5. Read installed Skill → write and run batch scripts to fulfill user's original task
```

Present the plan and wait for user to confirm or adjust. Do not ask separate questions about items that have reasonable defaults (output directory, naming conventions, etc.).

After user confirms, enter execution loop with no mid-process questions.

---

> **Phase 2 and Phase 3 below execute in a loop for each capability unit — complete one before starting the next.**

---

## Phase 2 — Capability Exploration

Read the corresponding reference file based on capability type:
- **Extraction** → `references/exploration_extraction.md`
- **Operation** → `references/exploration_operation.md`

**Goal**: prioritize API endpoints for target capability; fall back to DOM operations when API isn't viable. Record complete reproducible invocation methods.

**Success criteria**:
- Can stably obtain target data / trigger target action (API or DOM path)
- Complete invocation/operation method recorded (endpoint + params, or selectors + interaction steps)
- Enum parameters collected for all meaningful values

**When a means fails, follow this sequence:**
1. Do not retry with different parameters (varying parameters rarely changes the outcome)
2. Return to the goal itself
3. Enumerate all alternative means that could achieve the goal
4. Pick the next one and execute

A deterministic failure (explicit error code, structural mismatch) confirms the means is unviable in one attempt. A transient failure (timeout, connection drop) warrants one retry — but not more.

**Exploration cap**: 100 tool call steps. If still unable to progress, report known obstacles to user and ask for next steps.

**Don't touch experience notes**: experience notes (`browser-act-skill-forge-memories/`) are for generated Skills' future Agent use — neither read nor write during exploration and generation phases.

---


## Progressive Disclosure References (On-Demand)
- Detailed templates, extended examples, and deep-dive checklists have been moved to [references/detailed-guide.md](./references/detailed-guide.md) to keep context lean. Load that file via `view_file` only when needed.

## ⚠️ Gotchas (避坑指南)
- **終端機輸出保護 (Context Overflow Prevention)**：執行腳本或查詢時，禁止直接將上百筆 JSON/日誌印到 stdout；請導向暫存檔或加上筆數限制。
- **優先使用確定性腳本**：遇到格式轉換、字數統計或合規檢查，優先調用 `scripts/` 下的 Python 工具，不要依賴純語意猜測。
