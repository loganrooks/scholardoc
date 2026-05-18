# Agent Execution Protocol

> **Shared operational conventions for all GSD agents**
>
> Convention changes go HERE, not in individual agent specs.
> Agent-specific overrides should appear ABOVE the `<required_reading>` tag in agent specs.

## 1. Git Safety Rules

**NEVER use `git add .` or `git add -A`**

Stage files individually by name to prevent unintended commits of sensitive files (.env, credentials), large binaries, or temporary files.

```bash
# CORRECT
git add src/api/auth.ts
git add src/types/user.ts

# NEVER
git add .
git add -A
```

**Rationale:** Batch staging risks committing files you don't intend to commit. Explicit individual file staging ensures you control exactly what enters version history.

## 2. File Staging Conventions

**Before staging:**

```bash
git status --short
```

Review the list. Stage only files related to the current task:

```bash
git add path/to/file1.ts
git add path/to/file2.ts
git add path/to/file3.ts
```

Each file gets its own `git add` command. This makes git history clear and prevents accidental commits.

## 3. Commit Format & Types

**Format:** `{type}({phase}-{plan}): {concise description}`

Body uses bullet points for key changes.

**For full commit format reference, see:**

@./.claude/get-shit-done/references/git-integration.md

**Quick reference — Commit types:**

| Type       | When                                            |
| ---------- | ----------------------------------------------- |
| `feat`     | New feature, endpoint, component                |
| `fix`      | Bug fix, error correction                       |
| `test`     | Test-only changes (TDD RED)                     |
| `refactor` | Code cleanup, no behavior change (TDD REFACTOR) |
| `chore`    | Config, tooling, dependencies                   |
| `perf`     | Performance improvement                         |
| `docs`     | Documentation changes                           |

**Note:** git-integration.md is the canonical reference. The table above is a quick agent-level summary.

**Example:**

```bash
git commit -m "feat(08-02): create user registration endpoint

- POST /auth/register validates email and password
- Checks for duplicate users
- Returns JWT token on success
"
```

## 4. gsd-tools.js Commit Pattern

Use gsd-tools.js for committing planning artifacts (PLAN.md, SUMMARY.md, RESEARCH.md, STATE.md, ROADMAP.md).

**Pattern:**

```bash
node ./.claude/get-shit-done/bin/gsd-tools.js commit "{message}" --files {file1} {file2}
```

**When to use:**

- After creating RESEARCH.md
- After creating PLAN.md files
- After completing a plan (SUMMARY.md + STATE.md)
- After debugging (resolved debug session file)

**Example:**

```bash
node ./.claude/get-shit-done/bin/gsd-tools.js commit "docs(22-01): create shared agent protocol" --files .claude/get-shit-done/references/agent-protocol.md .planning/phases/22-agent-boilerplate-extraction/22-EXTRACTION-REGISTRY.md
```

The gsd-tools.js commit command respects `commit_docs` configuration automatically.

## 5. commit_docs Configuration

**What it controls:** Git operations ONLY, not file writing.

**Always:**
1. Write files first (using Write/Edit tools)
2. Check `commit_docs` configuration
3. If `commit_docs: true` → commit via gsd-tools.js
4. If `commit_docs: false` → skip git commit, files still written

**Critical distinction:**

- `commit_docs: false` means "don't commit" NOT "don't write files"
- Planning artifacts MUST be written regardless of commit_docs setting
- Code files are committed separately from planning artifacts

**How gsd-tools.js handles it:**

The `gsd-tools.js commit` command automatically checks `commit_docs` from config.json:
- If `true`: executes git commit
- If `false`: skips git commit silently

Agents don't need to check commit_docs manually when using gsd-tools.js commit.

## 6. State File Conventions

**Standard GSD file paths and naming patterns:**

### Directory Structure

