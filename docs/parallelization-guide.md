# Parallelization Guide

Best practices for parallel agent delegation in autonomous development workflows.

## Core Principle

> **Parallelize reads, serialize writes.**
>
> Read operations (exploration, analysis, review) are safe to parallelize.
> Write operations (implementation, git) should remain sequential to avoid conflicts.

## When to Parallelize

### High Value (Always Consider)

| Task Type | Agent | Model | Risk |
|-----------|-------|-------|------|
| Multi-area exploration | `Explore` | sonnet | Low |
| Independent reviews | `general-purpose` | sonnet | Low |
| Log source analysis | `Explore` | sonnet | Low |
| Pattern diagnosis | `root-cause-analyst` | sonnet | Low |

### Medium Value (Context-Dependent)

| Task Type | Agent | Model | Risk |
|-----------|-------|-------|------|
| Documentation + Testing | `quality-engineer` | sonnet | Medium |
| Multiple improvement reviews | `general-purpose` | sonnet | Low |

### Avoid Parallelizing

| Task Type | Reason |
|-----------|--------|
| Implementation | File conflicts, merge issues |
| Git operations | Race conditions |
| Sequential dependencies | Ordering matters |
| Single-file changes | No benefit |

## Syntax Examples

### Parallel Exploration (3 areas)

```
# In a single message, spawn multiple Task calls:
Task(subagent_type="Explore", model="sonnet", prompt="Explore authentication code in src/auth/")
Task(subagent_type="Explore", model="sonnet", prompt="Explore API routes in src/routes/")
Task(subagent_type="Explore", model="sonnet", prompt="Explore test patterns in tests/")
```

### Parallel Reviews

```
Task(subagent_type="general-purpose", model="sonnet", prompt="Code review: Check for security issues in [diff]")
Task(subagent_type="general-purpose", model="sonnet", prompt="Code review: Check for performance issues in [diff]")
Task(subagent_type="general-purpose", model="sonnet", prompt="Code review: Check for maintainability in [diff]")
```

### Parallel Log Analysis

```
Task(subagent_type="Explore", model="sonnet", prompt="Analyze .claude/logs/signals/ for patterns")
Task(subagent_type="Explore", model="sonnet", prompt="Analyze git log --oneline -50 for fix/revert patterns")
Task(subagent_type="Explore", model="sonnet", prompt="Analyze ~/.claude/projects/ JSONL for tool failures")
```

### Parallel Diagnosis

```
Task(subagent_type="root-cause-analyst", model="sonnet", prompt="Diagnose: repeated test failures in auth module")
Task(subagent_type="root-cause-analyst", model="sonnet", prompt="Diagnose: context loss between sessions")
Task(subagent_type="root-cause-analyst", model="sonnet", prompt="Diagnose: lint errors not being caught")
```

## Model Selection

| Scenario | Model | Rationale |
|----------|-------|-----------|
| Code exploration | `sonnet` | Needs understanding |
| Code review | `sonnet` | Quality matters |
| Pattern analysis | `sonnet` | Synthesis required |
| Log aggregation | `haiku` | Simple counting/grep |
| File listing | `haiku` | Mechanical task |
| Summary generation | `sonnet` | Quality matters |

**Rule of thumb**: Use `haiku` only for truly mechanical tasks where quality of reasoning doesn't matter. When in doubt, use `sonnet`.

## Parallelization Decision Tree

```
Is the task read-only?
├── No → Keep sequential (avoid conflicts)
└── Yes → Can be split into independent parts?
    ├── No → Keep sequential
    └── Yes → Are there 3+ parts?
        ├── No → Sequential is fine (overhead not worth it)
        └── Yes → Parallelize with Task tool
            └── Choose model based on task complexity
```

## Integration with Workflows

### /project:auto

| Phase | Parallelization |
|-------|-----------------|
| 0: Requirements | Sequential (human interaction) |
| 1: Exploration | **Parallel** if multiple areas |
| 2: Planning | Sequential (needs exploration results) |
| 3: Implementation | Sequential (avoid conflicts) |
| 4: Doc + Validation | **Parallel** (independent) |
| 5: Integration | Sequential |
| 6: Completion | Sequential |

### /project:improve

| Phase | Parallelization |
|-------|-----------------|
| 1: Explore signals | **Parallel** (multiple sources) |
| 2: Diagnose | **Parallel** (multiple patterns) |
| 3: Plan improvements | Sequential (needs diagnosis) |
| 3.3: Review proposals | **Parallel** (independent reviews) |
| 4: Implement | Sequential (avoid conflicts) |
| 5: Validate | Sequential |

### /project:analyze-logs

| Phase | Parallelization |
|-------|-----------------|
| 1: Gather data | **Parallel** (signal, git, native logs) |
| 2: Pattern analysis | **Parallel** (by source) |
| 3: Aggregation | Sequential |
| 4: Sequential thinking | Sequential |
| 5: Report | Sequential |

## Overhead Considerations

Parallelization has overhead:
- Agent spawn time (~1-2s per agent)
- Context transfer cost
- Result aggregation

**Parallelize when**:
- 3+ independent tasks
- Each task takes >10 seconds
- Total time savings > overhead

**Keep sequential when**:
- 1-2 tasks
- Tasks are fast (<10s each)
- Tasks have dependencies

## Error Handling

When parallel agents fail:
1. Collect all results (success and failure)
2. Retry failed agents individually
3. If still failing, fall back to sequential
4. Report which agents failed and why

```
# Example error handling pattern
results = await Promise.allSettled([
  Task(agent1),
  Task(agent2),
  Task(agent3)
]);

failed = results.filter(r => r.status === 'rejected');
if (failed.length > 0) {
  // Retry failed ones sequentially
  for (const f of failed) {
    await Task(f.reason.agent); // Sequential retry
  }
}
```

## Monitoring

Track parallelization effectiveness:
- Time saved vs sequential
- Agent failure rates
- Quality of parallel results

Log in session notes:
```
## Parallelization Used
- Exploration: 3 agents (frontend, backend, tests) → 45s vs ~2min sequential
- Reviews: 2 agents (security, performance) → 30s vs ~1min sequential
```
