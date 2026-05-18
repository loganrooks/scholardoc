<purpose>
Execute small, ad-hoc tasks with GSD guarantees (atomic commits, STATE.md tracking) while skipping optional agents (research, plan-checker, verifier). Quick mode spawns gsd-planner (quick mode) + gsd-executor(s), tracks tasks in `.planning/quick/`, and updates STATE.md's "Quick Tasks Completed" table.
</purpose>

<required_reading>
Read all files referenced by the invoking prompt's execution_context before starting.
</required_reading>

<process>
**Step 1: Get task description**

Prompt user interactively for the task description:

```
AskUserQuestion(
  header: "Quick Task",
  question: "What do you want to do?",
  followUp: null
)
```

Store response as `$DESCRIPTION`.

If empty, re-prompt: "Please provide a task description."

---

**Step 2: Initialize**

```bash
INIT=$(node ./.claude/get-shit-done/bin/gsd-tools.js init quick "$DESCRIPTION")
```

Parse JSON for: `planner_model`, `executor_model`, `commit_docs`, `next_num`, `slug`, `date`, `timestamp`, `quick_dir`, `task_dir`, `roadmap_exists`, `planning_exists`.

**If `roadmap_exists` is false:** Error — Quick mode requires an active project with ROADMAP.md. Run `/gsd:new-project` first.

Quick tasks can run mid-phase - validation only checks ROADMAP.md exists, not phase status.

---

**Step 3: Create task directory**

```bash
mkdir -p "${task_dir}"
```

---

**Step 4: Create quick task directory**

Create the directory for this quick task:

```bash
QUICK_DIR=".planning/quick/${next_num}-${slug}"
mkdir -p "$QUICK_DIR"
```

Report to user:
```
Creating quick task ${next_num}: ${DESCRIPTION}
Directory: ${QUICK_DIR}
```

Store `$QUICK_DIR` for use in orchestration.

---

**Step 4b: Assess task complexity**

<!-- Complexity gate: routes trivial tasks to inline execution, complex tasks to planner+executor -->
<!--                                                                                             -->
<!-- TRIVIAL examples (inline execution):                                                        -->
<!--   "fix typo in README"              - short, single concern, no keywords                    -->
<!--   "update version to 1.5.0"         - short, single concern                                -->
<!--   "add .gitignore entry"            - short, single concern                                 -->
<!--   "remove unused import in utils"   - short, single concern                                 -->
<!--                                                                                             -->
<!-- COMPLEX examples (planner+executor):                                                        -->
<!--   "update the tests and fix the linting errors"  - multi-concern ("and" joining two tasks)  -->
<!--   "refactor auth module"                         - complexity keyword ("refactor")           -->
<!--   "integrate Stripe webhooks with the order service" - complexity keyword ("integrate")     -->
<!--   "fix the build across all packages"            - multi-concern keyword ("across", "all")  -->
<!--   multi-line descriptions                        - multiple sentences signal complexity      -->

Evaluate `$DESCRIPTION` for complexity signals:

```
isTrivial = true  IF ALL of the following are true:
  - length(DESCRIPTION) < 100 characters
  - DESCRIPTION does NOT contain multi-step indicators: "and then", "and", "then", "also", "additionally", "as well"
  - DESCRIPTION does NOT contain multi-concern indicators: "multiple", "several", "across", "each", "all"
  - DESCRIPTION does NOT contain complexity keywords: "refactor", "migrate", "integrate", "architecture", "redesign"
  - DESCRIPTION does NOT contain numbered steps (patterns like "1." "2." or bullet lists)
  - DESCRIPTION is a single sentence (no newlines, no semicolons separating clauses)

isTrivial = false  OTHERWISE (fall back to planner+executor flow)
```

Note: The "and" check uses word-boundary matching to avoid false positives on words containing "and" (e.g., "handler", "standard"). Match the standalone word "and" only.

> **Conservative by design:** This heuristic errs on the side of caution. False positives (treating trivial as complex) only waste a planner spawn. False negatives (treating complex as trivial) risk incomplete execution. When in doubt, the task is classified as complex.

**If `isTrivial` is true:** proceed to Step 5a (inline execution).

**If `isTrivial` is false:** proceed to Step 5 (planner spawn) as normal.

---

**Step 5a: Execute inline (trivial task)**

*This step is only reached when `isTrivial` is true (from Step 4b).*

The orchestrating agent executes the task directly -- no `Task()` spawn for planner or executor:

1. Read relevant files identified from `$DESCRIPTION`
2. Make the changes directly (edit files, create files, etc.)
3. Run verification (tests, linting, build) as appropriate for the change
4. Commit changes atomically per normal GSD patterns (individual file staging, conventional commit message)
5. Store the commit hash as `$commit_hash`

After execution completes, proceed to Step 6a.

---

**Step 6a: Create minimal tracking artifacts**

*This step is only reached when `isTrivial` is true (from Step 5a).*

Create minimal PLAN.md and SUMMARY.md so that Step 7 (STATE.md update) and Step 8 (final commit) work identically regardless of which path was taken.

**6a-i. Create minimal PLAN.md:**

Write `${QUICK_DIR}/${next_num}-PLAN.md`:

```markdown
---
phase: quick
plan: ${next_num}
type: execute
wave: 1
---

# Quick Task ${next_num}: ${DESCRIPTION}

<tasks>
<task type="auto">
  <name>${DESCRIPTION}</name>
  <done>Completed inline (trivial task)</done>
</task>
</tasks>
```

