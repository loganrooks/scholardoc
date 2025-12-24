#!/usr/bin/env python3
"""
Enforce feature branch workflow.

BLOCKS commits to main/master - must use feature branches.
ADVISORY warnings for other operations on main.

This ensures the feature branch workflow is followed:
1. Create feature branch
2. Make commits on feature branch
3. PR to merge into main
"""

import json
import subprocess
import sys


def get_current_branch() -> str:
    """Get the current git branch name."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        return result.stdout.strip() if result.returncode == 0 else ""
    except Exception:
        return ""


def main():
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)

    tool_name = input_data.get("tool_name", "")
    if tool_name != "Bash":
        sys.exit(0)

    tool_input = input_data.get("tool_input", {})
    command = tool_input.get("command", "")

    # Only check git commit commands
    if not command.strip().startswith("git commit"):
        sys.exit(0)

    current_branch = get_current_branch()
    protected_branches = ["main", "master"]

    if current_branch in protected_branches:
        # BLOCK commits to protected branches
        # For PreToolUse blocking: use permissionDecision: "deny" in hookSpecificOutput
        output = {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": f"""🚫 BLOCKED: Cannot commit directly to '{current_branch}'.

Use feature branches for all work:
  git checkout -b feature/<name>
  # make your changes
  git commit -m "feat: description"
  git push -u origin feature/<name>
  gh pr create

Then merge via PR after review.""",
            },
        }
        print(json.dumps(output))
        sys.exit(0)  # Exit 0 when using JSON output

    # Allow commits on feature branches
    sys.exit(0)


if __name__ == "__main__":
    main()
