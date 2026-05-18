#!/usr/bin/env bash
# kb-rebuild-index.sh -- Rebuild the knowledge store index from entry files.
# Atomic: writes to temp file then renames.
# Handles empty knowledge base gracefully.
# Supports project-local KB (.planning/knowledge/) as primary,
# with fallback to GSD_HOME or ~/.gsd/knowledge/.

set -o pipefail

# Project-local KB takes priority, then GSD_HOME, then user-global
if [ -d ".planning/knowledge" ]; then
  KB_DIR=".planning/knowledge"
elif [ -n "${GSD_HOME:-}" ]; then
  KB_DIR="$GSD_HOME/knowledge"
else
  KB_DIR="$HOME/.gsd/knowledge"
fi

INDEX_TMP="$KB_DIR/index.md.tmp"
INDEX="$KB_DIR/index.md"

# Ensure KB exists
mkdir -p "$KB_DIR"

# --- Helper: extract frontmatter field ---
get_field() {
  local file="$1" field="$2"
  grep "^${field}:" "$file" 2>/dev/null | head -1 | sed "s/^${field}:[[:space:]]*//"
}

# --- Helper: extract tags array as comma-separated ---
get_tags() {
  local file="$1"
  grep "^tags:" "$file" 2>/dev/null | head -1 | sed 's/^tags:[[:space:]]*\[//; s/\][[:space:]]*$//' | sed 's/,[ ]*/,/g'
}

# --- Collect entries for a type ---
# Args: type_dir
# Output: lines of "date|file" for sorting
collect_entries() {
  local type_dir="$1"
  if [ ! -d "$type_dir" ]; then
    return
  fi
  while IFS= read -r -d '' file; do
    local status
    status=$(get_field "$file" "status")
    # Skip archived entries; include active and entries with no status field
    if [ "$status" = "archived" ]; then
      continue
    fi
    local created
    created=$(get_field "$file" "created")
    # Use date portion for sorting
    local date_sort="${created:-0000-00-00}"
    echo "${date_sort}|${file}"
  done < <(find "$type_dir" -name '*.md' -print0 2>/dev/null)
}

# --- Build signal rows ---
build_signal_rows() {
  local rows=""
  local count=0
  while IFS='|' read -r date_sort file; do
    [ -z "$file" ] && continue
    local id project severity tags created status
    id=$(get_field "$file" "id")
    project=$(get_field "$file" "project")
    severity=$(get_field "$file" "severity")
    lifecycle_state=$(get_field "$file" "lifecycle_state")
    [ -z "$lifecycle_state" ] && lifecycle_state="detected"
    tags=$(get_tags "$file")
    created=$(get_field "$file" "created")
    status=$(get_field "$file" "status")
    [ -z "$status" ] && status="active"
    local date_display="${created%%T*}"
    rows="${rows}| ${id} | ${project} | ${severity} | ${lifecycle_state} | ${tags} | ${date_display} | ${status} |
"
    count=$((count + 1))
  done < <(collect_entries "$KB_DIR/signals" | sort -t'|' -k1 -r)
  echo "$count"
  printf '%s' "$rows"
}

# --- Build spike rows ---
build_spike_rows() {
  local rows=""
  local count=0
  while IFS='|' read -r date_sort file; do
    [ -z "$file" ] && continue
    local id project outcome tags created status
    id=$(get_field "$file" "id")
    project=$(get_field "$file" "project")
    outcome=$(get_field "$file" "outcome")
    tags=$(get_tags "$file")
    created=$(get_field "$file" "created")
    status=$(get_field "$file" "status")
    [ -z "$status" ] && status="active"
    local date_display="${created%%T*}"
    rows="${rows}| ${id} | ${project} | ${outcome} | ${tags} | ${date_display} | ${status} |
"
    count=$((count + 1))
  done < <(collect_entries "$KB_DIR/spikes" | sort -t'|' -k1 -r)
  echo "$count"
  printf '%s' "$rows"
}

# --- Build lesson rows ---
build_lesson_rows() {
  local rows=""
  local count=0
  while IFS='|' read -r date_sort file; do
    [ -z "$file" ] && continue
    local id project category tags created status
    id=$(get_field "$file" "id")
    project=$(get_field "$file" "project")
    category=$(get_field "$file" "category")
    tags=$(get_tags "$file")
    created=$(get_field "$file" "created")
    status=$(get_field "$file" "status")
    [ -z "$status" ] && status="active"
    local date_display="${created%%T*}"
    rows="${rows}| ${id} | ${project} | ${category} | ${tags} | ${date_display} | ${status} |
"
    count=$((count + 1))
  done < <(collect_entries "$KB_DIR/lessons" | sort -t'|' -k1 -r)
  echo "$count"
  printf '%s' "$rows"
}

# --- Generate index ---

# Capture signal output
signal_output=$(build_signal_rows)
signal_count=$(echo "$signal_output" | head -1)
signal_rows=$(echo "$signal_output" | tail -n +2)

# Capture spike output
spike_output=$(build_spike_rows)
spike_count=$(echo "$spike_output" | head -1)
spike_rows=$(echo "$spike_output" | tail -n +2)

# Conditionally include lessons section only when lessons/ directory exists
has_lessons=false
lesson_count=0
lesson_rows=""
if [ -d "$KB_DIR/lessons" ]; then
  has_lessons=true
  lesson_output=$(build_lesson_rows)
  lesson_count=$(echo "$lesson_output" | head -1)
  lesson_rows=$(echo "$lesson_output" | tail -n +2)
fi

if [ "$has_lessons" = true ]; then
  total=$((signal_count + spike_count + lesson_count))
else
  total=$((signal_count + spike_count))
fi
generated=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# Write to temp file
{
  printf '# Knowledge Store Index\n\n'
  printf '**Generated:** %s\n' "$generated"
  printf '**Total entries:** %s\n\n' "$total"
  printf '## Signals (%s)\n\n' "$signal_count"
  printf '| ID | Project | Severity | Lifecycle | Tags | Date | Status |\n'
  printf '|----|---------|----------|-----------|------|------|--------|\n'
  if [ -n "$signal_rows" ]; then
    printf '%s\n' "$signal_rows"
  fi
  printf '\n## Spikes (%s)\n\n' "$spike_count"
  printf '| ID | Project | Outcome | Tags | Date | Status |\n'
  printf '|----|---------|---------|------|------|--------|\n'
  if [ -n "$spike_rows" ]; then
    printf '%s\n' "$spike_rows"
  fi
  if [ "$has_lessons" = true ]; then
    printf '\n## Lessons (%s)\n\n' "$lesson_count"
    printf '| ID | Project | Category | Tags | Date | Status |\n'
    printf '|----|---------|----------|------|------|--------|\n'
    if [ -n "$lesson_rows" ]; then
      printf '%s\n' "$lesson_rows"
    fi
  fi
  printf '\n'
} > "$INDEX_TMP"

# Atomic rename
mv "$INDEX_TMP" "$INDEX"

if [ "$has_lessons" = true ]; then
  echo "Index rebuilt: ${total} entries (${signal_count} signals, ${spike_count} spikes, ${lesson_count} lessons)"
else
  echo "Index rebuilt: ${total} entries (${signal_count} signals, ${spike_count} spikes)"
fi
exit 0
