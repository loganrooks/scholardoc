---
description: Analyze session logs for self-improvement patterns
allowed-tools: Read, Glob, Grep, Bash, Task, mcp__serena__*, mcp__sequential-thinking__*
argument-hint: [scope: session|week|month|all] [focus: errors|patterns|metrics|all]
---

# Analyze Logs: $ARGUMENTS

Systematic analysis of session logs to identify improvement opportunities.

## Parallelization Strategy

For comprehensive analysis, spawn parallel agents to analyze different data sources:

```
# Parallel log analysis (single message, multiple Task calls)
Task(subagent_type="Explore", model="sonnet", prompt="Analyze .claude/logs/signals/ for error patterns and frequency")
Task(subagent_type="Explore", model="sonnet", prompt="Analyze git log for fix/revert patterns and hotspot files")
Task(subagent_type="Explore", model="sonnet", prompt="Analyze native Claude logs at ~/.claude/projects/ for tool failures")
```

After parallel analysis completes, synthesize findings into unified report.

## Phase 1: Gather Log Data

### 1.1 Custom Session Logs
```bash
# List available session logs
ls -lt .claude/logs/sessions/ 2>/dev/null | head -20

# Count by time period
echo "This week:"
find .claude/logs/sessions/ -mtime -7 -name "*.md" 2>/dev/null | wc -l

echo "This month:"
find .claude/logs/sessions/ -mtime -30 -name "*.md" 2>/dev/null | wc -l
```

### 1.2 Native Claude Code Logs (JSONL)
```bash
# Claude Code stores detailed logs here
CLAUDE_LOG_DIR="$HOME/.claude/projects$(pwd)"

if [ -d "$CLAUDE_LOG_DIR" ]; then
  echo "Native logs available:"
  ls -lt "$CLAUDE_LOG_DIR"/*.jsonl 2>/dev/null | head -10
else
  echo "No native Claude logs found at: $CLAUDE_LOG_DIR"
fi
```

### 1.3 Unprocessed Signals
```bash
ls -la .claude/logs/signals/ 2>/dev/null | grep -v "^d" | grep -v ".gitkeep" | grep -v "processed"
```

---

## Phase 2: Pattern Analysis

### 2.1 Error Patterns
```bash
# Aggregate errors from session logs
echo "=== Error Frequency ==="
grep -rh "Issue\|Error\|FAIL" .claude/logs/sessions/*.md 2>/dev/null | sort | uniq -c | sort -rn | head -10
```

### 2.2 Warning Patterns
```bash
echo "=== Warning Frequency ==="
grep -rh "Warning\|WARN" .claude/logs/sessions/*.md 2>/dev/null | sort | uniq -c | sort -rn | head -10
```

### 2.3 Git Patterns
```bash
echo "=== Commit Message Patterns ==="
git log --oneline -100 | grep -iE "fix|bug|revert|oops|typo|wip" | head -20

echo "=== Hotspot Files (frequently changed) ==="
git log --name-only --oneline -100 | grep -v "^[a-f0-9]" | sort | uniq -c | sort -rn | head -15
```

---

## Phase 3: Metric Aggregation

### 3.1 Session Metrics
```bash
# Calculate averages from session logs
echo "=== Session Metrics Summary ==="

# Average files modified per session
grep -rh "Files Modified" .claude/logs/sessions/*.md 2>/dev/null |
  grep -oE "[0-9]+" |
  awk '{ sum += $1; count++ } END { if (count > 0) print "Avg files/session:", sum/count }'

# Average lint errors
grep -rh "Lint Errors" .claude/logs/sessions/*.md 2>/dev/null |
  grep -oE "[0-9]+" |
  awk '{ sum += $1; count++ } END { if (count > 0) print "Avg lint errors:", sum/count }'

# TODO accumulation trend
grep -rh "TODOs Added" .claude/logs/sessions/*.md 2>/dev/null |
  grep -oE "[0-9]+" |
  awk '{ sum += $1; count++ } END { if (count > 0) print "Total TODOs added:", sum }'
```