```
.planning/
├── STATE.md                    # Current position, decisions, blockers
├── ROADMAP.md                  # Phase list with goals and plans
├── PROJECT.md                  # Project vision and metadata
├── REQUIREMENTS.md             # Project requirements
├── MILESTONES.md               # Milestone definitions and tracking
├── config.json                 # GSD configuration
├── phases/
│   ├── XX-name/                # Phase directory (e.g., 01-foundation)
│   │   ├── XX-CONTEXT.md       # User decisions from /gsd:discuss-phase
│   │   ├── XX-RESEARCH.md      # Phase research findings
│   │   ├── XX-01-PLAN.md       # Individual plan files
│   │   ├── XX-01-SUMMARY.md    # Plan completion summaries
│   │   └── XX-VERIFICATION.md  # Verification results
├── debug/
│   ├── {slug}.md               # Active debug sessions
│   └── resolved/               # Completed debug sessions
├── milestones/                 # Milestone tracking artifacts
├── quick/                      # Quick fix plans (non-phase work)
├── research/
│   ├── SUMMARY.md              # Project research synthesis
│   ├── STACK.md                # Technology recommendations
│   ├── FEATURES.md             # Feature analysis
│   ├── ARCHITECTURE.md         # Architecture patterns
│   └── PITFALLS.md             # Common pitfalls
├── spikes/                     # Spike investigation artifacts
├── todos/                      # TODO tracking
└── codebase/
    ├── STACK.md                # Current tech stack
    ├── ARCHITECTURE.md         # Current architecture
    ├── STRUCTURE.md            # Directory structure guide
    ├── CONVENTIONS.md          # Coding conventions
    ├── TESTING.md              # Testing patterns
    ├── INTEGRATIONS.md         # External integrations
    └── CONCERNS.md             # Technical debt/issues
```

### File Naming Patterns

**Phase files:**
- `{phase}-CONTEXT.md` — User decisions (e.g., `22-CONTEXT.md`)
- `{phase}-RESEARCH.md` — Research findings (e.g., `22-RESEARCH.md`)
- `{phase}-{plan}-PLAN.md` — Plan prompts (e.g., `22-01-PLAN.md`)
- `{phase}-{plan}-SUMMARY.md` — Execution summaries (e.g., `22-01-SUMMARY.md`)
- `{phase}-VERIFICATION.md` — Verification results (e.g., `22-VERIFICATION.md`)

**Phase identifiers:**
- Standard: `01-foundation`, `02-auth`, etc.
- Decimal (hotfixes): `01.1-hotfix`
- Padded phase numbers: `01`, `02`, `22` (always 2+ digits)

**Debug files:**
- Active: `.planning/debug/{slug}.md`
- Resolved: `.planning/debug/resolved/{slug}.md`

## 7. gsd-tools.js Init Pattern

Most agents load execution context via gsd-tools.js init command.

**General pattern:**

```bash
INIT=$(node ./.claude/get-shit-done/bin/gsd-tools.js init {subcommand} "${PHASE}")
```

**Available init subcommands:**

| Subcommand       | Used By                      | Returns                                                    |
| ---------------- | ---------------------------- | ---------------------------------------------------------- |
| `execute-phase`  | gsd-executor                 | executor_model, commit_docs, phase_dir, plans, summaries  |
| `plan-phase`     | gsd-planner                  | planner_model, checker_model, research_enabled, phase_dir |
| `phase-op`       | gsd-phase-researcher, others | phase_dir, padded_phase, phase_number                     |
| `state load`     | gsd-debugger, others         | Full config + state content                               |
| `verify`         | gsd-verifier                 | phase_dir, verification settings                          |

**What agents extract from INIT JSON:**

Each agent uses different fields. Common fields:
- `phase_dir`: Absolute path to phase directory
- `commit_docs`: Whether to commit planning artifacts
- `phase_number`: Numeric phase identifier
- `padded_phase`: Zero-padded phase number (e.g., "01", "22")

The specific init subcommand and fields extracted remain in each agent spec (agent-specific).

**Example from executor:**

```bash
INIT=$(node ./.claude/get-shit-done/bin/gsd-tools.js init execute-phase "${PHASE}")
# Extract: executor_model, commit_docs, phase_dir, plans, incomplete_plans
```

## 8. Tool Conventions (Context7 / WebSearch / Brave)

### Tool Priority Table

| Priority | Tool       | Use For                                    | Trust Level   |
| -------- | ---------- | ------------------------------------------ | ------------- |
| 1st      | Context7   | Library APIs, features, config, versions   | HIGH          |
| 2nd      | WebFetch   | Official docs/READMEs, changelogs          | HIGH-MEDIUM   |
| 3rd      | WebSearch  | Ecosystem discovery, community patterns    | Needs verification |

