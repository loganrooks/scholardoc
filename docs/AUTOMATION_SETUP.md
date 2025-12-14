# ScholarDoc Automation Configuration

> **Purpose:** Maximize Claude Code autonomy while maintaining quality guardrails  
> **Philosophy:** Pre-approve safe operations, enforce quality checks, block dangerous patterns  
> **Last Updated:** December 2025

---

## Overview

This configuration creates a "trust but verify" ecosystem:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     SCHOLARDOC AUTOMATION LAYERS                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Layer 1: PERMISSIONS (Pre-approved operations)                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ ALLOW: Read, Edit(src/**), Bash(uv *), Bash(pytest *), git ops      │   │
│  │ DENY:  rm -rf, sudo, curl|sh, Edit(.env*), force push               │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                              ↓                                              │
│  Layer 2: PRE-TOOL HOOKS (Gate dangerous operations)                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ • Block edits to critical files without confirmation                 │   │
│  │ • Require tests exist before editing implementation                  │   │
│  │ • Validate file paths are within project                            │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                              ↓                                              │
│  Layer 3: POST-TOOL HOOKS (Enforce quality)                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ • Run ruff format after Python edits                                │   │
│  │ • Run ruff check after Python edits                                 │   │
│  │ • Run affected tests after implementation changes                   │   │
│  │ • Validate type hints with mypy                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                              ↓                                              │
│  Layer 4: STOP HOOKS (Verify completeness)                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ • All tests pass?                                                   │   │
│  │ • No linting errors?                                                │   │
│  │ • Documentation updated if needed?                                  │   │
│  │ • CHANGELOG updated for features?                                   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                              ↓                                              │
│  Layer 5: SESSION HOOKS (Learning & continuity)                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ • SessionStart: Load project context, recent decisions              │   │
│  │ • SessionEnd: Log accomplishments, update learnings                 │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## File Structure

```
scholardoc/
├── .claude/
│   ├── settings.json          # Permissions and hook configuration
│   ├── hooks/
│   │   ├── pre-edit-gate.py   # Block edits without tests
│   │   ├── post-edit-quality.py    # Run formatters/linters
│   │   ├── post-edit-test.py       # Run affected tests
│   │   ├── stop-verify.py          # Verify completeness
│   │   ├── session-start.py        # Load context
│   │   ├── session-end.py          # Log learnings
│   │   └── block-dangerous.py      # Block dangerous patterns
│   ├── commands/
│   │   ├── implement.md       # TDD implementation workflow
│   │   ├── explore.md         # Safe exploration mode
│   │   ├── refactor.md        # Safe refactoring workflow
│   │   └── document.md        # Documentation update workflow
│   └── agents/
│       ├── code-reviewer.md   # Review changes before commit
│       └── test-writer.md     # Generate tests
├── CLAUDE.md                  # Project instructions
└── pyproject.toml
```

---

## 1. Permissions Configuration

### .claude/settings.json

```json
{
  "permissions": {
    "allow": [
      "Read(**)",
      
      "Edit(scholardoc/**)",
      "Edit(tests/**)",
      "Edit(spikes/**)",
      "Edit(docs/**/*.md)",
      "Edit(CLAUDE.md)",
      "Edit(README.md)",
      "Edit(CHANGELOG.md)",
      "Edit(pyproject.toml)",
      
      "Bash(uv sync*)",
      "Bash(uv run pytest*)",
      "Bash(uv run ruff*)",
      "Bash(uv run mypy*)",
      "Bash(uv run python spikes/*)",
      "Bash(uv add*)",
      "Bash(uv remove*)",
      
      "Bash(git status*)",
      "Bash(git diff*)",
      "Bash(git log*)",
      "Bash(git add*)",
      "Bash(git commit*)",
      "Bash(git checkout*)",
      "Bash(git branch*)",
      "Bash(git switch*)",
      "Bash(git stash*)",
      "Bash(git show*)",
      
      "Bash(cat *)",
      "Bash(head *)",
      "Bash(tail *)",
      "Bash(wc *)",
      "Bash(find *)",
      "Bash(grep *)",
      "Bash(ls *)",
      "Bash(mkdir *)",
      "Bash(cp *)",
      "Bash(mv scholardoc/* scholardoc/*)",
      "Bash(mv tests/* tests/*)",
      
      "Bash(which *)",
      "Bash(python --version*)",
      "Bash(uv --version*)"
    ],
    
    "deny": [
      "Bash(rm -rf *)",
      "Bash(rm -r *)",
      "Bash(sudo *)",
      "Bash(curl *|*sh)",
      "Bash(wget *|*sh)",
      "Bash(chmod 777 *)",
      "Bash(git push --force*)",
      "Bash(git push -f*)",
      "Bash(git reset --hard*)",
      "Bash(pip install*)",
      
      "Edit(.env*)",
      "Edit(.git/**)",
      "Edit(__pycache__/**)",
      "Edit(*.pyc)",
      "Edit(.claude/settings.json)"
    ]
  },
  
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [{
          "type": "command",
          "command": "python3 .claude/hooks/pre-edit-gate.py"
        }]
      },
      {
        "matcher": "Bash",
        "hooks": [{
          "type": "command",
          "command": "python3 .claude/hooks/block-dangerous.py"
        }]
      }
    ],
    
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [{
          "type": "command",
          "command": "python3 .claude/hooks/post-edit-quality.py"
        }]
      }
    ],
    
    "Stop": [{
      "hooks": [{
        "type": "command",
        "command": "python3 .claude/hooks/stop-verify.py"
      }]
    }],
    
    "SessionStart": [{
      "hooks": [{
        "type": "command",
        "command": "python3 .claude/hooks/session-start.py"
      }]
    }],
    
    "SessionEnd": [{
      "hooks": [{
        "type": "command",
        "command": "python3 .claude/hooks/session-end.py"
      }]
    }]
  }
}
```

---

## 2. Hook Implementations

### Pre-Edit Gate: Enforce TDD

```python
#!/usr/bin/env python3
"""
.claude/hooks/pre-edit-gate.py

Gates edits to implementation files - requires tests to exist first.
"""

