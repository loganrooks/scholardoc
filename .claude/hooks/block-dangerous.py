#!/usr/bin/env python3
"""
Block dangerous bash patterns before execution.

MINIMAL blocking - only the truly catastrophic stuff.
Permissions in settings.json handle the rest.
"""

import json
import re
import sys


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

    # ONLY block patterns that are catastrophic AND unambiguous
    # These patterns must be at the START of the command (not in args/strings)
    catastrophic_patterns = [
        # Recursive delete at root or with force - only at command start
        (r"^\s*rm\s+-rf\s+/\s*$", "Blocked: rm -rf /"),
        (r"^\s*rm\s+-rf\s+/\*", "Blocked: rm -rf /*"),
        (r"^\s*rm\s+-rf\s+~\s*$", "Blocked: rm -rf ~"),
        # Fork bomb
        (r":\s*\(\)\s*\{.*:\s*\|", "Blocked: fork bomb"),
        # Direct pipe to shell from curl/wget (remote code execution)
        (r"^\s*curl\s+.*\|\s*(?:sudo\s+)?(?:ba)?sh", "Blocked: curl pipe to shell"),
        (r"^\s*wget\s+.*\|\s*(?:sudo\s+)?(?:ba)?sh", "Blocked: wget pipe to shell"),
        # Writing to critical system paths
        (r">\s*/dev/[sh]d[a-z]", "Blocked: write to disk device"),
        # Disk operations
        (r"^\s*mkfs\.", "Blocked: filesystem format"),
        (r"^\s*dd\s+.*of=/dev/[sh]d", "Blocked: dd to disk"),
    ]

    for pattern, reason in catastrophic_patterns:
        if re.search(pattern, command, re.IGNORECASE):
            print(reason, file=sys.stderr)
            sys.exit(2)

    # Allow everything else - permissions handle the rest
    sys.exit(0)


if __name__ == "__main__":
    main()
