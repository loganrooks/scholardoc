# Debugging Guide

## Purpose

Systematically diagnose and fix issues by isolating root causes rather than guessing at symptoms.

## Principles

1. **Reproduce first** - Can't fix what you can't see
2. **Isolate the problem** - Narrow scope systematically
3. **Read error messages** - They often tell you exactly what's wrong
4. **One change at a time** - Know what fixed it
5. **Document findings** - Help future debugging sessions

## Debugging Process

### Phase 1: UNDERSTAND

```
1. What is the expected behavior?
2. What is the actual behavior?
3. What error messages/logs exist?
4. When did it start failing?
5. What changed recently?
```

### Phase 2: REPRODUCE

```
1. Create minimal reproduction case
2. Identify exact steps to trigger
3. Determine: Always fails? Intermittent?
4. Note: Environment? Data? Timing?
```

### Phase 3: ISOLATE

Binary search approach:
```
1. Start with known-good state
2. Add components until failure occurs
3. OR: Remove components until failure disappears
4. Pinpoint the difference
```

### Phase 4: DIAGNOSE

```
1. Form hypothesis based on evidence
2. Test hypothesis with specific experiment
3. If wrong, revise hypothesis
4. Continue until root cause identified
```

### Phase 5: FIX

```
1. Implement minimal fix for root cause
2. Verify fix resolves the issue
3. Add test to prevent regression
4. Check for similar issues elsewhere
```

## Diagnostic Techniques

### Reading Stack Traces

```
1. Start at the BOTTOM (root cause)
2. Follow up through YOUR code
3. Note: file, line number, function
4. Error message is usually most helpful
```

### Strategic Logging

```python
# Bad: Too verbose
logger.debug(f"Processing {data}")

# Good: Decision points and state changes
logger.info(f"Starting process: items={len(data)}, mode={mode}")
logger.error(f"Failed to process item {item_id}: {error}")
```

### Binary Search Debugging

```
1. Comment out half the suspect code
2. Does problem persist?
3. If yes: problem in remaining half
4. If no: problem in commented half
5. Repeat until isolated
```

### Diff Analysis

```bash
# What changed recently?
git log --oneline -10
git diff HEAD~5

# When did it start failing?
git bisect start
git bisect bad HEAD
git bisect good <known-good-commit>
```

## Common Bug Categories

| Category | Symptoms | Check |
|----------|----------|-------|
| Null/undefined | Crash on access | Input validation |
| Off-by-one | Wrong count, missing items | Loop boundaries |
| Race condition | Intermittent failure | Async operations |
| State mutation | Unexpected values | Shared mutable state |
| Type mismatch | "undefined is not a function" | Type checks, interfaces |
| Import/path | Module not found | Import statements, paths |

## Quality Criteria

A good debugging session:
- [ ] Root cause identified, not just symptom
- [ ] Minimal reproduction exists
- [ ] Fix addresses root cause
- [ ] Regression test added
- [ ] Similar issues checked
- [ ] Findings documented if non-trivial

## Anti-patterns

- **Shotgun debugging**: Random changes hoping something works
- **Print statement spam**: Unstructured logging everywhere
- **Fixing symptoms**: Treating effects, not causes
- **Assumption blindness**: "That can't be the problem"
- **Solo suffering**: Not asking for help when stuck
- **No test after fix**: Same bug can return

## Adaptation Notes

When generating for a project:
- Reference project's logging framework
- Include project-specific debug commands
- Mention relevant monitoring/observability tools
- Note project's test commands for verification
- Include relevant environment setup for reproduction
