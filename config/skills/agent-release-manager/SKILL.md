---
name: agent-release-manager
description: "Use when preparing semantic versioning changelogs, release checklists, and rollback plans. 版本發布檢查清單與Changelog管理"
---

---
name: release-manager
description: Automated release coordination and deployment with ruv-swarm orchestration for seamless version management, testing, and deployment across multiple packages
type: development
color: "#FF6B35"
tools:
  - Bash
  - Read
  - Write
  - Edit
  - TodoWrite
  - TodoRead
  - Task
  - WebFetch
  - mcp__github__create_pull_request
  - mcp__github__merge_pull_request
  - mcp__github__create_branch
  - mcp__github__push_files
  - mcp__github__create_issue
  - mcp__claude-flow__swarm_init
  - mcp__claude-flow__agent_spawn
  - mcp__claude-flow__task_orchestrate
  - mcp__claude-flow__memory_usage
hooks:
  pre_task: |
    echo "🚀 Initializing release management pipeline..."
    npx ruv-swarm hook pre-task --mode release-manager
  post_edit: |
    echo "📝 Validating release changes and updating documentation..."
    npx ruv-swarm hook post-edit --mode release-manager --validate-release
  post_task: |
    echo "✅ Release management task completed. Updating release status..."
    npx ruv-swarm hook post-task --mode release-manager --update-status
  notification: |
    echo "📢 Sending release notifications to stakeholders..."
    npx ruv-swarm hook notification --mode release-manager
---

# GitHub Release Manager

## Purpose
Automated release coordination and deployment with ruv-swarm orchestration for seamless version management, testing, and deployment across multiple packages.

## Capabilities
- **Automated release pipelines** with comprehensive testing
- **Version coordination** across multiple packages
- **Deployment orchestration** with rollback capabilities  
- **Release documentation** generation and management
- **Multi-stage validation** with swarm coordination

## Usage Patterns

### 1. Coordinated Release Preparation
```javascript
// Initialize release management swarm
mcp__claude-flow__swarm_init { topology: "hierarchical", maxAgents: 6 }
mcp__claude-flow__agent_spawn { type: "coordinator", name: "Release Coordinator" }
mcp__claude-flow__agent_spawn { type: "tester", name: "QA Engineer" }
mcp__claude-flow__agent_spawn { type: "reviewer", name: "Release Reviewer" }
mcp__claude-flow__agent_spawn { type: "coder", name: "Version Manager" }
mcp__claude-flow__agent_spawn { type: "analyst", name: "Deployment Analyst" }

// Create release preparation branch
mcp__github__create_branch {
  owner: "ruvnet",
  repo: "ruv-FANN",
  branch: "release$v1.0.72",
  from_branch: "main"
}

// Orchestrate release preparation
mcp__claude-flow__task_orchestrate {
  task: "Prepare release v1.0.72 with comprehensive testing and validation",
  strategy: "sequential",
  priority: "critical"
}
```

### 2. Multi-Package Version Coordination
```javascript
// Update versions across packages
mcp__github__push_files {
  owner: "ruvnet",
  repo: "ruv-FANN", 
  branch: "release$v1.0.72",
  files: [
    {
      path: "claude-code-flow$claude-code-flow$package.json",
      content: JSON.stringify({
        name: "claude-flow",
        version: "1.0.72",
        // ... rest of package.json
      }, null, 2)
    },
    {
      path: "ruv-swarm$npm$package.json", 
      content: JSON.stringify({
        name: "ruv-swarm",
        version: "1.0.12",
        // ... rest of package.json
      }, null, 2)
    },
    {
      path: "CHANGELOG.md",
      content: `# Changelog

## [1.0.72] - ${new Date().toISOString().split('T')[0]}

### Added
- Comprehensive GitHub workflow integration
- Enhanced swarm coordination capabilities
- Advanced MCP tools suite

### Changed  
- Aligned Node.js version requirements
- Improved package synchronization
- Enhanced documentation structure

### Fixed
- Dependency resolution issues
- Integration test reliability
- Memory coordination optimization`
    }
  ],
  message: "release: Prepare v1.0.72 with GitHub integration and swarm enhancements"
}
```

### 3. Automated Release Validation
```javascript
// Comprehensive release testing
Bash("cd $workspaces$ruv-FANN$claude-code-flow$claude-code-flow && npm install")
Bash("cd $workspaces$ruv-FANN$claude-code-flow$claude-code-flow && npm run test")
Bash("cd $workspaces$ruv-FANN$claude-code-flow$claude-code-flow && npm run lint")
Bash("cd $workspaces$ruv-FANN$claude-code-flow$claude-code-flow && npm run build")

Bash("cd $workspaces$ruv-FANN$ruv-swarm$npm && npm install")
Bash("cd $workspaces$ruv-FANN$ruv-swarm$npm && npm run test:all")
Bash("cd $workspaces$ruv-FANN$ruv-swarm$npm && npm run lint")


## Progressive Disclosure References (On-Demand)
- Detailed templates, extended examples, and deep-dive checklists have been moved to [references/detailed-guide.md](./references/detailed-guide.md) to keep context lean. Load that file via `view_file` only when needed.

## ⚠️ Gotchas (避坑指南)
- **終端機輸出保護 (Context Overflow Prevention)**：執行腳本或查詢時，禁止直接將上百筆 JSON/日誌印到 stdout；請導向暫存檔或加上筆數限制。
- **優先使用確定性腳本**：遇到格式轉換、字數統計或合規檢查，優先調用 `scripts/` 下的 Python 工具，不要依賴純語意猜測。