import json
import sys
from pathlib import Path

input_data = json.load(sys.stdin)
tool_input = input_data.get("tool_input", {})
file_path = tool_input.get("file_path", "")

# Critical files that need explicit approval
PROTECTED_FILES = [
    "CLAUDE.md",
    "pyproject.toml",
    ".claude/settings.json",
]

# Implementation files that need tests
IMPL_PATTERNS = [
    "scholardoc/readers/",
    "scholardoc/writers/",
    "scholardoc/normalizers/",
]

def check_test_exists(impl_path: str) -> bool:
    """Check if corresponding test file exists."""
    # scholardoc/readers/pdf.py -> tests/unit/readers/test_pdf.py
    path = Path(impl_path)
    
    if not path.suffix == ".py":
        return True  # Not a Python file
    
    if path.name.startswith("__"):
        return True  # __init__.py, etc.
    
    # Construct test path
    relative = path.relative_to("scholardoc")
    test_path = Path("tests/unit") / relative.parent / f"test_{path.name}"
    
    return test_path.exists()


# Check protected files
for protected in PROTECTED_FILES:
    if file_path.endswith(protected):
        output = {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "ask",
                "permissionDecisionReason": f"Editing protected file: {protected}"
            }
        }
        print(json.dumps(output))
        sys.exit(0)

# Check TDD compliance for implementation files
for pattern in IMPL_PATTERNS:
    if pattern in file_path:
        if not check_test_exists(file_path):
            output = {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": f"TDD violation: Write tests first. Expected test file for {file_path}"
                }
            }
            print(json.dumps(output))
            sys.exit(0)

# Allow the edit
sys.exit(0)
```

### Post-Edit Quality: Format and Lint

```python
#!/usr/bin/env python3
"""
.claude/hooks/post-edit-quality.py

Runs formatters and linters after Python file edits.
"""

import json
import sys
import subprocess
from pathlib import Path

input_data = json.load(sys.stdin)
tool_input = input_data.get("tool_input", {})
file_path = tool_input.get("file_path", "")

# Only process Python files
if not file_path.endswith(".py"):
    sys.exit(0)

# Skip test output and cache
if "__pycache__" in file_path or ".pytest_cache" in file_path:
    sys.exit(0)

errors = []

# Run ruff format
result = subprocess.run(
    ["uv", "run", "ruff", "format", file_path],
    capture_output=True,
    text=True
)
if result.returncode != 0:
    errors.append(f"Format failed: {result.stderr}")

# Run ruff check with auto-fix
result = subprocess.run(
    ["uv", "run", "ruff", "check", "--fix", file_path],
    capture_output=True,
    text=True
)

# Run ruff check again to see remaining issues
result = subprocess.run(
    ["uv", "run", "ruff", "check", file_path],
    capture_output=True,
    text=True
)
if result.returncode != 0:
    errors.append(f"Linting errors:\n{result.stdout}")

# Run mypy on the file
result = subprocess.run(
    ["uv", "run", "mypy", file_path, "--ignore-missing-imports"],
    capture_output=True,
    text=True
)
if result.returncode != 0:
    # Don't block on mypy, just report
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PostToolUse",
            "additionalContext": f"Type hints warning:\n{result.stdout}"
        }
    }))

