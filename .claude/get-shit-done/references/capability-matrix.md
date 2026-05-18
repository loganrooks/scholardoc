# Runtime Capability Matrix

> Reference document for GSD workflow orchestrators. Declares which features
> are available in each supported runtime. Workflows use `has_capability()`
> patterns to branch behavior based on this matrix.

## Quick Reference

| Capability | Claude Code | OpenCode | Gemini CLI | Codex CLI | Impact When Missing |
|------------|:-----------:|:--------:|:----------:|:---------:|---------------------|
| task_tool  |      Y      |    Y     |   Y [1]    |     N     | Sequential execution |
| hooks      |      Y      |    N     |     Y      |     N     | Skip hook features   |
| tool_permissions | Y     |    Y     |   Y [2]    |     N     | All tools available  |
| mcp_servers|      Y      |    Y     |   Y [3]    |   Y [4]   | Skip MCP features    |

> [1] Experimental, sequential only. Parallel subagent execution not yet available.
> [2] Via tools.core (allowlist), tools.exclude (denylist), and per-sub-agent restrictions.
> [3] STDIO, SSE, and Streamable HTTP transports. OAuth support.
> [4] STDIO and Streamable HTTP transports. OAuth support.

## Format Reference

| Property | Claude Code | OpenCode | Gemini CLI | Codex CLI |
|----------|-------------|----------|------------|-----------|
| frontmatter | YAML | YAML (tools as map) | TOML | SKILL.md |
| commands | commands/gsd/*.md | command/gsd-*.md | commands/gsd/*.toml | skills/*.md |
| agents | agents/gsd-*.md | agents/gsd-*.md | agents/gsd-*.md | (via AGENTS.md) |
| config | settings.json | opencode.json | settings.json | codex.toml |

## Capability Details

### task_tool

Can spawn subagent processes via Task() calls for parallel execution. This is the primary mechanism for wave-based plan execution -- the orchestrator spawns a gsd-executor agent for each plan in a wave, and they run concurrently.

**Available in:** Claude Code, OpenCode, Gemini CLI [1]
**Missing in:** Codex CLI

> [1] Gemini CLI task_tool support is experimental and sequential only. Parallel subagent execution is not yet available -- plans within a wave execute one at a time rather than concurrently.

**Degraded behavior when missing:**
Execute plans sequentially in the main context. The orchestrator reads plan files directly and executes tasks one at a time instead of spawning gsd-executor agents per wave. Wave grouping and parallel spawning are skipped. Plans execute in dependency order, and each plan's tasks are completed before moving to the next plan.

**How orchestrators adapt:**
Use `<capability_check name="parallel_execution">` before wave execution logic. If task_tool is available, spawn agents as designed. Otherwise, execute plans sequentially following the execute-plan.md flow inline.

### hooks

Pre/post tool execution hooks (SessionStart, Stop, etc.). Used for automatic update checks at session start, statusline integration, and pre-commit validation.

**Available in:** Claude Code, Gemini CLI
**Missing in:** OpenCode, Codex CLI

**Degraded behavior when missing:**
Skip hook-dependent features entirely. No automatic update checks at session start, no statusline integration. Version checking happens on explicit GSD command invocation instead of automatically via session hooks. This is a graceful degradation -- the user still gets update notifications, just triggered differently.

**How orchestrators adapt:**
Use `<capability_check name="hooks_support">` before hook configuration. If hooks are available, configure them normally. Otherwise, skip hook setup and note that update checks run on command invocation.

### tool_permissions

Granular tool allow/deny lists in agent/command frontmatter. Allows restricting which tools an agent can use (e.g., read-only agents that cannot write files).

**Available in:** Claude Code (allowed-tools list), OpenCode (permission map in YAML), Gemini CLI (tools.core allowlist, tools.exclude denylist)
**Missing in:** Codex CLI

**Degraded behavior when missing:**
All tools are available to all agents (Codex CLI). There is no mechanism to restrict tool access at the agent/command level. This is generally safe -- GSD agents are designed to operate correctly without restrictions -- but means that tool sandboxing relies on runtime-level controls rather than per-agent configuration.

**How orchestrators adapt:**
No orchestrator adaptation needed. The installer preserves tool permission frontmatter for runtimes that support it (Claude Code, OpenCode, Gemini CLI) and strips it for runtimes that do not (Codex CLI). Agents function correctly with all tools available.

### mcp_servers

MCP (Model Context Protocol) server integration. Allows agents to access external tools and services via the MCP protocol.

**Available in:** Claude Code, OpenCode, Gemini CLI, Codex CLI
**Status:** Available in all supported runtimes.

**Transport support by runtime:**
- Claude Code: STDIO, SSE, Streamable HTTP
- OpenCode: STDIO, SSE, Streamable HTTP
- Gemini CLI: STDIO, SSE, Streamable HTTP. OAuth support.
- Codex CLI: STDIO, Streamable HTTP. OAuth support.

**Degraded behavior (informational):**
All four supported runtimes now support MCP servers. This section is retained for documentation purposes -- if a future runtime lacks MCP support, the degraded behavior is: MCP-dependent features are skipped, MCP tool references in agent specs are excluded during format conversion, and agents function with their built-in tools only.

**How orchestrators adapt:**
No orchestrator adaptation needed. The installer preserves MCP tool references for all runtimes. MCP server configuration is handled at the runtime config level (settings.json, opencode.json, codex.toml).

## Degraded Behavior Summary

### Codex CLI (most constrained)

| Feature | Status | Adaptation |
|---------|--------|------------|
| Parallel agents (task_tool) | N | Sequential plan execution in main context |
| Hooks | N | Update checks on GSD command invocation |
| Tool permissions | N | All tools available to all agents |
| MCP servers | Y | Full MCP support via STDIO and Streamable HTTP |

Codex CLI operates as the baseline runtime with two missing capabilities: parallel execution (task_tool) and session hooks. All GSD workflows are designed to function correctly under these constraints. The primary impact is execution speed (sequential vs parallel) and the absence of automatic session hooks. MCP servers and tool permissions are the only areas where Codex remains more constrained than other runtimes (no tool permissions support).

### Gemini CLI

| Feature | Status | Adaptation |
|---------|--------|------------|
| Parallel agents (task_tool) | Y [1] | Experimental, sequential only -- no parallel subagent execution |

> [1] task_tool is available but limited. Subagents execute sequentially rather than in parallel waves.

Gemini CLI is near-full capability. It supports tool permissions (via tools.core/tools.exclude), MCP servers (STDIO, SSE, Streamable HTTP), and hooks. The only limitation is that task_tool support is experimental and sequential -- parallel subagent execution is not yet available.

### OpenCode

| Feature | Status | Adaptation |
|---------|--------|------------|
| Hooks | N | Update checks on GSD command invocation |

OpenCode is near-full capability. The only limitation is the lack of session hooks, which means update checks happen on explicit GSD command invocation rather than automatically at session start.

### Claude Code

Full capability -- no degradation. All features available.

## Feature Detection Convention

Workflows use a prose-based feature detection pattern. This is a **convention for LLM-read specifications**, not a programmatic API. When an LLM executes a workflow, it reads the capability check and branches behavior accordingly.

### The `has_capability()` Pattern

Workflows express capability checks using this prose pattern:

```
If has_capability("feature_name"):
  [Standard behavior when feature is available]

Else:
  [Degraded behavior when feature is missing]
```

The LLM executing the workflow reads the capability matrix (this document) to determine which features are available in its runtime, then follows the appropriate branch.

### The `<capability_check>` XML Tag

Capability checks are wrapped in `<capability_check>` XML tags for grep-ability and clear scoping:

```markdown
<capability_check name="parallel_execution">
Check the runtime capability matrix (get-shit-done/references/capability-matrix.md):

If has_capability("task_tool"):
  Spawn gsd-executor via Task() for each plan in the wave.
  Track agent progress, collect results, proceed to next wave.

Else:
  Note to user (first occurrence only): "Note: Running sequentially -- this runtime doesn't support parallel agents."
  For each plan in execution order:
  1. Read the plan file directly
  2. Execute each task in sequence
  3. Create SUMMARY.md after all tasks complete
  4. Proceed to next plan
</capability_check>
```

### Design Principles

1. **Always wrap in `<capability_check>` tags** -- enables discovery via `grep capability_check`
2. **Include a descriptive `name` attribute** -- makes checks identifiable and grep-able
3. **Standard behavior first** -- the if/else always presents the full-capability path first, then the degraded path
4. **Inform once, then adapt silently** -- on first encounter of a missing capability in a session, emit a brief note to the user. Subsequent occurrences adapt without comment
5. **Degraded paths must be functionally complete** -- degraded is not broken. The system works correctly, just differently
6. **Capability checks live in orchestrators only** -- agent specs stay clean and capability-agnostic. They describe WHAT to do, not WHETHER to do it
7. **Feature detection, not runtime detection** -- use `has_capability("task_tool")`, never `if runtime === "codex"`. Feature detection survives new runtimes being added
