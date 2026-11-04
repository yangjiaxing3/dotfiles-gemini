# subagent-driven-development — Detailed Reference & Extended Examples

## Advantages

**vs. Manual execution:**
- Subagents follow TDD naturally
- Fresh context per task (no confusion)
- Parallel-safe (subagents don't interfere)
- Subagent can ask questions (before AND during work)

**vs. Executing Plans:**
- Same session (no handoff)
- Continuous progress (no waiting)
- Review checkpoints automatic

**Efficiency gains:**
- No file reading overhead (controller provides full text)
- Controller curates exactly what context is needed
- Subagent gets complete information upfront
- Questions surfaced before work begins (not after)

**Quality gates:**
- Self-review catches issues before handoff
- Two-stage review: spec compliance, then code quality
- Review loops ensure fixes actually work
- Spec compliance prevents over/under-building
- Code quality ensures implementation is well-built

**Cost:**
- More subagent invocations (implementer + 2 reviewers per task)
- Controller does more prep work (extracting all tasks upfront)
- Review loops add iterations
- But catches issues early (cheaper than debugging later)

## Red Flags

**Never:**
- Skip reviews (spec compliance OR code quality)
- Proceed with unfixed issues
- Dispatch multiple implementation subagents in parallel (conflicts)
- Make subagent read plan file (provide full text instead)
- Skip scene-setting context (subagent needs to understand where task fits)
- Ignore subagent questions (answer before letting them proceed)
- Accept "close enough" on spec compliance (spec reviewer found issues = not done)
- Skip review loops (reviewer found issues = implementer fixes = review again)
- Let implementer self-review replace actual review (both are needed)
- **Start code quality review before spec compliance is ✅** (wrong order)
- Move to next task while either review has open issues
- **Hand off to Spec Reviewer without a PASS test or E2E check** (Always run dynamic Execution Validation/Verification Checkpoint first)

**If subagent asks questions:**
- Answer clearly and completely
- Provide additional context if needed
- Don't rush them into implementation

**If reviewer finds issues (Bounded Loop):**
- Implementer (same subagent) fixes them.
- Reviewer reviews again.
- **Limit:** Repeat maximum 3 times. Do not loop infinitely.
- If rejected after 3 attempts, escalate to Fixer Subagent.

**If subagent fails task or reaches 3-loop limit:**
- Dispatch **Fixer subagent (Agent D)** with ZERO previous context (Surgical Fixer Loop).
- Tell Fixer: "Run failing checks. Read files. State actual cause in 1 sentence. Fix only that cause. Use the specific error log and single AST to prevent context pollution."
- Don't try to fix manually (context pollution).
- **Learning Loop**: After Fixer succeeds and returns `<PatternExtract>`, Manager MUST execute `[Memory Store Action] Save the knowledge globally by appending it to your system memory or a local `.memory` markdown file. Pattern: "[PatternExtract]"` to save the knowledge globally.

**Context Injection (自我進化)**:
- Before spawning any new Implementer or Reviewer, Manager should retrieve relevant patterns (e.g. `[Memory Search Action] Search the AI knowledge base or local .memory files for patterns related to "seo".`) and inject them into the subagent's context.

## Integration

**Required workflow skills:**
- **superpowers:writing-plans** - Creates the plan this skill executes
- **superpowers:requesting-code-review** - Code review template for reviewer subagents
- **superpowers:finishing-a-development-branch** - Complete development after all tasks

**Subagents should use:**
- **superpowers:test-driven-development** - Subagents follow TDD for each task

**Alternative workflow:**
- **superpowers:executing-plans** - Use for parallel session instead of same-session execution
