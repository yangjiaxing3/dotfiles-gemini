---
name: github-code-review
description: "''''Use when tasks involve github code review: Comprehensive GitHub code review with AI-powered swarm coordination''''"
version: 1.0.0
---

# GitHub Code Review Skill

> **AI-Powered Code Review**: Deploy specialized review agents to perform comprehensive, intelligent code reviews that go beyond traditional static analysis.

## 🎯 Quick Start

### Simple Review
```bash
# Initialize review swarm for PR
gh pr view 123 --json files,diff | npx ruv-swarm github review-init --pr 123

# Post review status
gh pr comment 123 --body "🔍 Multi-agent code review initiated"
```

### Complete Review Workflow
```bash
# Get PR context with gh CLI
PR_DATA=$(gh pr view 123 --json files,additions,deletions,title,body)
PR_DIFF=$(gh pr diff 123)

# Initialize comprehensive review
npx ruv-swarm github review-init \
  --pr 123 \
  --pr-data "$PR_DATA" \
  --diff "$PR_DIFF" \
  --agents "security,performance,style,architecture,accessibility" \
  --depth comprehensive
```

---

## 📚 Table of Contents

<details>
<summary><strong>Core Features<$strong><$summary>

- [Multi-Agent Review System](#multi-agent-review-system)
- [Specialized Review Agents](#specialized-review-agents)
- [PR-Based Swarm Management](#pr-based-swarm-management)
- [Automated Workflows](#automated-workflows)
- [Quality Gates & Checks](#quality-gates--checks)

<$details>

<details>
<summary><strong>Review Agents<$strong><$summary>

- [Security Review Agent](#security-review-agent)
- [Performance Review Agent](#performance-review-agent)
- [Architecture Review Agent](#architecture-review-agent)
- [Style & Convention Agent](#style--convention-agent)
- [Accessibility Agent](#accessibility-agent)

<$details>

<details>
<summary><strong>Advanced Features<$strong><$summary>

- [Context-Aware Reviews](#context-aware-reviews)
- [Learning from History](#learning-from-history)
- [Cross-PR Analysis](#cross-pr-analysis)
- [Custom Review Agents](#custom-review-agents)

<$details>

<details>
<summary><strong>Integration & Automation<$strong><$summary>

- [CI/CD Integration](#cicd-integration)
- [Webhook Handlers](#webhook-handlers)
- [PR Comment Commands](#pr-comment-commands)
- [Automated Fixes](#automated-fixes)

<$details>

---

## 🚀 Core Features

### Multi-Agent Review System

Deploy specialized AI agents for comprehensive code review:

```bash
# Initialize review swarm with GitHub CLI integration
PR_DATA=$(gh pr view 123 --json files,additions,deletions,title,body)
PR_DIFF=$(gh pr diff 123)

# Start multi-agent review
npx ruv-swarm github review-init \
  --pr 123 \
  --pr-data "$PR_DATA" \
  --diff "$PR_DIFF" \
  --agents "security,performance,style,architecture,accessibility" \
  --depth comprehensive

# Post initial review status
gh pr comment 123 --body "🔍 Multi-agent code review initiated"
```

**Benefits:**
- ✅ Parallel review by specialized agents
- ✅ Comprehensive coverage across multiple domains
- ✅ Faster review cycles with coordinated analysis
- ✅ Consistent quality standards enforcement

---

## 🤖 Specialized Review Agents

### Security Review Agent

**Focus:** Identify security vulnerabilities and suggest fixes

```bash
# Get changed files from PR
CHANGED_FILES=$(gh pr view 123 --json files --jq '.files[].path')

# Run security-focused review
SECURITY_RESULTS=$(npx ruv-swarm github review-security \
  --pr 123 \
  --files "$CHANGED_FILES" \
  --check "owasp,cve,secrets,permissions" \
  --suggest-fixes)

# Post findings based on severity
if echo "$SECURITY_RESULTS" | grep -q "critical"; then
  # Request changes for critical issues
  gh pr review 123 --request-changes --body "$SECURITY_RESULTS"
  gh pr edit 123 --add-label "security-review-required"
else
  # Post as comment for non-critical issues
  gh pr comment 123 --body "$SECURITY_RESULTS"
fi
```

<details>
<summary><strong>Security Checks Performed<$strong><$summary>


## Progressive Disclosure References (On-Demand)
- Detailed templates, extended examples, and deep-dive checklists have been moved to [references/detailed-guide.md](./references/detailed-guide.md) to keep context lean. Load that file via `view_file` only when needed.

## ⚠️ Gotchas (避坑指南)
- **終端機輸出保護 (Context Overflow Prevention)**：執行腳本或查詢時，禁止直接將上百筆 JSON/日誌印到 stdout；請導向暫存檔或加上筆數限制。
- **優先使用確定性腳本**：遇到格式轉換、字數統計或合規檢查，優先調用 `scripts/` 下的 Python 工具，不要依賴純語意猜測。