if errors:
    output = {
        "decision": "block",
        "reason": "\n".join(errors)
    }
    print(json.dumps(output))
    sys.exit(2)

sys.exit(0)
```

### Post-Edit Test: Run Affected Tests

```python
#!/usr/bin/env python3
"""
.claude/hooks/post-edit-test.py

Runs tests related to the edited file.
"""

import json
import sys
import subprocess
from pathlib import Path

input_data = json.load(sys.stdin)
tool_input = input_data.get("tool_input", {})
file_path = tool_input.get("file_path", "")

# Only process Python implementation files
if not file_path.endswith(".py"):
    sys.exit(0)

if not file_path.startswith("scholardoc/"):
    sys.exit(0)

# Find corresponding test file
path = Path(file_path)
relative = path.relative_to("scholardoc")
test_path = Path("tests/unit") / relative.parent / f"test_{path.name}"

if not test_path.exists():
    # Also try integration tests
    test_path = Path("tests/integration") / relative.parent / f"test_{path.name}"

if test_path.exists():
    result = subprocess.run(
        ["uv", "run", "pytest", str(test_path), "-v", "--tb=short"],
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        output = {
            "decision": "block",
            "reason": f"Tests failed for {file_path}:\n{result.stdout}\n{result.stderr}"
        }
        print(json.dumps(output))
        sys.exit(2)
    else:
        print(json.dumps({
            "hookSpecificOutput": {
                "hookEventName": "PostToolUse",
                "additionalContext": f"Tests passed for {file_path}"
            }
        }))

sys.exit(0)
```

### Block Dangerous Patterns

```python
#!/usr/bin/env python3
"""
.claude/hooks/block-dangerous.py

Blocks dangerous bash patterns that might slip through permissions.
"""

import json
import sys
import re

input_data = json.load(sys.stdin)
tool_name = input_data.get("tool_name", "")
tool_input = input_data.get("tool_input", {})

if tool_name != "Bash":
    sys.exit(0)

command = tool_input.get("command", "")

DANGEROUS_PATTERNS = [
    (r'rm\s+.*-[rf]', "Recursive/force delete"),
    (r'>\s*/dev/', "Writing to device"),
    (r':\s*\(\)\s*{', "Fork bomb pattern"),
    (r'\|\s*sh\b', "Piping to shell"),
    (r'\|\s*bash\b', "Piping to bash"),
    (r'eval\s', "Eval execution"),
    (r'git\s+push.*(-f|--force)', "Force push"),
    (r'git\s+reset\s+--hard', "Hard reset"),
    (r'pip\s+install', "Use uv instead of pip"),
    (r'python\s+-m\s+pip', "Use uv instead of pip"),
]

for pattern, reason in DANGEROUS_PATTERNS:
    if re.search(pattern, command, re.IGNORECASE):
        output = {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": f"Blocked: {reason}"
            }
        }
        print(json.dumps(output))
        sys.exit(0)

sys.exit(0)
```

### Stop Verify: Check Completeness

```python
#!/usr/bin/env python3
"""
.claude/hooks/stop-verify.py

Verifies work is complete before stopping.
"""

import json
import sys
import subprocess

# Run all tests
result = subprocess.run(
    ["uv", "run", "pytest", "--tb=short", "-q"],
    capture_output=True,
    text=True
)

issues = []

if result.returncode != 0:
    issues.append(f"Tests failing:\n{result.stdout}")

# Run linter on whole project
result = subprocess.run(
    ["uv", "run", "ruff", "check", "scholardoc/", "tests/"],
    capture_output=True,
    text=True
)

if result.returncode != 0:
    issues.append(f"Linting errors:\n{result.stdout}")

# Check for uncommitted changes
result = subprocess.run(
    ["git", "status", "--porcelain"],
    capture_output=True,
    text=True
)

if result.stdout.strip():
    # There are uncommitted changes - remind to commit
    issues.append(f"Uncommitted changes:\n{result.stdout}\nConsider committing your work.")

if issues:
    output = {
        "decision": "block",
        "reason": "Before stopping, please address:\n\n" + "\n\n".join(issues)
    }
    print(json.dumps(output))
    sys.exit(0)

# All good
print(json.dumps({
    "continue": True,
    "systemMessage": "All checks passed. Safe to stop."
}))
sys.exit(0)
```

### Session Start: Load Context

```python
#!/usr/bin/env python3
"""
.claude/hooks/session-start.py

Loads project context at session start.
"""

