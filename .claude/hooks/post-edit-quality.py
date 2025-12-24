#!/usr/bin/env python3
"""
Run quality checks after editing Python files.

Runs ruff format and ruff check after Python file edits.
Non-blocking - reports issues as warnings rather than blocking.
"""

import json
import subprocess
import sys
from pathlib import Path


def main():
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)

    tool_input = input_data.get("tool_input", {})
    file_path = tool_input.get("file_path", "")

    # Only process Python files
    if not file_path.endswith(".py"):
        sys.exit(0)

    # Skip cache directories
    skip_dirs = ["__pycache__", ".pytest_cache", ".ruff_cache", ".git", "node_modules"]
    if any(d in file_path for d in skip_dirs):
        sys.exit(0)

    # Check file exists
    if not Path(file_path).exists():
        sys.exit(0)

    messages = []
    has_errors = False

    # Run ruff format
    result = subprocess.run(
        ["uv", "run", "ruff", "format", file_path],
        capture_output=True,
        text=True,
        timeout=30,
    )
    if result.returncode != 0:
        messages.append(f"Format issue: {result.stderr.strip()}")

    # Run ruff check with auto-fix
    result = subprocess.run(
        ["uv", "run", "ruff", "check", "--fix", file_path],
        capture_output=True,
        text=True,
        timeout=30,
    )

    # Check for remaining lint errors
    result = subprocess.run(
        ["uv", "run", "ruff", "check", file_path],
        capture_output=True,
        text=True,
        timeout=30,
    )
    if result.returncode != 0 and result.stdout.strip():
        messages.append(f"Lint issues:\n{result.stdout.strip()}")
        has_errors = True

    # Output result - ALWAYS ADVISORY, never block
    if messages:
        # Categorize severity for informational purposes
        severity = "warning" if has_errors else "info"
        prefix = "⚠️ Lint issues (consider fixing):" if has_errors else "ℹ️ Auto-formatted:"

        output = {
            "decision": "allow",  # Never block - advisory only per SuperClaude framework
            "reason": None,
            "hookSpecificOutput": {
                "hookEventName": "PostToolUse",
                "additionalContext": f"{prefix}\n" + "\n".join(messages),
                "severity": severity,
            },
        }
        print(json.dumps(output))

    sys.exit(0)


if __name__ == "__main__":
    main()
