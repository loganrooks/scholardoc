---
description: Enhanced session logging hook for self-improvement feedback
hooks:
  - event: Stop
    script: |
      #!/bin/bash
      # Enhanced Session Logger Hook
      # Captures rich session data for self-improvement cycles

      SESSION_LOG_DIR=".claude/logs/sessions"
      SIGNAL_DIR=".claude/logs/signals"
      TIMESTAMP=$(date +%Y%m%d_%H%M%S)
      SESSION_LOG="$SESSION_LOG_DIR/session_${TIMESTAMP}.md"

      mkdir -p "$SESSION_LOG_DIR"
      mkdir -p "$SIGNAL_DIR"

      # Gather metrics
      GIT_BRANCH=$(git branch --show-current 2>/dev/null || echo "unknown")
      GIT_STATUS=$(git status --porcelain 2>/dev/null | wc -l)
      STAGED_FILES=$(git diff --cached --name-only 2>/dev/null | wc -l)
      UNSTAGED_FILES=$(git diff --name-only 2>/dev/null | wc -l)

      # Check for lint/test status (project-specific commands)
      LINT_ERRORS=0
      TEST_STATUS="unknown"

      # Try common lint commands
      if [ -f "package.json" ] && grep -q '"lint"' package.json 2>/dev/null; then
        LINT_ERRORS=$(npm run lint 2>&1 | grep -cE "(error|warning)" || echo "0")
      elif [ -f "pyproject.toml" ] || [ -f "setup.py" ]; then
        LINT_ERRORS=$(ruff check . 2>&1 | grep -cE "^[^:]+:[0-9]+" || echo "0")
      fi

      # Count files modified in session (approximation via recent git activity)
      RECENT_COMMITS=$(git log --oneline --since="1 hour ago" 2>/dev/null | wc -l)

      # Detect potential issues (signals for self-improvement)
      ISSUES=()
      WARNINGS=()

      # Check for uncommitted changes at session end
      if [ "$GIT_STATUS" -gt 5 ]; then
        WARNINGS+=("Many uncommitted changes: $GIT_STATUS files")
      fi

      # Check for lint errors
      if [ "$LINT_ERRORS" -gt 0 ]; then
        ISSUES+=("Lint errors present: $LINT_ERRORS")
      fi

      # Check for TODO comments added this session
      TODO_COUNT=$(git diff HEAD 2>/dev/null | grep -c "^\+.*TODO" || echo "0")
      if [ "$TODO_COUNT" -gt 0 ]; then
        WARNINGS+=("TODOs added this session: $TODO_COUNT")
      fi

      # Check for large commits (might indicate missing incremental commits)
      LAST_COMMIT_SIZE=$(git diff HEAD~1 --stat 2>/dev/null | tail -1 | grep -oE "[0-9]+ file" | grep -oE "[0-9]+" || echo "0")
      if [ "$LAST_COMMIT_SIZE" -gt 10 ]; then
        WARNINGS+=("Large commit detected: $LAST_COMMIT_SIZE files (consider smaller commits)")
      fi

      # Write enhanced session log
      cat > "$SESSION_LOG" << EOF
      # Session Log: $TIMESTAMP

      ## Session Metrics

      | Metric | Value |
      |--------|-------|
      | Timestamp | $(date '+%Y-%m-%d %H:%M:%S') |
      | Branch | $GIT_BRANCH |
      | Duration | [Calculate from start if available] |
      | Files Modified | $GIT_STATUS |
      | Staged | $STAGED_FILES |
      | Unstaged | $UNSTAGED_FILES |
      | Recent Commits | $RECENT_COMMITS |
      | Lint Errors | $LINT_ERRORS |
      | TODOs Added | $TODO_COUNT |

      ## Git Activity

      ### Recent Commits
      \`\`\`
      $(git log --oneline -5 2>/dev/null || echo "No commits")
      \`\`\`

      ### Changed Files
      \`\`\`
      $(git status --short 2>/dev/null || echo "No changes")
      \`\`\`

      ## Issues Detected
      $(if [ ${#ISSUES[@]} -eq 0 ]; then echo "None"; else printf '%s\n' "${ISSUES[@]}" | sed 's/^/- /'; fi)

      ## Warnings
      $(if [ ${#WARNINGS[@]} -eq 0 ]; then echo "None"; else printf '%s\n' "${WARNINGS[@]}" | sed 's/^/- /'; fi)

      ## Session Handoff

      **Remember**: Update \`session_handoff\` memory with:
      - What was worked on
      - What was accomplished
      - What's still in progress
      - Key decisions made
      - Blockers/questions
      - Recommended next steps

      EOF

      # If issues were detected, create a signal file for self-improvement
      if [ ${#ISSUES[@]} -gt 0 ]; then
        SIGNAL_FILE="$SIGNAL_DIR/signal_${TIMESTAMP}.md"
        cat > "$SIGNAL_FILE" << EOF
      # Signal: Session Issues Detected

      **Type**: INTERNAL
      **Severity**: MEDIUM
      **Timestamp**: $(date '+%Y-%m-%d %H:%M:%S')
      **Branch**: $GIT_BRANCH

      ## Issues
      $(printf '%s\n' "${ISSUES[@]}" | sed 's/^/- /')

      ## Warnings
      $(printf '%s\n' "${WARNINGS[@]}" | sed 's/^/- /')

      ## Context
      - Session log: $SESSION_LOG
      - Recent commits: $RECENT_COMMITS

      ## Suggested Action
      Run \`/project:diagnose session-issues\` to analyze patterns.

      EOF
        echo "Signal created: $SIGNAL_FILE"
      fi

      echo "Session logged: $SESSION_LOG"
---

# Enhanced Session Logger Hook

This hook captures rich session data when Claude Code sessions end.

## Data Captured

| Category | Metrics |
|----------|---------|
| Git State | Branch, status, staged/unstaged files, recent commits |
| Quality | Lint errors, TODO count, commit sizes |
| Signals | Issues, warnings, patterns detected |

## Signal Generation

When issues are detected, a signal file is automatically created in `.claude/logs/signals/` for processing by `/project:improve`.

## Signal Types Detected

| Signal | Trigger | Action |
|--------|---------|--------|
| Uncommitted changes | >5 files at session end | Warning |
| Lint errors | Any lint failures | Issue |
| TODO accumulation | TODOs added in session | Warning |
| Large commits | >10 files in single commit | Warning |

## Output Files

- **Session logs**: `.claude/logs/sessions/session_YYYYMMDD_HHMMSS.md`
- **Signals**: `.claude/logs/signals/signal_YYYYMMDD_HHMMSS.md`

## Integration

This hook integrates with:
- `/project:improve` - Processes signals
- `/project:diagnose` - Analyzes patterns
- `/project:resume` - Loads session context