**6a-ii. Create minimal SUMMARY.md:**

Write `${QUICK_DIR}/${next_num}-SUMMARY.md`:

```markdown
---
phase: quick
plan: ${next_num}
duration: ${duration}
completed: ${date}
---

# Quick Task ${next_num}: ${DESCRIPTION}

**Executed inline (trivial task -- skipped planner+executor spawn)**

## Performance
- **Duration:** ${duration}
- **Tasks:** 1
- **Files modified:** ${file_count}

## Task Commits
1. **${DESCRIPTION}** - \`${commit_hash}\`

## Files Modified
${list of files modified}
```

After artifacts are created, proceed to Step 7 (unchanged).

---

**Step 5: Spawn planner (quick mode)**

Spawn gsd-planner with quick mode context:

```
Task(
  prompt="
<planning_context>

**Mode:** quick
**Directory:** ${QUICK_DIR}
**Description:** ${DESCRIPTION}

**Project State:**
@.planning/STATE.md

</planning_context>

<constraints>
- Create a SINGLE plan with 1-3 focused tasks
- Quick tasks should be atomic and self-contained
- No research phase, no checker phase
- Target ~30% context usage (simple, focused)
</constraints>

<output>
Write plan to: ${QUICK_DIR}/${next_num}-PLAN.md
Return: ## PLANNING COMPLETE with plan path
</output>
",
  subagent_type="gsd-planner",
  model="{planner_model}",
  description="Quick plan: ${DESCRIPTION}"
)
```

After planner returns:
1. Verify plan exists at `${QUICK_DIR}/${next_num}-PLAN.md`
2. Extract plan count (typically 1 for quick tasks)
3. Report: "Plan created: ${QUICK_DIR}/${next_num}-PLAN.md"

If plan not found, error: "Planner failed to create ${next_num}-PLAN.md"

---

**Step 6: Spawn executor**

Spawn gsd-executor with plan reference:

```
Task(
  prompt="
Execute quick task ${next_num}.

Plan: @${QUICK_DIR}/${next_num}-PLAN.md
Project state: @.planning/STATE.md

<constraints>
- Execute all tasks in the plan
- Commit each task atomically
- Create summary at: ${QUICK_DIR}/${next_num}-SUMMARY.md
- Do NOT update ROADMAP.md (quick tasks are separate from planned phases)
</constraints>
",
  subagent_type="gsd-executor",
  model="{executor_model}",
  description="Execute: ${DESCRIPTION}"
)
```

After executor returns:
1. Verify summary exists at `${QUICK_DIR}/${next_num}-SUMMARY.md`
2. Extract commit hash from executor output
3. Report completion status

**Known Claude Code bug (classifyHandoffIfNeeded):** If executor reports "failed" with error `classifyHandoffIfNeeded is not defined`, this is a Claude Code runtime bug — not a real failure. Check if summary file exists and git log shows commits. If so, treat as successful.

If summary not found, error: "Executor failed to create ${next_num}-SUMMARY.md"

Note: For quick tasks producing multiple plans (rare), spawn executors in parallel waves per execute-phase patterns.

---

**Step 7: Update STATE.md**

Update STATE.md with quick task completion record.

**7a. Check if "Quick Tasks Completed" section exists:**

Read STATE.md and check for `### Quick Tasks Completed` section.

**7b. If section doesn't exist, create it:**

Insert after `### Blockers/Concerns` section:

```markdown
### Quick Tasks Completed

| # | Description | Date | Commit | Directory |
|---|-------------|------|--------|-----------|
```

**7c. Append new row to table:**

Use `date` from init:
```markdown
| ${next_num} | ${DESCRIPTION} | ${date} | ${commit_hash} | [${next_num}-${slug}](./quick/${next_num}-${slug}/) |
```

**7d. Update "Last activity" line:**

Use `date` from init:
```
Last activity: ${date} - Completed quick task ${next_num}: ${DESCRIPTION}
```

Use Edit tool to make these changes atomically

---

**Step 8: Final commit and completion**

Stage and commit quick task artifacts:

```bash
node ./.claude/get-shit-done/bin/gsd-tools.js commit "docs(quick-${next_num}): ${DESCRIPTION}" --files ${QUICK_DIR}/${next_num}-PLAN.md ${QUICK_DIR}/${next_num}-SUMMARY.md .planning/STATE.md
```

Get final commit hash:
```bash
commit_hash=$(git rev-parse --short HEAD)
```

Display completion output:
```
---

GSD > QUICK TASK COMPLETE

Quick Task ${next_num}: ${DESCRIPTION}

Summary: ${QUICK_DIR}/${next_num}-SUMMARY.md
Commit: ${commit_hash}

---

Ready for next task: /gsd:quick
```

</process>

<success_criteria>
- [ ] ROADMAP.md validation passes
- [ ] User provides task description
- [ ] Slug generated (lowercase, hyphens, max 40 chars)
- [ ] Next number calculated (001, 002, 003...)
- [ ] Directory created at `.planning/quick/NNN-slug/`
- [ ] `${next_num}-PLAN.md` created by planner
- [ ] `${next_num}-SUMMARY.md` created by executor
- [ ] STATE.md updated with quick task row
- [ ] Artifacts committed
- [ ] Complexity gate evaluates task description
- [ ] Trivial tasks execute inline (no agent spawn)
- [ ] Complex tasks use full planner+executor flow
- [ ] Minimal PLAN.md and SUMMARY.md created for inline tasks
</success_criteria>
