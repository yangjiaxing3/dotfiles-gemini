---
name: github-workflow-automation
description: "''''Use when tasks involve github workflow automation: Advanced GitHub Actions workflow automation with AI swarm coordination..."
version: 1.0.0
---

# GitHub Workflow Automation Skill

## Overview

This skill provides comprehensive GitHub Actions automation with AI swarm coordination. It integrates intelligent CI/CD pipelines, workflow orchestration, and repository management to create self-organizing, adaptive GitHub workflows.

## Quick Start

<details>
<summary>💡 Basic Usage - Click to expand<$summary>

### Initialize GitHub Workflow Automation
```bash
# Start with a simple workflow
npx ruv-swarm actions generate-workflow \
  --analyze-codebase \
  --detect-languages \
  --create-optimal-pipeline
```

### Common Commands
```bash
# Optimize existing workflow
npx ruv-swarm actions optimize \
  --workflow ".github$workflows$ci.yml" \
  --suggest-parallelization

# Analyze failed runs
gh run view <run-id> --json jobs,conclusion | \
  npx ruv-swarm actions analyze-failure \
    --suggest-fixes
```

<$details>

## Core Capabilities

### 🤖 Swarm-Powered GitHub Modes

<details>
<summary>Available GitHub Integration Modes<$summary>

#### 1. gh-coordinator
**GitHub workflow orchestration and coordination**
- **Coordination Mode**: Hierarchical
- **Max Parallel Operations**: 10
- **Batch Optimized**: Yes
- **Best For**: Complex GitHub workflows, multi-repo coordination

```bash
# Usage example
npx claude-flow@alpha github gh-coordinator \
  "Coordinate multi-repo release across 5 repositories"
```

#### 2. pr-manager
**Pull request management and review coordination**
- **Review Mode**: Automated
- **Multi-reviewer**: Yes
- **Conflict Resolution**: Intelligent

```bash
# Create PR with automated review
gh pr create --title "Feature: New capability" \
  --body "Automated PR with swarm review" | \
  npx ruv-swarm actions pr-validate \
    --spawn-agents "linter,tester,security,docs"
```

#### 3. issue-tracker
**Issue management and project coordination**
- **Issue Workflow**: Automated
- **Label Management**: Smart
- **Progress Tracking**: Real-time

```bash
# Create coordinated issue workflow
npx claude-flow@alpha github issue-tracker \
  "Manage sprint issues with automated tracking"
```

#### 4. release-manager
**Release coordination and deployment**
- **Release Pipeline**: Automated
- **Versioning**: Semantic
- **Deployment**: Multi-stage

```bash
# Automated release management
npx claude-flow@alpha github release-manager \
  "Create v2.0.0 release with changelog and deployment"
```

#### 5. repo-architect
**Repository structure and organization**
- **Structure Optimization**: Yes
- **Multi-repo Support**: Yes
- **Template Management**: Advanced

```bash
# Optimize repository structure
npx claude-flow@alpha github repo-architect \
  "Restructure monorepo with optimal organization"
```

#### 6. code-reviewer
**Automated code review and quality assurance**
- **Review Quality**: Deep
- **Security Analysis**: Yes
- **Performance Check**: Automated

```bash
# Automated code review
gh pr view 123 --json files | \
  npx ruv-swarm actions pr-validate \
    --deep-review \
    --security-scan
```

#### 7. ci-orchestrator
**CI/CD pipeline coordination**
- **Pipeline Management**: Advanced
- **Test Coordination**: Parallel
- **Deployment**: Automated

```bash
# Orchestrate CI/CD pipeline
npx claude-flow@alpha github ci-orchestrator \
  "Setup parallel test execution with smart caching"
```

#### 8. security-guardian
**Security and compliance management**
- **Security Scan**: Automated
- **Compliance Check**: Continuous
- **Vulnerability Management**: Proactive

```bash
# Security audit
npx ruv-swarm actions security \

## Progressive Disclosure References (On-Demand)
- Detailed templates, extended examples, and deep-dive checklists have been moved to [references/detailed-guide.md](./references/detailed-guide.md) to keep context lean. Load that file via `view_file` only when needed.

## ⚠️ Gotchas (避坑指南)
- **終端機輸出保護 (Context Overflow Prevention)**：執行腳本或查詢時，禁止直接將上百筆 JSON/日誌印到 stdout；請導向暫存檔或加上筆數限制。
- **優先使用確定性腳本**：遇到格式轉換、字數統計或合規檢查，優先調用 `scripts/` 下的 Python 工具，不要依賴純語意猜測。