### Context7 MCP Flow

**1. Resolve library ID first:**

```javascript
mcp__context7__resolve-library-id with libraryName: "library-name"
```

Returns: `{ libraryId: "npm:library-name@version" }`

**2. Query docs with resolved ID:**

```javascript
mcp__context7__query-docs with libraryId: "npm:library-name@version", query: "specific question"
```

**Never guess Context7 library IDs.** Always resolve first.

**When to use Context7:**
- Checking library capabilities
- Finding API signatures
- Verifying configuration options
- Confirming version-specific behavior

### WebSearch Best Practices

**Always include current year in queries:**

```
"next.js app router best practices 2026"
"stripe webhook verification 2026"
```

**Use multiple query variations:**

```
"how to implement X with Y"
"Y library X pattern"
"best way to do X in Y"
```

**Cross-verify findings:**
- WebSearch alone = LOW confidence
- WebSearch + official docs = MEDIUM confidence
- Context7 confirmation = HIGH confidence

### Enhanced Web Search (Brave API)

**When available** (check `brave_search` config), use Brave Search via gsd-tools.js:

```bash
node ./.claude/get-shit-done/bin/gsd-tools.js websearch "query" --limit 10
```

**Options:**
- `--limit N` — Number of results (default: 10)
- `--freshness day|week|month` — Restrict to recent content

**Benefits:**
- Independent search index (not Google/Bing)
- Less SEO spam
- Faster responses

**When Brave unavailable:** Fall back to built-in WebSearch tool.

## 9. Source Hierarchy & Confidence Levels

### Confidence Level Table

| Level  | Sources                                                 | How to Use                |
| ------ | ------------------------------------------------------- | ------------------------- |
| HIGH   | Context7, official docs, official releases              | State as fact             |
| MEDIUM | WebSearch verified with official source, multiple credible sources | State with attribution |
| LOW    | WebSearch only, single source, unverified               | Flag as needing validation |

### Source Priority Chain

1. **Context7** — Current, version-aware library documentation
2. **Official Documentation** — Canonical project docs
3. **Official GitHub** — Release notes, changelogs, issue discussions
4. **WebSearch (verified)** — Cross-referenced with authoritative sources
5. **WebSearch (unverified)** — Requires validation before use

**Never present LOW confidence findings as authoritative.**

When documenting research:
- HIGH confidence: "Library X provides feature Y"
- MEDIUM confidence: "According to [source], library X supports Y"
- LOW confidence: "WebSearch suggests X (unverified, needs validation)"

## 10. Research Verification Protocol

### Verification Flow

**For each research finding:**

```
1. Can I verify with Context7?
   └─ YES → HIGH confidence, proceed
   └─ NO → Continue to step 2

2. Can I verify with official docs?
   └─ YES → MEDIUM confidence, proceed
   └─ NO → Continue to step 3

3. Do multiple credible sources agree?
   └─ YES → MEDIUM confidence (multiple sources)
   └─ NO → LOW confidence, flag for validation
```

### Known Research Pitfalls

**Configuration Scope Blindness**

**What goes wrong:** Assuming global configuration means no project-scoping exists

**Prevention:** Verify ALL configuration scopes (global, project, local, workspace)

---

**Deprecated Features**

**What goes wrong:** Finding old documentation and concluding feature doesn't exist

**Prevention:** Check current official docs, review changelog, verify version numbers and publication dates

---

**Negative Claims Without Evidence**

**What goes wrong:** Making definitive "X is not possible" statements without official verification

**Prevention:** For any negative claim:
- Is it verified by official docs?
- Have you checked recent updates?
- Are you confusing "didn't find it" with "doesn't exist"?

---

**Single Source Reliance**

**What goes wrong:** Relying on a single source for critical claims

**Prevention:** Require multiple sources:
- Official docs (primary)
- Release notes (currency check)
- Additional credible source (verification)

### Pre-Submission Research Checklist

Before finalizing research outputs:

- [ ] All domains investigated (stack, patterns, pitfalls)
- [ ] Negative claims verified with official docs
- [ ] Multiple sources cross-referenced for critical claims
- [ ] URLs provided for authoritative sources
- [ ] Publication dates checked (prefer recent/current)
- [ ] Confidence levels assigned honestly
- [ ] "What might I have missed?" review completed

