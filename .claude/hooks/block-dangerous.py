#!/usr/bin/env python3
"""
Block dangerous bash patterns before execution.

This hook intercepts Bash tool calls and blocks patterns that could be harmful.
Uses exit code 2 to block, exit code 0 with JSON to allow/deny.
"""

import json
import re
import sys


def main():
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)  # Allow if we can't parse input

    tool_name = input_data.get("tool_name", "")
    if tool_name != "Bash":
        sys.exit(0)

    tool_input = input_data.get("tool_input", {})
    command = tool_input.get("command", "")

    # Dangerous patterns to block
    dangerous_patterns = [
        (r"rm\s+.*-[rf]", "Recursive/force delete blocked - use explicit file paths"),
        (r"rm\s+-[rf]", "Recursive/force delete blocked"),
        (r">\s*/dev/", "Writing to device blocked"),
        (r":\s*\(\)\s*\{", "Fork bomb pattern blocked"),
        (r"\|\s*sh\b", "Piping to shell blocked"),
        (r"\|\s*bash\b", "Piping to bash blocked"),
        (r"\beval\s", "Eval execution blocked"),
        (r"git\s+push.*(-f|--force)", "Force push blocked - ask human first"),
        (r"git\s+reset\s+--hard", "Hard reset blocked - ask human first"),
        (r"\bsudo\b", "Sudo blocked"),
        (r"pip\s+install", "Use 'uv add' instead of pip"),
        (r"python\s+-m\s+pip", "Use 'uv add' instead of pip"),
        (r"curl.*\|\s*(sh|bash)", "Curl to shell blocked"),
        (r"wget.*\|\s*(sh|bash)", "Wget to shell blocked"),
        (r"chmod\s+777", "chmod 777 blocked - use specific permissions"),
        (r">\s*/etc/", "Writing to /etc blocked"),
        (r"dd\s+if=", "dd command blocked"),
        (r"mkfs\.", "Filesystem format blocked"),
    ]

    for pattern, reason in dangerous_patterns:
        if re.search(pattern, command, re.IGNORECASE):
            # Exit code 2 blocks the tool with error message
            print(reason, file=sys.stderr)
            sys.exit(2)

    # Allow the command
    sys.exit(0)


if __name__ == "__main__":
    main()
