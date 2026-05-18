#!/usr/bin/env node
// Check CI status in background, write result to cache
// Called by SessionStart hook - runs once per session

const fs = require('fs');
const path = require('path');
const os = require('os');
const { spawn } = require('child_process');

const cacheDir = path.join(os.homedir(), '.claude', 'cache');
const cacheFile = path.join(cacheDir, 'gsd-ci-status.json');

// Ensure cache directory exists
if (!fs.existsSync(cacheDir)) {
  fs.mkdirSync(cacheDir, { recursive: true });
}

// Run check in background
const child = spawn(process.execPath, ['-e', `
  const fs = require('fs');
  const { execSync } = require('child_process');
  const cacheFile = ${JSON.stringify(cacheFile)};

  // Pre-flight: check gh CLI availability
  try { execSync('command -v gh', { stdio: 'ignore', timeout: 3000 }); }
  catch { process.exit(0); } // No gh CLI -- silent exit

  // Pre-flight: check gh auth
  try { execSync('gh auth status', { stdio: 'ignore', timeout: 5000 }); }
  catch {
    fs.writeFileSync(cacheFile, JSON.stringify({
      degraded: true,
      reason: 'gh-not-authenticated',
      checked: Math.floor(Date.now() / 1000)
    }));
    process.exit(0);
  }

  // Get current branch
  let branch = 'main';
  try { branch = execSync('git branch --show-current', { encoding: 'utf8', timeout: 5000 }).trim() || 'main'; }
  catch {}

  // Get latest run for current branch
  try {
    const runs = JSON.parse(execSync(
      'gh run list --branch "' + branch + '" --limit 1 --json conclusion,displayTitle,name,createdAt,headSha,status',
      { encoding: 'utf8', timeout: 10000 }
    ));

    fs.writeFileSync(cacheFile, JSON.stringify({
      branch,
      latest_run: runs[0] || null,
      checked: Math.floor(Date.now() / 1000)
    }));
  } catch {
    // API call failed -- write degraded status
    fs.writeFileSync(cacheFile, JSON.stringify({
      degraded: true,
      reason: 'gh-api-error',
      branch,
      checked: Math.floor(Date.now() / 1000)
    }));
  }
`], {
  stdio: 'ignore',
  windowsHide: true,
  detached: true
});

child.unref();