### 3.2 Native Log Analysis (if available)
```bash
# Parse JSONL for tool usage patterns
CLAUDE_LOG_DIR="$HOME/.claude/projects$(pwd)"

if [ -f "$CLAUDE_LOG_DIR"/*.jsonl ]; then
  echo "=== Tool Usage Patterns ==="
  cat "$CLAUDE_LOG_DIR"/*.jsonl 2>/dev/null |
    grep -o '"tool":"[^"]*"' |
    sort | uniq -c | sort -rn | head -10
fi
```

---

## Phase 4: Sequential Analysis (Deep Dive)

For complex pattern analysis, use sequential thinking:

```
Use mcp__sequential-thinking__sequentialthinking to:

1. Review the aggregated patterns above
2. Identify recurring themes
3. Correlate errors with specific file types or workflows
4. Hypothesize root causes
5. Prioritize by impact and frequency
6. Propose targeted improvements
```

---

## Phase 5: Generate Report

### Analysis Report Template

```markdown
## Log Analysis Report

**Scope**: $ARGUMENTS
**Period**: [date range]
**Sessions Analyzed**: [count]

### Error Summary

| Error Type | Frequency | Trend | Root Cause Hypothesis |
|------------|-----------|-------|----------------------|
| | | | |

### Warning Summary

| Warning Type | Frequency | Actionable? |
|--------------|-----------|-------------|
| | | |

### Hotspots

Files requiring frequent changes (may indicate design issues):
1. [file]: [change count] - [hypothesis]
2. ...

### Metric Trends

| Metric | This Week | Last Week | Trend |
|--------|-----------|-----------|-------|
| Files/session | | | |
| Lint errors | | | |
| TODOs added | | | |

### Pattern Categories

| Category | Signals | Frequency | System Component |
|----------|---------|-----------|------------------|
| Repeated errors | | | |
| Workflow friction | | | |
| Context loss | | | |
| Rule ignored | | | |

### Recommended Improvements

| Priority | Type | Target | Rationale |
|----------|------|--------|-----------|
| P0 | | | |
| P1 | | | |
| P2 | | | |

### Next Steps

1. Run `/project:diagnose [top-pattern]` for deep analysis
2. Run `/project:improve [trigger]` to implement changes
3. Schedule next analysis: [timing]
```

---

## Integration with Claude Agent SDK

For automated analysis, the Claude Agent SDK can be used in headless mode:

```typescript
// Example: Automated log analysis with SDK
import Anthropic from "@anthropic-ai/sdk";

const client = new Anthropic();

async function analyzeSessionLogs(logDir: string) {
  const result = await client.messages.create({
    model: "claude-sonnet-4-20250514",
    max_tokens: 8096,
    messages: [
      {
        role: "user",
        content: `Analyze the session logs in ${logDir} and identify:
          1. Recurring error patterns
          2. Workflow inefficiencies
          3. Opportunities for automation
          4. Recommended improvements

          Format as structured JSON.`
      }
    ],
    // For structured output
    // response_format: { type: "json_object" }
  });

  return result;
}
```

See `/docs/self-improvement-protocol.md` for full SDK integration details.

---

## Automation Options

### Scheduled Analysis (GitHub Actions)

```yaml
# .github/workflows/log-analysis.yml
name: Weekly Log Analysis
on:
  schedule:
    - cron: '0 9 * * 1'  # Monday 9am
  workflow_dispatch:

jobs:
  analyze:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run Claude Analysis
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
        run: |
          npx claude-code --print "Run /project:analyze-logs week all"
```

### Local Cron

```bash
# Add to crontab for weekly analysis
0 9 * * 1 cd /path/to/project && claude-code -p "Run /project:analyze-logs week all" >> .claude/logs/analysis.log 2>&1
```
