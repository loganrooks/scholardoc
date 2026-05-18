#!/usr/bin/env bash
set -euo pipefail

# reconcile-signal-lifecycle.sh
# Programmatic signal lifecycle reconciliation.
# Reads resolves_signals from PLAN.md frontmatter and updates signal
# lifecycle_state from detected/triaged to remediated.
#
# Usage: reconcile-signal-lifecycle.sh <phase-directory>
# Example: reconcile-signal-lifecycle.sh .planning/phases/38-extensible-sensor-architecture

PHASE_DIR="${1:-}"

if [ -z "$PHASE_DIR" ]; then
  echo "Usage: reconcile-signal-lifecycle.sh <phase-directory>"
  exit 1
fi

if [ ! -d "$PHASE_DIR" ]; then
  echo "Error: Directory not found: $PHASE_DIR"
  exit 1
fi

GSD_TOOLS="$HOME/.claude/get-shit-done/bin/gsd-tools.js"

# KB path resolution -- project-local primary, GSD_HOME middle tier, user-global fallback
if [ -d ".planning/knowledge" ]; then
  KB_DIR=".planning/knowledge"
elif [ -n "${GSD_HOME:-}" ] && [ -d "$GSD_HOME/knowledge" ]; then
  KB_DIR="$GSD_HOME/knowledge"
else
  KB_DIR="$HOME/.gsd/knowledge"
fi
KB_SIGNALS="$KB_DIR/signals"

# Rebuild script path follows GSD_HOME or user-global
if [ -n "${GSD_HOME:-}" ] && [ -x "$GSD_HOME/bin/kb-rebuild-index.sh" ]; then
  KB_REBUILD="$GSD_HOME/bin/kb-rebuild-index.sh"
else
  KB_REBUILD="$HOME/.gsd/bin/kb-rebuild-index.sh"
fi

reconciled=0
plans_processed=0

# Find all PLAN.md files in the phase directory
while IFS= read -r plan; do
  # Extract resolves_signals via gsd-tools frontmatter command
  raw=$(node "$GSD_TOOLS" frontmatter get "$plan" --field resolves_signals --raw 2>/dev/null || echo "")

  # Validate output is a JSON array (not an error object or empty)
  if ! echo "$raw" | grep -q '^\['; then
    continue
  fi

  plans_processed=$((plans_processed + 1))
  plan_basename=$(basename "$plan")
  timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

  # Parse signal IDs from the JSON array
  for sig_id in $(echo "$raw" | node -e "process.stdin.on('data', d => { try { JSON.parse(d).forEach(s => console.log(s)) } catch {} })" 2>/dev/null); do
    # Locate signal file recursively in KB signals directory
    sig_file=$(find "$KB_SIGNALS" -name "${sig_id}.md" 2>/dev/null | head -1)

    if [ -z "$sig_file" ]; then
      echo "  Warning: Signal file not found for ${sig_id}, skipping"
      continue
    fi

    # Check current lifecycle state
    current_state=$(grep "^lifecycle_state:" "$sig_file" 2>/dev/null | head -1 | sed 's/^lifecycle_state:[[:space:]]*//')

    # Only update if in detected or triaged state
    if [ "$current_state" != "detected" ] && [ "$current_state" != "triaged" ]; then
      echo "  Skipping ${sig_id}: already in '${current_state}' state"
      continue
    fi

    # Update lifecycle_state to remediated
    sed -i '' "s/^lifecycle_state:[[:space:]]*${current_state}/lifecycle_state: remediated/" "$sig_file"

    # Append lifecycle_log entry
    log_entry="  - event: remediated
    resolved_by_plan: \"${plan_basename}\"
    approach: \"programmatic reconciliation\"
    timestamp: \"${timestamp}\""

    if grep -q "^lifecycle_log:" "$sig_file"; then
      # Append under existing lifecycle_log (find last entry and add after it)
      # Use awk to find the lifecycle_log section and append after the last list item
      awk -v entry="$log_entry" '
        /^lifecycle_log:/ { in_log=1 }
        in_log && /^[a-zA-Z]/ && !/^lifecycle_log:/ { in_log=0; print entry; }
        in_log && /^---$/ { in_log=0; print entry; }
        { print }
        END { if (in_log) print entry }
      ' "$sig_file" > "${sig_file}.tmp" && mv "${sig_file}.tmp" "$sig_file"
    else
      # Add lifecycle_log before the closing --- of frontmatter
      sed -i '' "/^---$/,/^---$/ {
        /^---$/ {
          x
          s/.*//
          x
          /^---$/ {
            i\\
lifecycle_log:\\
${log_entry}
          }
        }
      }" "$sig_file"
    fi

    echo "  Reconciled: ${sig_id} (${current_state} -> remediated)"
    reconciled=$((reconciled + 1))
  done
done < <(find "$PHASE_DIR" -name '*-PLAN.md' 2>/dev/null)

# Rebuild KB index if any signals were reconciled
if [ "$reconciled" -gt 0 ] && [ -x "$KB_REBUILD" ]; then
  bash "$KB_REBUILD" 2>/dev/null || echo "  Warning: KB index rebuild failed (non-blocking)"
fi

echo "Reconciled ${reconciled} signals from ${plans_processed} plans in ${PHASE_DIR}"
