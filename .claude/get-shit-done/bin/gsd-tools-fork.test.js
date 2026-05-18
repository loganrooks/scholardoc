/**
 * GSD Tools Fork-Specific Tests
 *
 * Tests for fork custom config fields (health_check, devops, gsd_reflect_version)
 * that round-trip through config-set without data loss.
 *
 * Separate file from gsd-tools.test.js per Phase 9 decision:
 * "Separate fork-tools.js over modifying gsd-tools.js" — zero merge friction.
 */

const { test, describe, beforeEach, afterEach } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const TOOLS_PATH = path.join(__dirname, 'gsd-tools.js');

// Helper to run gsd-tools command (mirrors upstream test pattern)
function runGsdTools(args, cwd = process.cwd()) {
  try {
    const result = execSync(`node "${TOOLS_PATH}" ${args}`, {
      cwd,
      encoding: 'utf-8',
      stdio: ['pipe', 'pipe', 'pipe'],
    });
    return { success: true, output: result.trim() };
  } catch (err) {
    return {
      success: false,
      output: err.stdout?.toString().trim() || '',
      error: err.stderr?.toString().trim() || err.message,
    };
  }
}

// Create temp directory structure (mirrors upstream test pattern)
function createTempProject() {
  const tmpDir = fs.mkdtempSync(path.join(require('os').tmpdir(), 'gsd-fork-test-'));
  fs.mkdirSync(path.join(tmpDir, '.planning', 'phases'), { recursive: true });
  return tmpDir;
}

function cleanup(tmpDir) {
  fs.rmSync(tmpDir, { recursive: true, force: true });
}

// Helper to read config.json from a temp project
function readConfig(tmpDir) {
  const configPath = path.join(tmpDir, '.planning', 'config.json');
  return JSON.parse(fs.readFileSync(configPath, 'utf-8'));
}

// ─────────────────────────────────────────────────────────────────────────────
// config-set/config-get fork custom fields
// ─────────────────────────────────────────────────────────────────────────────

describe('config-set/config-get fork custom fields', () => {
  let tmpDir;

  beforeEach(() => {
    tmpDir = createTempProject();
    // Seed with minimal config.json so config-set has a file to read
    fs.writeFileSync(
      path.join(tmpDir, '.planning', 'config.json'),
      JSON.stringify({}, null, 2),
      'utf-8'
    );
  });

  afterEach(() => {
    cleanup(tmpDir);
  });

  test('sets and gets health_check.frequency', () => {
    const result = runGsdTools('config-set health_check.frequency milestone-only', tmpDir);
    assert.ok(result.success, `config-set failed: ${result.error}`);

    const config = readConfig(tmpDir);
    assert.strictEqual(
      config.health_check.frequency,
      'milestone-only',
      'health_check.frequency should be "milestone-only"'
    );
  });

  test('sets and gets health_check.stale_threshold_days', () => {
    const result = runGsdTools('config-set health_check.stale_threshold_days 7', tmpDir);
    assert.ok(result.success, `config-set failed: ${result.error}`);

    const config = readConfig(tmpDir);
    // Note: config-set parses numeric values via !isNaN check, so 7 becomes Number(7)
    assert.strictEqual(
      config.health_check.stale_threshold_days,
      7,
      'health_check.stale_threshold_days should be 7 (number)'
    );
  });

  test('sets and gets devops.ci_provider', () => {
    const result = runGsdTools('config-set devops.ci_provider github-actions', tmpDir);
    assert.ok(result.success, `config-set failed: ${result.error}`);

    const config = readConfig(tmpDir);
    assert.strictEqual(
      config.devops.ci_provider,
      'github-actions',
      'devops.ci_provider should be "github-actions"'
    );
  });

  test('sets and gets devops.commit_convention', () => {
    const result = runGsdTools('config-set devops.commit_convention conventional', tmpDir);
    assert.ok(result.success, `config-set failed: ${result.error}`);

    const config = readConfig(tmpDir);
    assert.strictEqual(
      config.devops.commit_convention,
      'conventional',
      'devops.commit_convention should be "conventional"'
    );
  });

  test('sets and gets gsd_reflect_version', () => {
    const result = runGsdTools('config-set gsd_reflect_version 1.13.0', tmpDir);
    assert.ok(result.success, `config-set failed: ${result.error}`);

    const config = readConfig(tmpDir);
    // "1.13.0" has multiple dots so isNaN("1.13.0") is true — stays as string
    assert.strictEqual(
      config.gsd_reflect_version,
      '1.13.0',
      'gsd_reflect_version should remain as string "1.13.0" (not parsed as number)'
    );
  });

  test('preserves existing config when setting fork fields', () => {
    // Pre-seed config with upstream field
    fs.writeFileSync(
      path.join(tmpDir, '.planning', 'config.json'),
      JSON.stringify({ mode: 'yolo', depth: 'comprehensive' }, null, 2),
      'utf-8'
    );

    const result = runGsdTools('config-set health_check.frequency milestone-only', tmpDir);
    assert.ok(result.success, `config-set failed: ${result.error}`);

    const config = readConfig(tmpDir);
    assert.strictEqual(config.mode, 'yolo', 'upstream mode field should be preserved');
    assert.strictEqual(config.depth, 'comprehensive', 'upstream depth field should be preserved');
    assert.strictEqual(
      config.health_check.frequency,
      'milestone-only',
      'fork field should be set alongside upstream fields'
    );
  });

  test('sets nested devops.environments as JSON array', () => {
    // config-set only accepts a single value argument, so we cannot pass a JSON array
    // directly through the CLI. Instead, verify that setting other devops fields
    // does not corrupt an existing environments array written directly to config.json.
    fs.writeFileSync(
      path.join(tmpDir, '.planning', 'config.json'),
      JSON.stringify({
        devops: {
          environments: ['staging', 'production'],
        },
      }, null, 2),
      'utf-8'
    );

    // Set a sibling field via config-set
    const result = runGsdTools('config-set devops.ci_provider github-actions', tmpDir);
    assert.ok(result.success, `config-set failed: ${result.error}`);

    const config = readConfig(tmpDir);
    assert.deepStrictEqual(
      config.devops.environments,
      ['staging', 'production'],
      'existing environments array should be preserved after setting sibling field'
    );
    assert.strictEqual(
      config.devops.ci_provider,
      'github-actions',
      'ci_provider should be set alongside environments'
    );
  });
});