import json
import sys
from pathlib import Path
from datetime import datetime

context_parts = []

# Load recent decisions from decision log
decision_log = Path("docs/decisions/DECISION_LOG.md")
if decision_log.exists():
    content = decision_log.read_text()
    # Get last 5 decisions
    lines = content.split("\n")
    recent = [l for l in lines if l.startswith("- ")][-5:]
    if recent:
        context_parts.append("Recent decisions:\n" + "\n".join(recent))

# Load current phase from ROADMAP
roadmap = Path("ROADMAP.md")
if roadmap.exists():
    content = roadmap.read_text()
    # Find current phase marker
    if "**CURRENT**" in content or "[x]" in content.lower():
        context_parts.append("Check ROADMAP.md for current phase")

# Load any TODOs from previous session
session_log = Path(".claude/session_log.md")
if session_log.exists():
    content = session_log.read_text()
    if "TODO:" in content or "NEXT:" in content:
        context_parts.append(f"Previous session notes:\n{content[-500:]}")

# Check test status
import subprocess
result = subprocess.run(
    ["uv", "run", "pytest", "--collect-only", "-q"],
    capture_output=True,
    text=True
)
test_count = result.stdout.count("test")
context_parts.append(f"Test suite: {test_count} tests collected")

# Output context
output = {
    "hookSpecificOutput": {
        "hookEventName": "SessionStart",
        "additionalContext": "\n\n".join(context_parts) if context_parts else "Ready to work on ScholarDoc."
    }
}

print(json.dumps(output))
sys.exit(0)
```

### Session End: Log Learnings

```python
#!/usr/bin/env python3
"""
.claude/hooks/session-end.py

Logs session accomplishments and learnings.
"""

import json
import sys
from pathlib import Path
from datetime import datetime

# Create session log entry
log_dir = Path(".claude/logs")
log_dir.mkdir(parents=True, exist_ok=True)

log_file = log_dir / f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"

# Get git diff summary
import subprocess
result = subprocess.run(
    ["git", "diff", "--stat", "HEAD~1..HEAD"],
    capture_output=True,
    text=True
)
diff_summary = result.stdout if result.returncode == 0 else "No commits this session"

# Get recent commits
result = subprocess.run(
    ["git", "log", "--oneline", "-5"],
    capture_output=True,
    text=True
)
recent_commits = result.stdout if result.returncode == 0 else "No recent commits"

log_content = f"""# Session Log - {datetime.now().isoformat()}

## Changes
{diff_summary}

## Recent Commits
{recent_commits}

## Notes
(Add any learnings or TODOs here)

"""

log_file.write_text(log_content)

print(json.dumps({
    "continue": True,
    "systemMessage": f"Session logged to {log_file}"
}))
sys.exit(0)
```

---

## 3. CLAUDE.md Enforcement Section

Add this to the main CLAUDE.md:

```markdown
## Automated Enforcement

This project uses hooks for automated quality control. The following are enforced:

### Pre-Edit Gates
- **TDD Required**: Cannot edit `scholardoc/` implementation files without corresponding test file
- **Protected Files**: CLAUDE.md, pyproject.toml, settings.json require confirmation

### Post-Edit Checks (Automatic)
- `ruff format` runs after every Python edit
- `ruff check --fix` runs after every Python edit  
- Related tests run after implementation changes
- Mypy type checking (warnings only)

### Stop Verification
Before stopping, the system verifies:
- All tests pass
- No linting errors
- Reminds about uncommitted changes

### What This Means for You (Claude)
1. Write tests FIRST for new functionality
2. Don't try to edit protected files without good reason
3. If post-edit checks fail, fix the issues before continuing
4. If stop verification fails, address the issues

### Bypassing (Emergency Only)
If hooks are blocking legitimate work:
1. Explain why in the conversation
2. Human can temporarily disable hooks
3. Document why bypass was needed

## Workflow Commands

Use these slash commands for structured workflows:

- `/project:implement <feature>` - TDD implementation workflow
- `/project:explore <topic>` - Safe exploration (no edits)
- `/project:refactor <target>` - Safe refactoring with tests
- `/project:document <what>` - Update documentation

## Quality Standards

### Code Style
- Follow ruff defaults (enforced by hooks)
- Type hints required for public APIs
- Docstrings required for public functions

### Testing
- Unit tests in `tests/unit/`
- Integration tests in `tests/integration/`  
- Minimum 80% coverage for new code
- Test file mirrors implementation structure

### Documentation
- Update relevant docs when changing behavior
- Keep QUESTIONS.md current with open questions
- Log decisions in docs/decisions/
```

---

## 4. Workflow Commands

### /project:implement

```markdown
---
description: TDD implementation workflow
---

