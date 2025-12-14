#!/usr/bin/env python3
"""
Block dangerous bash patterns before execution.

This hook intercepts Bash tool calls and blocks patterns that could be harmful.
Uses exit code 2 to block, exit code 0 with JSON to allow/deny.

Smart detection:
- Strips heredocs and quoted strings before checking certain patterns
- Distinguishes between "command context" and "text content"
"""

import json
import re
import sys


def strip_heredocs(command: str) -> str:
    """Remove heredoc content from command for pattern matching."""
    # Match heredoc: <<EOF or <<'EOF' or <<"EOF" until EOF
    # This is a simplified version - handles common cases
    result = re.sub(
        r"<<-?\s*['\"]?(\w+)['\"]?.*?\n.*?\1",
        "",
        command,
        flags=re.DOTALL,
    )
    return result


def strip_quoted_strings(command: str) -> str:
    """Remove content inside quotes for pattern matching."""
    # Remove double-quoted strings (but keep the quotes as markers)
    result = re.sub(r'"[^"]*"', '""', command)
    # Remove single-quoted strings
    result = re.sub(r"'[^']*'", "''", result)
    return result


def get_command_context(command: str) -> str:
    """
    Extract the 'command context' - the parts that are actually executed,
    not the content passed as arguments to things like git commit -m.
    """
    # For commands with heredocs, strip the heredoc content
    result = strip_heredocs(command)
    # For quoted strings, strip content (keeps structure)
    result = strip_quoted_strings(result)
    return result


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

    # Get command without heredocs/quoted content for context-sensitive patterns
    command_context = get_command_context(command)

    # Patterns that should only match in command context (not in quoted text)
    # These are commonly mentioned in documentation/comments
    context_sensitive_patterns = [
        (r"(?:^|[;&|])\s*rm\s+.*-[rf]", "Recursive/force delete blocked - use explicit file paths"),
        (r"(?:^|[;&|])\s*rm\s+-[rf]", "Recursive/force delete blocked"),
        (r"(?:^|[;&|])\s*sudo\b", "Sudo blocked"),
        (r"(?:^|[;&|])\s*pip\s+install", "Use 'uv add' instead of pip"),
        (r"(?:^|[;&|])\s*python\s+-m\s+pip", "Use 'uv add' instead of pip"),
        (r"chmod\s+777", "chmod 777 blocked - use specific permissions"),
    ]

    # Patterns that should match anywhere (rarely appear in normal text)
    # These are genuinely dangerous and unlikely to be in commit messages
    always_block_patterns = [
        (r">\s*/dev/", "Writing to device blocked"),
        (r":\s*\(\)\s*\{", "Fork bomb pattern blocked"),
        (r"\|\s*sh\s*$", "Piping to shell blocked"),
        (r"\|\s*bash\s*$", "Piping to bash blocked"),
        (r"\|\s*sh\s*[;&|]", "Piping to shell blocked"),
        (r"\|\s*bash\s*[;&|]", "Piping to bash blocked"),
        (r"\beval\s+[\"'\$]", "Eval execution blocked"),
        (r"git\s+push\s+.*(-f|--force)\b", "Force push blocked - ask human first"),
        (r"git\s+reset\s+--hard", "Hard reset blocked - ask human first"),
        (r"curl\s+[^|]*\|\s*(sh|bash)", "Curl to shell blocked"),
        (r"wget\s+[^|]*\|\s*(sh|bash)", "Wget to shell blocked"),
        (r">\s*/etc/", "Writing to /etc blocked"),
        (r"(?:^|[;&|])\s*dd\s+if=", "dd command blocked"),
        (r"(?:^|[;&|])\s*mkfs\.", "Filesystem format blocked"),
    ]

    # Check context-sensitive patterns against stripped command
    for pattern, reason in context_sensitive_patterns:
        if re.search(pattern, command_context, re.IGNORECASE | re.MULTILINE):
            print(reason, file=sys.stderr)
            sys.exit(2)

    # Check always-block patterns against full command
    for pattern, reason in always_block_patterns:
        if re.search(pattern, command, re.IGNORECASE):
            print(reason, file=sys.stderr)
            sys.exit(2)

    # Allow the command
    sys.exit(0)


if __name__ == "__main__":
    main()