## 11. Quality & Context Budget

### Quality Degradation Curve

Claude's output quality correlates with context window usage:

| Context Usage | Quality     | Claude's State               |
| ------------- | ----------- | ---------------------------- |
| 0-30%         | PEAK        | Thorough, comprehensive      |
| 30-50%        | GOOD        | Confident, solid work        |
| 50-70%        | DEGRADING   | Efficiency mode begins       |
| 70%+          | POOR        | Rushed, minimal              |

### Context Budget Rule

**Plans should complete within ~50% context** (not 80%).

**Why ~50% target:**
- No context anxiety
- Quality maintained start to finish
- Room for unexpected complexity
- Can handle plan deviations

**For standard plans:** 2-3 tasks maximum per plan

**For TDD plans:** 1 feature per plan, targeting ~40% context (lower than standard because RED→GREEN→REFACTOR cycles are execution-heavy)

### Plan Sizing Guidelines

| Task Complexity            | Tasks/Plan | Context/Task | Total    |
| -------------------------- | ---------- | ------------ | -------- |
| Simple (CRUD, config)      | 3          | ~10-15%      | ~30-45%  |
| Complex (auth, payments)   | 2          | ~20-30%      | ~40-50%  |
| Very complex (migrations)  | 1-2        | ~30-40%      | ~30-50%  |

**Split signals:**
- More than 3 tasks
- Multiple subsystems (DB + API + UI)
- Any task with >5 file modifications
- Checkpoint + implementation in same plan

## 12. Structured Return Conventions

All GSD agents return structured results to orchestrators using a consistent pattern.

### Structural Pattern

**All structured returns must:**

1. Use `## {STATUS KEYWORD}` as header
2. Include Phase/Status metadata immediately after header
3. Use tables for structured data
4. Provide clear "Next Steps" or "Awaiting" section

**Common status keywords:**

- `PLAN COMPLETE`
- `PLANNING COMPLETE`
- `RESEARCH COMPLETE`
- `DEBUG COMPLETE`
- `ROOT CAUSE FOUND`
- `VERIFICATION COMPLETE`
- `CHECKPOINT REACHED`

### Return Format Example

```markdown
## {STATUS KEYWORD}

**Phase:** {phase identifier}
**Status:** {current status}

### {Section Name}

[Structured content - often a table]

| Column 1 | Column 2 |
|----------|----------|
| Data     | Data     |

### Next Steps

[What should happen next]
```

**Note:** The actual return types and detailed content remain in each agent spec. This protocol defines only the structural conventions.

## 13. Forbidden Files

**Agents MUST NOT modify these files:**

### Sensitive Files

- `.env` — Environment variables with secrets
- `.env.local`, `.env.production`, `.env.development` — Environment variants
- `credentials.json`, `service-account.json` — Service credentials
- `**/secrets/**` — Any secrets directories
- `.npmrc` with auth tokens
- `.git/config` — Git configuration with remote URLs

### System Files

- `.git/` directory contents (except via git commands)
- `node_modules/` — Managed by package manager
- `.DS_Store`, `Thumbs.db` — OS metadata
- `*.swp`, `*.swo` — Editor temporary files

### Build Artifacts

- `dist/`, `build/`, `out/` — Build output directories
- `.next/`, `.nuxt/` — Framework build caches
- `*.log` — Log files

**Rationale:** Modifying these files can:
- Expose secrets to version control
- Break builds and deployments
- Corrupt system state
- Cause security vulnerabilities

**What agents CAN do:**

- Read package.json to understand dependencies (but not modify)
- Read .gitignore to understand project structure
- Read config files to understand settings
- Create NEW files like `.env.example` (documentation of required env vars)

**What agents MUST do instead:**

For environment variables:
- Create `.env.example` with placeholder values
- Document required env vars in USER-SETUP.md
- Use gsd-tools.js to set env vars in external dashboards via CLI (Vercel, Railway, etc.)

For configuration:
- Modify project config files (like `next.config.js`, `vite.config.ts`)
- NOT system/global config files

---

**End of Agent Execution Protocol**

**Version:** 1.0
**Last Updated:** 2026-02-18
**Maintained by:** Phase 22 (Agent Boilerplate Extraction)