# Implement: $ARGUMENTS

Follow this TDD workflow:

## Step 1: Understand
- What problem does this solve?
- What are the inputs/outputs?
- What are the edge cases?

## Step 2: Write Tests First
Create test file in `tests/unit/` or `tests/integration/`
Write tests for:
- Happy path
- Edge cases
- Error conditions

Run tests to confirm they fail:
```bash
uv run pytest tests/unit/path/to/test_file.py -v
```

## Step 3: Implement Minimum Code
Write just enough code to pass tests.
The post-edit hooks will run automatically.

## Step 4: Refactor
With passing tests, improve the code:
- Extract functions
- Improve naming
- Add type hints

## Step 5: Document
- Add docstrings
- Update README if needed
- Update CHANGELOG

## Step 6: Commit
```bash
git add -A
git commit -m "feat: $ARGUMENTS"
```
```

### /project:explore

```markdown
---
description: Safe exploration mode - read only
---

# Explore: $ARGUMENTS

**MODE: READ-ONLY EXPLORATION**

In this mode:
- ✅ Read any files
- ✅ Run analysis commands
- ✅ Run tests
- ❌ No editing files
- ❌ No creating files

## Your Task
Explore and understand: $ARGUMENTS

Report back with:
1. What you found
2. How it works
3. Potential issues
4. Recommendations

Only after exploration is complete, ask if I want to proceed with changes.
```

### /project:refactor

```markdown
---
description: Safe refactoring workflow
---

# Refactor: $ARGUMENTS

## Pre-Refactor Checklist
1. [ ] All tests pass before starting
2. [ ] Understand what's being refactored
3. [ ] Have a clear goal

## Refactoring Steps

### Step 1: Verify Tests Pass
```bash
uv run pytest -v
```
If tests fail, fix them first.

### Step 2: Make One Small Change
Refactor incrementally. One logical change at a time.

### Step 3: Run Tests
After each change, tests must pass.

### Step 4: Commit
Commit after each successful refactor step:
```bash
git add -A
git commit -m "refactor: <what changed>"
```

## Rules
- NEVER change behavior while refactoring
- NEVER skip tests between changes
- If tests fail, revert and try smaller change
```

---

## 5. Self-Improvement Integration

### Weekly Learning Hook

Add to CI/CD or run manually:

```bash
#!/bin/bash
# .claude/scripts/weekly-review.sh

echo "=== Weekly Review ==="

# Analyze session logs
echo "## Session Analysis"
find .claude/logs -name "*.md" -mtime -7 -exec cat {} \; | \
  grep -E "(TODO|LEARN|ERROR|ISSUE)" | head -20

# Check for repeated patterns
echo "## Repeated Test Failures"
find .claude/logs -name "*.md" -mtime -7 -exec grep -l "Tests failed" {} \;

# Suggest CLAUDE.md updates
echo "## Suggested Rules"
echo "Review session logs for patterns that should become rules"
```

### Decision Logging

Create `docs/decisions/DECISION_LOG.md`:

```markdown
# Decision Log

Track decisions made during development. Format:
- [DATE] DECISION - RATIONALE

## December 2025

- [2025-12-14] Use PyMuPDF for PDF extraction - Best balance of speed and features (pending spike validation)
- [2025-12-14] TDD enforcement via hooks - Prevents implementation without tests
- [2025-12-14] Footnotes deferred to Phase 2 - Complex, not MVP
```

---

## 6. Summary: What Gets Automated

| Aspect | Automation Level | Human Intervention |
|--------|------------------|-------------------|
| **Read operations** | Fully auto-approved | None |
| **Edit src/tests** | Auto-approved + quality checks | Only if checks fail |
| **Edit docs** | Auto-approved | None |
| **Run tests/lint** | Fully auto-approved | None |
| **Git operations** | Auto-approved (except force push) | None |
| **Edit protected files** | Requires confirmation | Yes |
| **Dangerous bash** | Blocked | Must request bypass |
| **TDD compliance** | Enforced by hooks | Only if bypass needed |
| **Code quality** | Auto-fixed when possible | Only unfixable issues |
| **Session continuity** | Auto-logged | Review weekly |

### Expected Human Intervention

**Rarely (emergency only):**
- Bypassing TDD for hotfix
- Force push after rebase
- Editing settings.json

**Occasionally:**
- Reviewing weekly learnings
- Approving protected file changes
- Resolving unfixable lint errors

**Never:**
- Approving reads
- Approving test runs
- Approving standard edits
- Approving git status/diff/log
