#!/usr/bin/env node
// Claude Code Statusline - GSD Edition
// Shows: model | current task | directory | context usage

const fs = require('fs');
const path = require('path');
const os = require('os');

// Read JSON from stdin
let input = '';
process.stdin.setEncoding('utf8');
process.stdin.on('data', chunk => input += chunk);
process.stdin.on('end', () => {
  try {
    const data = JSON.parse(input);
    const model = data.model?.display_name || 'Claude';
    const dir = data.workspace?.current_dir || process.cwd();
    const session = data.session_id || '';
    const remaining = data.context_window?.remaining_percentage;

    // Context window display (shows USED percentage scaled to 80% limit)
    // Claude Code enforces an 80% context limit, so we scale to show 100% at that point
    let ctx = '';
    if (remaining != null) {
      const rem = Math.round(remaining);
      const rawUsed = Math.max(0, Math.min(100, 100 - rem));
      // Scale: 80% real usage = 100% displayed
      const used = Math.min(100, Math.round((rawUsed / 80) * 100));

      // Build progress bar (10 segments)
      const filled = Math.floor(used / 10);
      const bar = '█'.repeat(filled) + '░'.repeat(10 - filled);

      // Color based on scaled usage (thresholds adjusted for new scale)
      if (used < 63) {        // ~50% real
        ctx = ` \x1b[32m${bar} ${used}%\x1b[0m`;
      } else if (used < 81) { // ~65% real
        ctx = ` \x1b[33m${bar} ${used}%\x1b[0m`;
      } else if (used < 95) { // ~76% real
        ctx = ` \x1b[38;5;208m${bar} ${used}%\x1b[0m`;
      } else {
        ctx = ` \x1b[5;31m💀 ${bar} ${used}%\x1b[0m`;
      }
    }

    // Current task from todos
    let task = '';
    const homeDir = os.homedir();
    const todosDir = path.join(homeDir, '.claude', 'todos');
    if (session && fs.existsSync(todosDir)) {
      try {
        const files = fs.readdirSync(todosDir)
          .filter(f => f.startsWith(session) && f.includes('-agent-') && f.endsWith('.json'))
          .map(f => ({ name: f, mtime: fs.statSync(path.join(todosDir, f)).mtime }))
          .sort((a, b) => b.mtime - a.mtime);

        if (files.length > 0) {
          try {
            const todos = JSON.parse(fs.readFileSync(path.join(todosDir, files[0].name), 'utf8'));
            const inProgress = todos.find(t => t.status === 'in_progress');
            if (inProgress) task = inProgress.activeForm || '';
          } catch (e) {}
        }
      } catch (e) {
        // Silently fail on file system errors - don't break statusline
      }
    }

    // GSD update available?
    let gsdUpdate = '';
    const cacheFile = path.join(homeDir, '.claude', 'cache', 'gsd-update-check.json');
    if (fs.existsSync(cacheFile)) {
      try {
        const cache = JSON.parse(fs.readFileSync(cacheFile, 'utf8'));
        if (cache.update_available) {
          gsdUpdate = '\x1b[33m⬆ /gsd:update\x1b[0m │ ';
        }
      } catch (e) {}
    }

    // CI status from SessionStart hook cache
    let ciStatus = '';
    const ciCacheFile = path.join(homeDir, '.claude', 'cache', 'gsd-ci-status.json');
    if (fs.existsSync(ciCacheFile)) {
      try {
        const ciCache = JSON.parse(fs.readFileSync(ciCacheFile, 'utf8'));
        // Only show if cache is less than 1 hour old and not degraded
        const age = Math.floor(Date.now() / 1000) - (ciCache.checked || 0);
        if (age < 3600 && ciCache.latest_run && ciCache.latest_run.conclusion === 'failure') {
          ciStatus = '\x1b[31mCI FAIL\x1b[0m | ';
        }
      } catch (e) {}
    }

    // Dev install indicator (VERSION file contains +dev suffix on local installs)
    let devTag = '';
    try {
      const versionFile = path.join(dir, '.claude', 'get-shit-done', 'VERSION');
      if (fs.existsSync(versionFile)) {
        const ver = fs.readFileSync(versionFile, 'utf8').trim();
        if (ver.includes('+dev')) {
          devTag = '\x1b[43;30m DEV \x1b[0m │ ';
        }
      }
    } catch {}


    // Automation level indicator
    let autoTag = '';
    try {
      const autoConfigPath = path.join(dir, '.planning', 'config.json');
      if (fs.existsSync(autoConfigPath)) {
        const cfg = JSON.parse(fs.readFileSync(autoConfigPath, 'utf8'));
        if (cfg.automation && cfg.automation.level !== undefined) {
          const configured = cfg.automation.level;
          // Runtime cap heuristic: check if hooks are available
          // If .claude/settings.json has hooks configured, assume full capability
          let effective = configured;
          try {
            const settingsPath = path.join(dir, '.claude', 'settings.json');
            if (fs.existsSync(settingsPath)) {
              const settings = JSON.parse(fs.readFileSync(settingsPath, 'utf8'));
              if (!settings.hooks || Object.keys(settings.hooks).length === 0) {
                // No hooks configured -- cap features that need hooks
                if (configured > 2) effective = 2;
              }
            } else {
              // No settings.json -- assume hookless runtime
              if (configured > 2) effective = 2;
            }
          } catch {}

          if (effective < configured) {
            autoTag = `\x1b[36mAuto:${configured}(${effective})\x1b[0m │ `;
          } else {
            autoTag = `\x1b[36mAuto:${configured}\x1b[0m │ `;
          }
        }
      }
    } catch {}

    // Output
    const dirname = path.basename(dir);
    if (task) {
      process.stdout.write(`${devTag}${gsdUpdate}${ciStatus}${autoTag}\x1b[2m${model}\x1b[0m │ \x1b[1m${task}\x1b[0m │ \x1b[2m${dirname}\x1b[0m${ctx}`);
    } else {
      process.stdout.write(`${devTag}${gsdUpdate}${ciStatus}${autoTag}\x1b[2m${model}\x1b[0m │ \x1b[2m${dirname}\x1b[0m${ctx}`);
    }
  } catch (e) {
    // Silent fail - don't break statusline on parse errors
  }
});
