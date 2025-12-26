---
description: Create a GitHub PR with AI-generated description from commits and changes
allowed-tools: Bash(gh:*), Bash(git:*), Bash(jq:*), Read, Write, Task, TodoWrite
argument-hint: [--base <branch>] [--draft] [--title "Custom title"]
---

# Create PR: $ARGUMENTS

**MODE: INTELLIGENT PR CREATION**

Create a GitHub pull request with an auto-generated description based on commits, changes, and project context.

---

## Phase 0: Parse Arguments

```
FLAGS:
  --base <branch>    : Target branch (default: main)
  --draft            : Create as draft PR
  --title "..."      : Override auto-generated title
  --no-review        : Skip self-review before creating
```

---

## Phase 1: Gather Context

### 1.1 Verify Branch State

```bash
# Current branch
git branch --show-current

# Check for uncommitted changes
git status --porcelain

# Check if branch is pushed
git rev-parse --abbrev-ref --symbolic-full-name @{upstream} 2>/dev/null || echo "NOT_PUSHED"
```

**STOP if**:
- On main/master branch
- Has uncommitted changes (offer to commit first)
- Branch not pushed (offer to push)

### 1.2 Get Commit History

```bash
# Commits since divergence from base
git log origin/main..HEAD --oneline

# Detailed commit messages
git log origin/main..HEAD --format="## %s%n%n%b"
```

### 1.3 Get Diff Summary

```bash
# Files changed
git diff origin/main --stat

# Full diff for analysis
git diff origin/main
```

### 1.4 Check for Related Issues

Look for issue references in commits or branch name:
- Branch: `feature/123-add-auth` → Issue #123
- Commits: "Fixes #45" → Issue #45

```bash
# Extract issue numbers from branch name
git branch --show-current | grep -oE '[0-9]+'

# Extract from commit messages
git log origin/main..HEAD --format="%s %b" | grep -oE '#[0-9]+' | sort -u
```

---

## Phase 2: Generate PR Content

### 2.1 Analyze Changes with Agent

```
Task: documentation-reviewer agent (repurposed for PR description)

Prompt:
---
Generate a pull request description based on these changes:

**Branch**: [current_branch]
**Target**: [base_branch]

**Commits**:
[commit list with messages]

**Files Changed**:
[file list with stats]

**Diff Summary**:
[condensed diff or key changes]

**Related Issues**: [if any]

Generate:
1. A concise title (if not provided)
2. A summary section (2-3 bullet points of what this PR does)
3. A "Changes" section (what was modified)
4. A "Test Plan" section (how to verify these changes work)
5. Any breaking changes or migration notes

Format as GitHub-flavored markdown.
---
```

### 2.2 Structure PR Body

```markdown
## Summary
[2-3 bullets describing what this PR accomplishes]

## Changes
[List of meaningful changes, grouped logically]

## Test Plan
- [ ] [How to test change 1]
- [ ] [How to test change 2]

## Related Issues
[Closes #X / Fixes #Y / Related to #Z]

---
*PR description generated with AI assistance*
```

---

## Phase 3: Self-Review (Optional)

### 3.1 Run Quick Code Review

Unless `--no-review` flag:

```
Task: code-reviewer agent

Prompt: Review these changes for obvious issues before creating PR
[Include diff]

Quick check for:
- Obvious bugs
- Security issues
- Missing tests
- Debug code left in
```

### 3.2 Address Blockers

If review finds **critical** issues:
- Report findings
- Ask user whether to proceed anyway or fix first

---

## Phase 4: Create PR

### 4.1 Push Branch (if needed)

```bash
git push -u origin $(git branch --show-current)
```

### 4.2 Create PR via gh CLI

```bash
gh pr create \
  --base [BASE_BRANCH] \
  --title "[TITLE]" \
  --body "$(cat <<'EOF'
[GENERATED_BODY]
EOF
)" \
  [--draft if flag set]
```

### 4.3 Add Labels (if detected)

Based on changes, suggest labels:
- `feat:` commits → `enhancement`
- `fix:` commits → `bug`
- `docs:` commits → `documentation`
- `test:` commits → `testing`

```bash
gh pr edit [PR_NUMBER] --add-label "enhancement,needs-review"
```

---

## Phase 5: Report

### 5.1 Success Output

```markdown
## ✅ PR Created

**PR**: #[NUMBER] - [TITLE]
**URL**: [PR_URL]
**Base**: [BASE] ← **Head**: [HEAD]
**Status**: [Draft/Ready for Review]

### Summary
[Brief description]

### Pre-Review Check
[Results of self-review if run]

### Next Steps
- [ ] Request reviewers
- [ ] Add additional labels if needed
- [ ] Monitor CI checks
```

---

## Integration with Other Commands

### From `/project:auto`

After implementation phase completes:
```
→ Create feature branch (if not exists)
→ Commit changes
→ /project:create-pr --no-review (already reviewed)
```

### Before `/project:review-pr`

```
/project:create-pr
→ Posts PR
→ Can then run /project:review-pr [number] for self-review on GitHub
```

---

## Examples

```bash
# Basic PR creation
/project:create-pr

# Specify target branch
/project:create-pr --base develop

# Create as draft
/project:create-pr --draft

# Custom title
/project:create-pr --title "Add user authentication system"

# Skip self-review
/project:create-pr --no-review
```

---

## Error Handling

| Error | Action |
|-------|--------|
| On main branch | Exit with message |
| Uncommitted changes | Offer to commit |
| Branch not pushed | Push automatically |
| No commits ahead of base | Exit with message |
| PR already exists | Show existing PR URL |
| gh auth failed | Guide to `gh auth login` |
