# Dual Installation: Local + Global

## Intended Topology

- **Global install** (user-level config dir, e.g. `$HOME/./.claude/get-shit-done/`): Baseline. Makes GSD available in every project by default.
- **Local install** (project-level `.claude/get-shit-done/`): Version pin. Overrides global for a specific project that needs stability or a particular version.

This mirrors the npm global vs local package model.

## Precedence Rules

Local always takes precedence over global. When both exist:
- Commands execute from the local installation
- VERSION from local is the "active" version
- Hooks check local first, fall back to global
- gsd-tools.js init reports the local version as active

## When to Use Each

| Scenario | Recommended Setup |
|----------|-------------------|
| GSD available everywhere, no version pinning needed | Global only |
| Specific project needs a pinned GSD version | Local (project) + Global (baseline) |
| Testing a development build of GSD | Local only (in the GSD repo itself) |
| New to GSD, just getting started | Global only |

## Autocomplete Behavior

When both installations exist, Claude Code discovers commands from both the global and local `commands/` directories. This may cause duplicate entries in autocomplete. The version and scope are appended to each command's description (e.g., "Create execution plan (v1.15.2 local)") to help differentiate them.

The local installation's commands take precedence for execution.

## Cross-Project Impact

Updating the **global** installation affects ALL projects that rely on it (i.e., projects without their own local install). Before updating global:
- Consider which projects use it
- The version-check hook detects version mismatches on session start
- Projects with local installs are unaffected by global updates

Updating a **local** installation only affects that specific project.

## Installing

```bash
# Global (baseline -- available in all projects)
npx get-shit-done-reflect-cc --global

# Local (version pin -- this project only)
npx get-shit-done-reflect-cc --local

# The installer warns if the other scope already has GSD installed
```

## Detection

The `gsd-tools.js init` commands include a `dual_install` field in their JSON output:

```json
{
  "dual_install": {
    "detected": true,
    "local": { "path": "/path/to/project/.claude/get-shit-done", "version": "1.15.0" },
    "global": { "path": "/home/user/.claude/get-shit-done", "version": "1.15.0" },
    "active_scope": "local"
  }
}
```

When only one installation exists: `{ "detected": false }`.

## Related

- `/gsd:update` -- handles both scopes when dual installation detected
- `.planning/config.json` -- project-level GSD version tracking
- `resume-project.md` -- surfaces dual-install status on session resume