// ─────────────────────────────────────────────────────────────────────────────
// frontmatter roundtrip: triage/lifecycle objects (Phase 33 prerequisite)
// ─────────────────────────────────────────────────────────────────────────────

describe('frontmatter roundtrip with populated triage/lifecycle objects', () => {
  let tmpDir;

  beforeEach(() => {
    tmpDir = createTempProject();
  });

  afterEach(() => {
    cleanup(tmpDir);
  });

  test('signal with populated triage object validates and preserves colon-containing timestamps', () => {
    const signalPath = path.join(tmpDir, 'triaged-signal.md');
    fs.writeFileSync(signalPath, `---
id: sig-2026-02-28-roundtrip-test
type: signal
project: test-project
tags: [roundtrip, triage, lifecycle]
created: "2026-02-28T10:00:00Z"
updated: "2026-02-28T11:00:00Z"
severity: notable
signal_type: deviation
signal_category: negative
lifecycle_state: triaged
confidence: high
confidence_basis: test roundtrip validation
triage:
  decision: address
  rationale: Cluster of 4 deviation signals about plan accuracy
  priority: medium
  by: reflector
  at: "2026-02-28T10:00:00Z"
remediation:
verification:
lifecycle_log:
  - "detected->triaged by reflector at 2026-02-28T10:00:00Z: cluster triage"
---

# Roundtrip Test Signal

Body content should be preserved exactly.
`);

    // Validate the hand-written signal
    const result = runGsdTools(`frontmatter validate ${signalPath} --schema signal`, tmpDir);
    assert.ok(result.success, `Validation failed: ${result.error}`);
    const output = JSON.parse(result.output);
    assert.strictEqual(output.valid, true, `Signal should be valid, got missing: ${output.missing}`);
    assert.strictEqual(output.schema, 'signal');

    // Read the file content back and verify key fields are present
    const content = fs.readFileSync(signalPath, 'utf-8');
    assert.ok(content.includes('lifecycle_state: triaged'), 'lifecycle_state should be preserved');
    assert.ok(content.includes('decision: address'), 'triage.decision should be preserved');
    assert.ok(content.includes('2026-02-28T10:00:00Z'), 'timestamp with colons should be preserved');
    assert.ok(content.includes('Body content should be preserved exactly'), 'body should be preserved');
  });

  test('signal with populated triage survives write-read-validate roundtrip via spliceFrontmatter', () => {
    // Write initial signal WITHOUT triage
    const signalPath = path.join(tmpDir, 'pre-triage-signal.md');
    const initialContent = `---
id: sig-2026-02-28-pre-triage
type: signal
project: test-project
tags: [roundtrip, pre-triage]
created: "2026-02-28T10:00:00Z"
severity: notable
signal_type: deviation
signal_category: negative
lifecycle_state: detected
confidence: medium
confidence_basis: initial detection
triage:
remediation:
verification:
lifecycle_log:
  - "created -> detected by sensor at 2026-02-28T09:00:00Z"
---

# Pre-Triage Signal

Original body content.
`;
    fs.writeFileSync(signalPath, initialContent);

    // Validate initial state
    const result1 = runGsdTools(`frontmatter validate ${signalPath} --schema signal`, tmpDir);
    assert.ok(result1.success, `Initial validation failed: ${result1.error}`);
    const output1 = JSON.parse(result1.output);
    assert.strictEqual(output1.valid, true, 'Initial signal should be valid');

    // Now simulate what the reflector does: read, parse, modify mutable fields, write back
    // We use a small node script that exercises extractFrontmatter + spliceFrontmatter
    const scriptPath = path.join(tmpDir, 'roundtrip.js');
    fs.writeFileSync(scriptPath, `
      const fs = require('fs');
      const toolsSrc = fs.readFileSync('${TOOLS_PATH.replace(/\\/g, '\\\\')}', 'utf-8');

      // Extract the three functions from gsd-tools.js source
      const extractFn = toolsSrc.match(/function extractFrontmatter\\(content\\)[\\s\\S]+?^\\}/m)[0];
      const reconstructFn = toolsSrc.match(/function reconstructFrontmatter\\(obj\\)[\\s\\S]+?^\\}/m)[0];
      const spliceFn = toolsSrc.match(/function spliceFrontmatter\\(content, newObj\\)[\\s\\S]+?^\\}/m)[0];
      eval(extractFn);
      eval(reconstructFn);
      eval(spliceFn);

      // Read the signal
      const content = fs.readFileSync('${signalPath.replace(/\\/g, '\\\\')}', 'utf-8');
      const fm = extractFrontmatter(content);

      // Verify frozen fields before modification
      const frozenBefore = JSON.stringify({
        id: fm.id, type: fm.type, project: fm.project,
        tags: fm.tags, created: fm.created, severity: fm.severity,
        signal_type: fm.signal_type, signal_category: fm.signal_category,
        confidence: fm.confidence, confidence_basis: fm.confidence_basis
      });

      // Modify ONLY mutable fields (simulating reflector triage write)
      fm.lifecycle_state = 'triaged';
      fm.updated = '2026-02-28T11:00:00Z';
      fm.triage = {
        decision: 'address',
        rationale: 'Cluster of 4 deviation signals about plan accuracy',
        priority: 'medium',
        by: 'reflector',
        at: '2026-02-28T10:30:00Z'
      };
      if (!Array.isArray(fm.lifecycle_log)) fm.lifecycle_log = [];
      fm.lifecycle_log.push('detected->triaged by reflector at 2026-02-28T10:30:00Z: cluster triage');

      // Write back via spliceFrontmatter
      const newContent = spliceFrontmatter(content, fm);
      fs.writeFileSync('${signalPath.replace(/\\/g, '\\\\')}', newContent);

      // Read back and verify roundtrip
      const reread = fs.readFileSync('${signalPath.replace(/\\/g, '\\\\')}', 'utf-8');
      const fm2 = extractFrontmatter(reread);

      // Verify frozen fields unchanged
      const frozenAfter = JSON.stringify({
        id: fm2.id, type: fm2.type, project: fm2.project,
        tags: fm2.tags, created: fm2.created, severity: fm2.severity,
        signal_type: fm2.signal_type, signal_category: fm2.signal_category,
        confidence: fm2.confidence, confidence_basis: fm2.confidence_basis
      });

      const result = {
        frozen_match: frozenBefore === frozenAfter,
        lifecycle_state: fm2.lifecycle_state,
        triage_decision: fm2.triage && fm2.triage.decision,
        triage_rationale: fm2.triage && fm2.triage.rationale,
        triage_priority: fm2.triage && fm2.triage.priority,
        triage_by: fm2.triage && fm2.triage.by,
        triage_at: fm2.triage && fm2.triage.at,
        lifecycle_log_count: Array.isArray(fm2.lifecycle_log) ? fm2.lifecycle_log.length : 0,
        lifecycle_log_last: Array.isArray(fm2.lifecycle_log) ? fm2.lifecycle_log[fm2.lifecycle_log.length - 1] : null,
        body_preserved: reread.includes('Original body content'),
        frozen_before: frozenBefore,
        frozen_after: frozenAfter
      };
      console.log(JSON.stringify(result));
    `);

    const roundtripResult = execSync(`node "${scriptPath}"`, { encoding: 'utf-8', cwd: tmpDir });
    const rt = JSON.parse(roundtripResult.trim());

    // Assert frozen fields survived roundtrip
    assert.strictEqual(rt.frozen_match, true,
      `Frozen fields changed during roundtrip!\nBefore: ${rt.frozen_before}\nAfter: ${rt.frozen_after}`);

    // Assert mutable fields were written correctly
    assert.strictEqual(rt.lifecycle_state, 'triaged', 'lifecycle_state should be triaged after roundtrip');
    assert.strictEqual(rt.triage_decision, 'address', 'triage.decision should survive roundtrip');
    assert.strictEqual(rt.triage_rationale, 'Cluster of 4 deviation signals about plan accuracy',
      'triage.rationale should survive roundtrip');
    assert.strictEqual(rt.triage_priority, 'medium', 'triage.priority should survive roundtrip');
    assert.strictEqual(rt.triage_by, 'reflector', 'triage.by should survive roundtrip');
    assert.strictEqual(rt.triage_at, '2026-02-28T10:30:00Z',
      'triage.at timestamp with colons should survive roundtrip');
    assert.strictEqual(rt.lifecycle_log_count, 2, 'lifecycle_log should have 2 entries after append');
    assert.ok(rt.lifecycle_log_last.includes('detected->triaged'),
      'lifecycle_log last entry should contain the triage transition');
    assert.ok(rt.lifecycle_log_last.includes('2026-02-28T10:30:00Z'),
      'lifecycle_log last entry should contain timestamp with colons');
    assert.strictEqual(rt.body_preserved, true, 'Body content should survive roundtrip');

    // Validate the modified file still passes schema validation
    const result2 = runGsdTools(`frontmatter validate ${signalPath} --schema signal`, tmpDir);
    assert.ok(result2.success, `Post-roundtrip validation failed: ${result2.error}`);
    const output2 = JSON.parse(result2.output);
    assert.strictEqual(output2.valid, true,
      `Signal should still be valid after roundtrip, got missing: ${output2.missing}`);
  });

  test('critical signal triage requires evidence (backward_compat constraint)', () => {
    // A critical signal WITHOUT lifecycle_state should pass (backward_compat)
    const signalPath = path.join(tmpDir, 'critical-no-lifecycle.md');
    fs.writeFileSync(signalPath, `---
id: sig-2026-02-28-critical-backcompat
type: signal
project: test-project
tags: [critical, backcompat]
created: "2026-02-28T10:00:00Z"
severity: critical
signal_type: deviation
---

# Critical signal without lifecycle_state
`);

    const result1 = runGsdTools(`frontmatter validate ${signalPath} --schema signal`, tmpDir);
    const output1 = JSON.parse(result1.output);
    assert.strictEqual(output1.valid, true,
      'Critical signal without lifecycle_state should pass via backward_compat');
    assert.ok(output1.warnings.some(w => w.includes('backward_compat')),
      'Should have backward_compat warning for evidence');

    // Now add lifecycle_state WITHOUT evidence -- should FAIL
    const signalPath2 = path.join(tmpDir, 'critical-with-lifecycle-no-evidence.md');
    fs.writeFileSync(signalPath2, `---
id: sig-2026-02-28-critical-broken
type: signal
project: test-project
tags: [critical, broken]
created: "2026-02-28T10:00:00Z"
severity: critical
signal_type: deviation
lifecycle_state: triaged
triage:
  decision: address
  rationale: test
  priority: high
  by: reflector
  at: "2026-02-28T10:00:00Z"
---

# Critical signal with lifecycle_state but no evidence
`);

    const result2 = runGsdTools(`frontmatter validate ${signalPath2} --schema signal`, tmpDir);
    const output2 = JSON.parse(result2.output);
    assert.strictEqual(output2.valid, false,
      'Critical signal WITH lifecycle_state but WITHOUT evidence should FAIL');
    assert.ok(output2.missing.includes('evidence'),
      'Missing should include evidence');

    // Now add lifecycle_state WITH evidence -- should PASS
    const signalPath3 = path.join(tmpDir, 'critical-with-lifecycle-and-evidence.md');
    fs.writeFileSync(signalPath3, `---
id: sig-2026-02-28-critical-correct
type: signal
project: test-project
tags: [critical, correct]
created: "2026-02-28T10:00:00Z"
severity: critical
signal_type: deviation
lifecycle_state: triaged
evidence:
  supporting:
    - "Observed issue X in execution log"
  counter: []
triage:
  decision: address
  rationale: test
  priority: high
  by: reflector
  at: "2026-02-28T10:00:00Z"
---

# Critical signal with lifecycle_state AND evidence
`);

    const result3 = runGsdTools(`frontmatter validate ${signalPath3} --schema signal`, tmpDir);
    const output3 = JSON.parse(result3.output);
    assert.strictEqual(output3.valid, true,
      'Critical signal with lifecycle_state AND evidence should pass');
  });
});
