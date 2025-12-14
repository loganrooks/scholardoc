#!/usr/bin/env python3
"""
Verify work is complete before stopping.

Checks:
1. All tests pass
2. No linting errors
3. Reminds about uncommitted changes

This hook is advisory - it won't block stopping but will provide warnings.
"""

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path


def run_command(cmd: list[str], timeout: int = 60) -> tuple[int, str, str]:
    """Run a command and return (returncode, stdout, stderr)."""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return 1, "", "Command timed out"
    except FileNotFoundError:
        return 1, "", f"Command not found: {cmd[0]}"


def main():
    issues = []
    warnings = []

    # Check if tests pass
    returncode, stdout, stderr = run_command(
        ["uv", "run", "pytest", "--tb=short", "-q"], timeout=120
    )
    if returncode != 0:
        # Only report if there are actual test failures, not just no tests
        if "no tests ran" not in stdout.lower() and "collected 0 items" not in stdout:
            issues.append(f"Tests failing:\n{stdout[:500]}")
        elif "error" in stderr.lower():
            issues.append(f"Test error:\n{stderr[:500]}")

    # Check for lint errors
    returncode, stdout, stderr = run_command(
        ["uv", "run", "ruff", "check", "scholardoc/", "tests/", "spikes/"]
    )
    if returncode != 0 and stdout.strip():
        issues.append(f"Lint errors:\n{stdout[:500]}")

    # Check for uncommitted changes
    returncode, stdout, stderr = run_command(["git", "status", "--porcelain"])
    if stdout.strip():
        changed_files = stdout.strip().split("\n")
        file_count = len(changed_files)
        warnings.append(
            f"Uncommitted changes ({file_count} files). Consider committing your work."
        )

    # Log session end
    log_dir = Path(".claude/logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"

    # Get summary of changes
    _, diff_stat, _ = run_command(["git", "diff", "--stat", "HEAD"])
    _, recent_commits, _ = run_command(["git", "log", "--oneline", "-5"])

    log_content = f"""# Session Log - {datetime.now().isoformat()}

## Status
- Issues: {len(issues)}
- Warnings: {len(warnings)}

## Changes Since Last Commit
```
{diff_stat[:1000] if diff_stat else "No changes"}
```

## Recent Commits
```
{recent_commits[:500] if recent_commits else "No recent commits"}
```

## Issues Found
{chr(10).join(f"- {i}" for i in issues) if issues else "None"}

## Warnings
{chr(10).join(f"- {w}" for w in warnings) if warnings else "None"}
"""

    log_file.write_text(log_content)

    # Build output
    all_messages = issues + warnings

    if all_messages:
        output = {
            "continue": True,  # Don't block stopping, just inform
            "systemMessage": "Before stopping:\n\n" + "\n\n".join(all_messages),
            "hookSpecificOutput": {
                "hookEventName": "Stop",
                "additionalContext": f"Session logged to {log_file}",
            },
        }
        print(json.dumps(output))
    else:
        output = {
            "continue": True,
            "systemMessage": f"All checks passed. Session logged to {log_file}",
        }
        print(json.dumps(output))

    sys.exit(0)


if __name__ == "__main__":
    main()
