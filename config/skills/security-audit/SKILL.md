---
name: security-audit
description: "Use when auditing auth, file uploads, or APIs for SQL injection, path traversal, and vulnerabilities. 資安稽核/漏洞掃描/SQL Injection與Path Traversal"
---

# Security Audit Skill

## Purpose
Comprehensive security scanning and vulnerability detection. Includes input validation, path traversal prevention, CVE detection, and secure coding pattern enforcement.

## When to Trigger
- authentication implementation
- authorization logic
- payment processing
- user data handling
- API endpoint creation
- file upload handling
- database queries
- external API integration

## When to Skip
- read-only operations on public data
- internal development tooling
- static documentation
- styling changes

## Commands

### Full Security Scan
Run comprehensive security analysis on the codebase

```bash
[Security Scan Action] Perform security analysis with parameters: --depth full
```

**Example:**
```bash
[Security Scan Action] Perform security analysis with parameters: --depth full --output security-report.json
```

### Input Validation Check
Check for input validation issues

```bash
[Security Scan Action] Perform security analysis with parameters: --check input-validation
```

**Example:**
```bash
[Security Scan Action] Perform security analysis with parameters: --check input-validation --path ./src/api
```

### Path Traversal Check
Check for path traversal vulnerabilities

```bash
[Security Scan Action] Perform security analysis with parameters: --check path-traversal
```

### SQL Injection Check
Check for SQL injection vulnerabilities

```bash
[Security Scan Action] Perform security analysis with parameters: --check sql-injection
```

### XSS Check
Check for cross-site scripting vulnerabilities

```bash
[Security Scan Action] Perform security analysis with parameters: --check xss
```

### CVE Scan
Scan dependencies for known CVEs

```bash
npx @claude-flow/cli security cve --scan
```

**Example:**
```bash
npx @claude-flow/cli security cve --scan --severity high
```

### Security Audit Report
Generate full security audit report

```bash
npx @claude-flow/cli security audit --report
```

**Example:**
```bash
npx @claude-flow/cli security audit --report --format markdown --output SECURITY.md
```

### Threat Modeling
Run threat modeling analysis

```bash
npx @claude-flow/cli security threats --analyze
```

### Validate Secrets
Check for hardcoded secrets

```bash
npx @claude-flow/cli security validate --check secrets
```


## Scripts

| Script | Path | Description |
|--------|------|-------------|
| `security-scan` | `.agents/scripts/security-scan.sh` | Run full security scan pipeline |
| `cve-remediate` | `.agents/scripts/cve-remediate.sh` | Auto-remediate known CVEs |


## References

| Document | Path | Description |
|----------|------|-------------|
| `Security Checklist` | `docs/security-checklist.md` | Security review checklist |
| `OWASP Guide` | `docs/owasp-top10.md` | OWASP Top 10 mitigation guide |

## Best Practices
1. Check memory for existing patterns before starting
2. Use hierarchical topology for coordination
3. Store successful patterns after completion
4. Document any new learnings

## ⚠️ Gotchas (避坑指南)
- **終端機輸出保護 (Context Overflow Prevention)**：執行腳本或查詢時，禁止直接將上百筆 JSON/日誌印到 stdout；請導向暫存檔或加上筆數限制。
- **優先使用確定性腳本**：遇到格式轉換、字數統計或合規檢查，優先調用 `scripts/` 下的 Python 工具，不要依賴純語意猜測。
