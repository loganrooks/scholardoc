#!/usr/bin/env python3
"""
Pre-commit reminder hook.

Provides a gentle reminder to check quality before committing.
NEVER blocks - just provides advisory feedback.
"""

import json
import sys


def main():
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)

    tool_input = input_data.get("tool_input", {})
    command = tool_input.get("command", "")

    # Only trigger on git commit commands
    if not command.strip().startswith("git commit"):
        sys.exit(0)

    # Provide advisory reminder - NEVER block
    # For PreToolUse: use permissionDecision in hookSpecificOutput
    output = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "allow",
            "permissionDecisionReason": """Pre-commit checklist reminder:
• Have you run the tests? (uv run pytest)
• Have you checked for lint errors? (uv run ruff check .)
• Are you committing the right files? (git status)
• Is your commit message descriptive?

This is just a reminder - proceeding with commit.""",
        },
    }
    print(json.dumps(output))
    sys.exit(0)


if __name__ == "__main__":
    main()
