/**
 * GSD Tools Tests
 */

const { test, describe, beforeEach, afterEach } = require('node:test');
const assert = require('node:assert');
const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const TOOLS_PATH = path.join(__dirname, 'gsd-tools.js');

// Helper to run gsd-tools command
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

// Create temp directory structure
function createTempProject() {
  const tmpDir = fs.mkdtempSync(path.join(require('os').tmpdir(), 'gsd-test-'));
  fs.mkdirSync(path.join(tmpDir, '.planning', 'phases'), { recursive: true });
  return tmpDir;
}

function cleanup(tmpDir) {
  fs.rmSync(tmpDir, { recursive: true, force: true });
}

describe('history-digest command', () => {
  let tmpDir;

  beforeEach(() => {
    tmpDir = createTempProject();
  });

  afterEach(() => {
    cleanup(tmpDir);
  });

  test('empty phases directory returns valid schema', () => {
    const result = runGsdTools('history-digest', tmpDir);
    assert.ok(result.success, `Command failed: ${result.error}`);

    const digest = JSON.parse(result.output);

    assert.deepStrictEqual(digest.phases, {}, 'phases should be empty object');
    assert.deepStrictEqual(digest.decisions, [], 'decisions should be empty array');
    assert.deepStrictEqual(digest.tech_stack, [], 'tech_stack should be empty array');
  });

  test('nested frontmatter fields extracted correctly', () => {
    // Create phase directory with SUMMARY containing nested frontmatter
    const phaseDir = path.join(tmpDir, '.planning', 'phases', '01-foundation');
    fs.mkdirSync(phaseDir, { recursive: true });

    const summaryContent = `---
phase: "01"
name: "Foundation Setup"
dependency-graph:
  provides:
    - "Database schema"
    - "Auth system"
  affects:
    - "API layer"
tech-stack:
  added:
    - "prisma"
    - "jose"
patterns-established:
  - "Repository pattern"
  - "JWT auth flow"
key-decisions:
  - "Use Prisma over Drizzle"
  - "JWT in httpOnly cookies"
---

# Summary content here
`;

    fs.writeFileSync(path.join(phaseDir, '01-01-SUMMARY.md'), summaryContent);

    const result = runGsdTools('history-digest', tmpDir);
    assert.ok(result.success, `Command failed: ${result.error}`);

    const digest = JSON.parse(result.output);

    // Check nested dependency-graph.provides
    assert.ok(digest.phases['01'], 'Phase 01 should exist');
    assert.deepStrictEqual(
      digest.phases['01'].provides.sort(),
      ['Auth system', 'Database schema'],
      'provides should contain nested values'
    );

    // Check nested dependency-graph.affects
    assert.deepStrictEqual(
      digest.phases['01'].affects,
      ['API layer'],
      'affects should contain nested values'
    );

    // Check nested tech-stack.added
    assert.deepStrictEqual(
      digest.tech_stack.sort(),
      ['jose', 'prisma'],
      'tech_stack should contain nested values'
    );

    // Check patterns-established (flat array)
    assert.deepStrictEqual(
      digest.phases['01'].patterns.sort(),
      ['JWT auth flow', 'Repository pattern'],
      'patterns should be extracted'
    );

    // Check key-decisions
    assert.strictEqual(digest.decisions.length, 2, 'Should have 2 decisions');
    assert.ok(
      digest.decisions.some(d => d.decision === 'Use Prisma over Drizzle'),
      'Should contain first decision'
    );
  });

  test('multiple phases merged into single digest', () => {
    // Create phase 01
    const phase01Dir = path.join(tmpDir, '.planning', 'phases', '01-foundation');
    fs.mkdirSync(phase01Dir, { recursive: true });
    fs.writeFileSync(
      path.join(phase01Dir, '01-01-SUMMARY.md'),
      `---
phase: "01"
name: "Foundation"
provides:
  - "Database"
patterns-established:
  - "Pattern A"
key-decisions:
  - "Decision 1"
---
`
    );

    // Create phase 02
    const phase02Dir = path.join(tmpDir, '.planning', 'phases', '02-api');
    fs.mkdirSync(phase02Dir, { recursive: true });
    fs.writeFileSync(
      path.join(phase02Dir, '02-01-SUMMARY.md'),
      `---
phase: "02"
name: "API"
provides:
  - "REST endpoints"
patterns-established:
  - "Pattern B"
key-decisions:
  - "Decision 2"
tech-stack:
  added:
    - "zod"
---
`
    );

    const result = runGsdTools('history-digest', tmpDir);
    assert.ok(result.success, `Command failed: ${result.error}`);

    const digest = JSON.parse(result.output);

    // Both phases present
    assert.ok(digest.phases['01'], 'Phase 01 should exist');
    assert.ok(digest.phases['02'], 'Phase 02 should exist');

    // Decisions merged
    assert.strictEqual(digest.decisions.length, 2, 'Should have 2 decisions total');

    // Tech stack merged
    assert.deepStrictEqual(digest.tech_stack, ['zod'], 'tech_stack should have zod');
  });

  test('malformed SUMMARY.md skipped gracefully', () => {
    const phaseDir = path.join(tmpDir, '.planning', 'phases', '01-test');
    fs.mkdirSync(phaseDir, { recursive: true });

    // Valid summary
    fs.writeFileSync(
      path.join(phaseDir, '01-01-SUMMARY.md'),
      `---
phase: "01"
provides:
  - "Valid feature"
---
`
    );

    // Malformed summary (no frontmatter)
    fs.writeFileSync(
      path.join(phaseDir, '01-02-SUMMARY.md'),
      `# Just a heading
No frontmatter here
`
    );

    // Another malformed summary (broken YAML)
    fs.writeFileSync(
      path.join(phaseDir, '01-03-SUMMARY.md'),
      `---
broken: [unclosed
---
`
    );

    const result = runGsdTools('history-digest', tmpDir);
    assert.ok(result.success, `Command should succeed despite malformed files: ${result.error}`);

    const digest = JSON.parse(result.output);
    assert.ok(digest.phases['01'], 'Phase 01 should exist');
    assert.ok(
      digest.phases['01'].provides.includes('Valid feature'),
      'Valid feature should be extracted'
    );
  });

  test('flat provides field still works (backward compatibility)', () => {
    const phaseDir = path.join(tmpDir, '.planning', 'phases', '01-test');
    fs.mkdirSync(phaseDir, { recursive: true });

    fs.writeFileSync(
      path.join(phaseDir, '01-01-SUMMARY.md'),
      `---
phase: "01"
provides:
  - "Direct provides"
---
`
    );

    const result = runGsdTools('history-digest', tmpDir);
    assert.ok(result.success, `Command failed: ${result.error}`);

    const digest = JSON.parse(result.output);
    assert.deepStrictEqual(
      digest.phases['01'].provides,
      ['Direct provides'],
      'Direct provides should work'
    );
  });

  test('inline array syntax supported', () => {
    const phaseDir = path.join(tmpDir, '.planning', 'phases', '01-test');
    fs.mkdirSync(phaseDir, { recursive: true });

    fs.writeFileSync(
      path.join(phaseDir, '01-01-SUMMARY.md'),
      `---
phase: "01"
provides: [Feature A, Feature B]
patterns-established: ["Pattern X", "Pattern Y"]
---
`
    );

    const result = runGsdTools('history-digest', tmpDir);
    assert.ok(result.success, `Command failed: ${result.error}`);

    const digest = JSON.parse(result.output);
    assert.deepStrictEqual(
      digest.phases['01'].provides.sort(),
      ['Feature A', 'Feature B'],
      'Inline array should work'
    );
    assert.deepStrictEqual(
      digest.phases['01'].patterns.sort(),
      ['Pattern X', 'Pattern Y'],
      'Inline quoted array should work'
    );
  });
});

// ─────────────────────────────────────────────────────────────────────────────
// phases list command
// ─────────────────────────────────────────────────────────────────────────────

describe('phases list command', () => {
  let tmpDir;

  beforeEach(() => {
    tmpDir = createTempProject();
  });

  afterEach(() => {
    cleanup(tmpDir);
  });

  test('empty phases directory returns empty array', () => {
    const result = runGsdTools('phases list', tmpDir);
    assert.ok(result.success, `Command failed: ${result.error}`);

    const output = JSON.parse(result.output);
    assert.deepStrictEqual(output.directories, [], 'directories should be empty');
    assert.strictEqual(output.count, 0, 'count should be 0');
  });

  test('lists phase directories sorted numerically', () => {
    // Create out-of-order directories
    fs.mkdirSync(path.join(tmpDir, '.planning', 'phases', '10-final'), { recursive: true });
    fs.mkdirSync(path.join(tmpDir, '.planning', 'phases', '02-api'), { recursive: true });
    fs.mkdirSync(path.join(tmpDir, '.planning', 'phases', '01-foundation'), { recursive: true });

    const result = runGsdTools('phases list', tmpDir);
    assert.ok(result.success, `Command failed: ${result.error}`);

    const output = JSON.parse(result.output);
    assert.strictEqual(output.count, 3, 'should have 3 directories');
    assert.deepStrictEqual(
      output.directories,
      ['01-foundation', '02-api', '10-final'],
      'should be sorted numerically'
    );
  });

  test('handles decimal phases in sort order', () => {
    fs.mkdirSync(path.join(tmpDir, '.planning', 'phases', '02-api'), { recursive: true });
    fs.mkdirSync(path.join(tmpDir, '.planning', 'phases', '02.1-hotfix'), { recursive: true });
    fs.mkdirSync(path.join(tmpDir, '.planning', 'phases', '02.2-patch'), { recursive: true });
    fs.mkdirSync(path.join(tmpDir, '.planning', 'phases', '03-ui'), { recursive: true });

    const result = runGsdTools('phases list', tmpDir);
    assert.ok(result.success, `Command failed: ${result.error}`);

    const output = JSON.parse(result.output);
    assert.deepStrictEqual(
      output.directories,
      ['02-api', '02.1-hotfix', '02.2-patch', '03-ui'],
      'decimal phases should sort correctly between whole numbers'
    );
  });

  test('--type plans lists only PLAN.md files', () => {
    const phaseDir = path.join(tmpDir, '.planning', 'phases', '01-test');
    fs.mkdirSync(phaseDir, { recursive: true });
    fs.writeFileSync(path.join(phaseDir, '01-01-PLAN.md'), '# Plan 1');
    fs.writeFileSync(path.join(phaseDir, '01-02-PLAN.md'), '# Plan 2');
    fs.writeFileSync(path.join(phaseDir, '01-01-SUMMARY.md'), '# Summary');
    fs.writeFileSync(path.join(phaseDir, 'RESEARCH.md'), '# Research');

    const result = runGsdTools('phases list --type plans', tmpDir);
    assert.ok(result.success, `Command failed: ${result.error}`);

    const output = JSON.parse(result.output);
    assert.deepStrictEqual(
      output.files.sort(),
      ['01-01-PLAN.md', '01-02-PLAN.md'],
      'should list only PLAN files'
    );
  });

  test('--type summaries lists only SUMMARY.md files', () => {
    const phaseDir = path.join(tmpDir, '.planning', 'phases', '01-test');
    fs.mkdirSync(phaseDir, { recursive: true });
    fs.writeFileSync(path.join(phaseDir, '01-01-PLAN.md'), '# Plan');
    fs.writeFileSync(path.join(phaseDir, '01-01-SUMMARY.md'), '# Summary 1');
    fs.writeFileSync(path.join(phaseDir, '01-02-SUMMARY.md'), '# Summary 2');

    const result = runGsdTools('phases list --type summaries', tmpDir);
    assert.ok(result.success, `Command failed: ${result.error}`);

    const output = JSON.parse(result.output);
    assert.deepStrictEqual(
      output.files.sort(),
      ['01-01-SUMMARY.md', '01-02-SUMMARY.md'],
      'should list only SUMMARY files'
    );
  });

  test('--phase filters to specific phase directory', () => {
    const phase01 = path.join(tmpDir, '.planning', 'phases', '01-foundation');
    const phase02 = path.join(tmpDir, '.planning', 'phases', '02-api');
    fs.mkdirSync(phase01, { recursive: true });
    fs.mkdirSync(phase02, { recursive: true });
    fs.writeFileSync(path.join(phase01, '01-01-PLAN.md'), '# Plan');
    fs.writeFileSync(path.join(phase02, '02-01-PLAN.md'), '# Plan');

    const result = runGsdTools('phases list --type plans --phase 01', tmpDir);
    assert.ok(result.success, `Command failed: ${result.error}`);

    const output = JSON.parse(result.output);
    assert.deepStrictEqual(output.files, ['01-01-PLAN.md'], 'should only list phase 01 plans');
    assert.strictEqual(output.phase_dir, 'foundation', 'should report phase name without number prefix');
  });
});

// ─────────────────────────────────────────────────────────────────────────────
// roadmap get-phase command
// ─────────────────────────────────────────────────────────────────────────────

describe('roadmap get-phase command', () => {
  let tmpDir;

  beforeEach(() => {
    tmpDir = createTempProject();
  });

  afterEach(() => {
    cleanup(tmpDir);
  });

  test('extracts phase section from ROADMAP.md', () => {
    fs.writeFileSync(
      path.join(tmpDir, '.planning', 'ROADMAP.md'),
      `# Roadmap v1.0

## Phases

### Phase 1: Foundation
**Goal:** Set up project infrastructure
**Plans:** 2 plans

Some description here.

### Phase 2: API
**Goal:** Build REST API
**Plans:** 3 plans
`
    );

    const result = runGsdTools('roadmap get-phase 1', tmpDir);
    assert.ok(result.success, `Command failed: ${result.error}`);

    const output = JSON.parse(result.output);
    assert.strictEqual(output.found, true, 'phase should be found');
    assert.strictEqual(output.phase_number, '1', 'phase number correct');
    assert.strictEqual(output.phase_name, 'Foundation', 'phase name extracted');
    assert.strictEqual(output.goal, 'Set up project infrastructure', 'goal extracted');
  });

  test('returns not found for missing phase', () => {
    fs.writeFileSync(
      path.join(tmpDir, '.planning', 'ROADMAP.md'),
      `# Roadmap v1.0

### Phase 1: Foundation
**Goal:** Set up project
`
    );

    const result = runGsdTools('roadmap get-phase 5', tmpDir);
    assert.ok(result.success, `Command failed: ${result.error}`);

    const output = JSON.parse(result.output);
    assert.strictEqual(output.found, false, 'phase should not be found');
  });

  test('handles decimal phase numbers', () => {
    fs.writeFileSync(
      path.join(tmpDir, '.planning', 'ROADMAP.md'),
      `# Roadmap

### Phase 2: Main
**Goal:** Main work

### Phase 2.1: Hotfix
**Goal:** Emergency fix
`
    );

    const result = runGsdTools('roadmap get-phase 2.1', tmpDir);
    assert.ok(result.success, `Command failed: ${result.error}`);

    const output = JSON.parse(result.output);
    assert.strictEqual(output.found, true, 'decimal phase should be found');
    assert.strictEqual(output.phase_name, 'Hotfix', 'phase name correct');
    assert.strictEqual(output.goal, 'Emergency fix', 'goal extracted');
  });

  test('extracts full section content', () => {
    fs.writeFileSync(
      path.join(tmpDir, '.planning', 'ROADMAP.md'),
      `# Roadmap

### Phase 1: Setup
**Goal:** Initialize everything

This phase covers:
- Database setup
- Auth configuration
- CI/CD pipeline

### Phase 2: Build
**Goal:** Build features
`
    );

    const result = runGsdTools('roadmap get-phase 1', tmpDir);
    assert.ok(result.success, `Command failed: ${result.error}`);

    const output = JSON.parse(result.output);
    assert.ok(output.section.includes('Database setup'), 'section includes description');
    assert.ok(output.section.includes('CI/CD pipeline'), 'section includes all bullets');
    assert.ok(!output.section.includes('Phase 2'), 'section does not include next phase');
  });

  test('handles missing ROADMAP.md gracefully', () => {
    const result = runGsdTools('roadmap get-phase 1', tmpDir);
    assert.ok(result.success, `Command failed: ${result.error}`);

    const output = JSON.parse(result.output);
    assert.strictEqual(output.found, false, 'should return not found');
    assert.strictEqual(output.error, 'ROADMAP.md not found', 'should explain why');
  });
});

// ─────────────────────────────────────────────────────────────────────────────
// phase next-decimal command
// ─────────────────────────────────────────────────────────────────────────────

describe('phase next-decimal command', () => {
  let tmpDir;

  beforeEach(() => {
    tmpDir = createTempProject();
  });

  afterEach(() => {
    cleanup(tmpDir);
  });

  test('returns X.1 when no decimal phases exist', () => {
    fs.mkdirSync(path.join(tmpDir, '.planning', 'phases', '06-feature'), { recursive: true });
    fs.mkdirSync(path.join(tmpDir, '.planning', 'phases', '07-next'), { recursive: true });

    const result = runGsdTools('phase next-decimal 06', tmpDir);
    assert.ok(result.success, `Command failed: ${result.error}`);

    const output = JSON.parse(result.output);
    assert.strictEqual(output.next, '06.1', 'should return 06.1');
    assert.deepStrictEqual(output.existing, [], 'no existing decimals');
  });

  test('increments from existing decimal phases', () => {
    fs.mkdirSync(path.join(tmpDir, '.planning', 'phases', '06-feature'), { recursive: true });
    fs.mkdirSync(path.join(tmpDir, '.planning', 'phases', '06.1-hotfix'), { recursive: true });
    fs.mkdirSync(path.join(tmpDir, '.planning', 'phases', '06.2-patch'), { recursive: true });

    const result = runGsdTools('phase next-decimal 06', tmpDir);
    assert.ok(result.success, `Command failed: ${result.error}`);

    const output = JSON.parse(result.output);
    assert.strictEqual(output.next, '06.3', 'should return 06.3');
    assert.deepStrictEqual(output.existing, ['06.1', '06.2'], 'lists existing decimals');
  });

  test('handles gaps in decimal sequence', () => {
    fs.mkdirSync(path.join(tmpDir, '.planning', 'phases', '06-feature'), { recursive: true });
    fs.mkdirSync(path.join(tmpDir, '.planning', 'phases', '06.1-first'), { recursive: true });
    fs.mkdirSync(path.join(tmpDir, '.planning', 'phases', '06.3-third'), { recursive: true });

    const result = runGsdTools('phase next-decimal 06', tmpDir);
    assert.ok(result.success, `Command failed: ${result.error}`);

    const output = JSON.parse(result.output);
    // Should take next after highest, not fill gap
    assert.strictEqual(output.next, '06.4', 'should return 06.4, not fill gap at 06.2');
  });

  test('handles single-digit phase input', () => {
    fs.mkdirSync(path.join(tmpDir, '.planning', 'phases', '06-feature'), { recursive: true });

    const result = runGsdTools('phase next-decimal 6', tmpDir);
    assert.ok(result.success, `Command failed: ${result.error}`);

    const output = JSON.parse(result.output);
    assert.strictEqual(output.next, '06.1', 'should normalize to 06.1');
    assert.strictEqual(output.base_phase, '06', 'base phase should be padded');
  });

  test('returns error if base phase does not exist', () => {
    fs.mkdirSync(path.join(tmpDir, '.planning', 'phases', '01-start'), { recursive: true });

    const result = runGsdTools('phase next-decimal 06', tmpDir);
    assert.ok(result.success, `Command should succeed: ${result.error}`);

    const output = JSON.parse(result.output);
    assert.strictEqual(output.found, false, 'base phase not found');
    assert.strictEqual(output.next, '06.1', 'should still suggest 06.1');
  });
});

// ─────────────────────────────────────────────────────────────────────────────
// phase-plan-index command
// ─────────────────────────────────────────────────────────────────────────────

describe('phase-plan-index command', () => {
  let tmpDir;

  beforeEach(() => {
    tmpDir = createTempProject();
  });

  afterEach(() => {
    cleanup(tmpDir);
  });

  test('empty phase directory returns empty plans array', () => {
    fs.mkdirSync(path.join(tmpDir, '.planning', 'phases', '03-api'), { recursive: true });

    const result = runGsdTools('phase-plan-index 03', tmpDir);
    assert.ok(result.success, `Command failed: ${result.error}`);

    const output = JSON.parse(result.output);
    assert.strictEqual(output.phase, '03', 'phase number correct');
    assert.deepStrictEqual(output.plans, [], 'plans should be empty');
    assert.deepStrictEqual(output.waves, {}, 'waves should be empty');
    assert.deepStrictEqual(output.incomplete, [], 'incomplete should be empty');
    assert.strictEqual(output.has_checkpoints, false, 'no checkpoints');
  });

  test('extracts single plan with frontmatter', () => {
    const phaseDir = path.join(tmpDir, '.planning', 'phases', '03-api');
    fs.mkdirSync(phaseDir, { recursive: true });

    fs.writeFileSync(
      path.join(phaseDir, '03-01-PLAN.md'),
      `---
wave: 1
autonomous: true
objective: Set up database schema
files-modified: [prisma/schema.prisma, src/lib/db.ts]
---

## Task 1: Create schema
## Task 2: Generate client
`
    );

    const result = runGsdTools('phase-plan-index 03', tmpDir);
    assert.ok(result.success, `Command failed: ${result.error}`);

    const output = JSON.parse(result.output);
    assert.strictEqual(output.plans.length, 1, 'should have 1 plan');
    assert.strictEqual(output.plans[0].id, '03-01', 'plan id correct');
    assert.strictEqual(output.plans[0].wave, 1, 'wave extracted');
    assert.strictEqual(output.plans[0].autonomous, true, 'autonomous extracted');
    assert.strictEqual(output.plans[0].objective, 'Set up database schema', 'objective extracted');
    assert.deepStrictEqual(output.plans[0].files_modified, ['prisma/schema.prisma', 'src/lib/db.ts'], 'files extracted');
    assert.strictEqual(output.plans[0].task_count, 2, 'task count correct');
    assert.strictEqual(output.plans[0].has_summary, false, 'no summary yet');
  });

  test('groups multiple plans by wave', () => {
    const phaseDir = path.join(tmpDir, '.planning', 'phases', '03-api');
    fs.mkdirSync(phaseDir, { recursive: true });

    fs.writeFileSync(
      path.join(phaseDir, '03-01-PLAN.md'),
      `---
wave: 1
autonomous: true
objective: Database setup
---

## Task 1: Schema
`
    );

    fs.writeFileSync(
      path.join(phaseDir, '03-02-PLAN.md'),
      `---
wave: 1
autonomous: true
objective: Auth setup
---

## Task 1: JWT
`
    );

    fs.writeFileSync(
      path.join(phaseDir, '03-03-PLAN.md'),
      `---
wave: 2
autonomous: false
objective: API routes
---

## Task 1: Routes
`
    );

    const result = runGsdTools('phase-plan-index 03', tmpDir);
    assert.ok(result.success, `Command failed: ${result.error}`);

    const output = JSON.parse(result.output);
    assert.strictEqual(output.plans.length, 3, 'should have 3 plans');
    assert.deepStrictEqual(output.waves['1'], ['03-01', '03-02'], 'wave 1 has 2 plans');
    assert.deepStrictEqual(output.waves['2'], ['03-03'], 'wave 2 has 1 plan');
  });

  test('detects incomplete plans (no matching summary)', () => {
    const phaseDir = path.join(tmpDir, '.planning', 'phases', '03-api');
    fs.mkdirSync(phaseDir, { recursive: true });

    // Plan with summary
    fs.writeFileSync(path.join(phaseDir, '03-01-PLAN.md'), `---\nwave: 1\n---\n## Task 1`);
    fs.writeFileSync(path.join(phaseDir, '03-01-SUMMARY.md'), `# Summary`);

    // Plan without summary
    fs.writeFileSync(path.join(phaseDir, '03-02-PLAN.md'), `---\nwave: 2\n---\n## Task 1`);

    const result = runGsdTools('phase-plan-index 03', tmpDir);
    assert.ok(result.success, `Command failed: ${result.error}`);

    const output = JSON.parse(result.output);
    assert.strictEqual(output.plans[0].has_summary, true, 'first plan has summary');
    assert.strictEqual(output.plans[1].has_summary, false, 'second plan has no summary');
    assert.deepStrictEqual(output.incomplete, ['03-02'], 'incomplete list correct');
  });

  test('detects checkpoints (autonomous: false)', () => {
    const phaseDir = path.join(tmpDir, '.planning', 'phases', '03-api');
    fs.mkdirSync(phaseDir, { recursive: true });

    fs.writeFileSync(
      path.join(phaseDir, '03-01-PLAN.md'),
      `---
wave: 1
autonomous: false
objective: Manual review needed
---

## Task 1: Review
`
    );

    const result = runGsdTools('phase-plan-index 03', tmpDir);
    assert.ok(result.success, `Command failed: ${result.error}`);

    const output = JSON.parse(result.output);
    assert.strictEqual(output.has_checkpoints, true, 'should detect checkpoint');
    assert.strictEqual(output.plans[0].autonomous, false, 'plan marked non-autonomous');
  });

  test('phase not found returns error', () => {
    const result = runGsdTools('phase-plan-index 99', tmpDir);
    assert.ok(result.success, `Command should succeed: ${result.error}`);

    const output = JSON.parse(result.output);
    assert.strictEqual(output.error, 'Phase not found', 'should report phase not found');
  });
});

// ─────────────────────────────────────────────────────────────────────────────
// state-snapshot command
// ─────────────────────────────────────────────────────────────────────────────

describe('state-snapshot command', () => {
  let tmpDir;

  beforeEach(() => {
    tmpDir = createTempProject();
  });

  afterEach(() => {
    cleanup(tmpDir);
  });

  test('missing STATE.md returns error', () => {
    const result = runGsdTools('state-snapshot', tmpDir);
    assert.ok(result.success, `Command should succeed: ${result.error}`);

    const output = JSON.parse(result.output);
    assert.strictEqual(output.error, 'STATE.md not found', 'should report missing file');
  });

  test('extracts basic fields from STATE.md', () => {
    fs.writeFileSync(
      path.join(tmpDir, '.planning', 'STATE.md'),
      `# Project State

**Current Phase:** 03
**Current Phase Name:** API Layer
**Total Phases:** 6
**Current Plan:** 03-02
**Total Plans in Phase:** 3
**Status:** In progress
**Progress:** 45%
**Last Activity:** 2024-01-15
**Last Activity Description:** Completed 03-01-PLAN.md
`
    );

    const result = runGsdTools('state-snapshot', tmpDir);
    assert.ok(result.success, `Command failed: ${result.error}`);

    const output = JSON.parse(result.output);
    assert.strictEqual(output.current_phase, '03', 'current phase extracted');
    assert.strictEqual(output.current_phase_name, 'API Layer', 'phase name extracted');
    assert.strictEqual(output.total_phases, 6, 'total phases extracted');
    assert.strictEqual(output.current_plan, '03-02', 'current plan extracted');
    assert.strictEqual(output.total_plans_in_phase, 3, 'total plans extracted');
    assert.strictEqual(output.status, 'In progress', 'status extracted');
    assert.strictEqual(output.progress_percent, 45, 'progress extracted');
    assert.strictEqual(output.last_activity, '2024-01-15', 'last activity date extracted');
  });

  test('extracts decisions table', () => {
    fs.writeFileSync(
      path.join(tmpDir, '.planning', 'STATE.md'),
      `# Project State

**Current Phase:** 01

## Decisions Made

| Phase | Decision | Rationale |
|-------|----------|-----------|
| 01 | Use Prisma | Better DX than raw SQL |
| 02 | JWT auth | Stateless authentication |
`
    );

    const result = runGsdTools('state-snapshot', tmpDir);
    assert.ok(result.success, `Command failed: ${result.error}`);

    const output = JSON.parse(result.output);
    assert.strictEqual(output.decisions.length, 2, 'should have 2 decisions');
    assert.strictEqual(output.decisions[0].phase, '01', 'first decision phase');
    assert.strictEqual(output.decisions[0].summary, 'Use Prisma', 'first decision summary');
    assert.strictEqual(output.decisions[0].rationale, 'Better DX than raw SQL', 'first decision rationale');
  });

  test('extracts blockers list', () => {
    fs.writeFileSync(
      path.join(tmpDir, '.planning', 'STATE.md'),
      `# Project State

**Current Phase:** 03

## Blockers

- Waiting for API credentials
- Need design review for dashboard
`
    );

    const result = runGsdTools('state-snapshot', tmpDir);
    assert.ok(result.success, `Command failed: ${result.error}`);

    const output = JSON.parse(result.output);
    assert.deepStrictEqual(output.blockers, [
      'Waiting for API credentials',
      'Need design review for dashboard',
    ], 'blockers extracted');
  });

  test('extracts session continuity info', () => {
    fs.writeFileSync(
      path.join(tmpDir, '.planning', 'STATE.md'),
      `# Project State

**Current Phase:** 03

## Session

**Last Date:** 2024-01-15
**Stopped At:** Phase 3, Plan 2, Task 1
**Resume File:** .planning/phases/03-api/03-02-PLAN.md
`
    );

    const result = runGsdTools('state-snapshot', tmpDir);
    assert.ok(result.success, `Command failed: ${result.error}`);

    const output = JSON.parse(result.output);
    assert.strictEqual(output.session.last_date, '2024-01-15', 'session date extracted');
    assert.strictEqual(output.session.stopped_at, 'Phase 3, Plan 2, Task 1', 'stopped at extracted');
    assert.strictEqual(output.session.resume_file, '.planning/phases/03-api/03-02-PLAN.md', 'resume file extracted');
  });

  test('handles paused_at field', () => {
    fs.writeFileSync(
      path.join(tmpDir, '.planning', 'STATE.md'),
      `# Project State

**Current Phase:** 03
**Paused At:** Phase 3, Plan 1, Task 2 - mid-implementation
`
    );

    const result = runGsdTools('state-snapshot', tmpDir);
    assert.ok(result.success, `Command failed: ${result.error}`);

    const output = JSON.parse(result.output);
    assert.strictEqual(output.paused_at, 'Phase 3, Plan 1, Task 2 - mid-implementation', 'paused_at extracted');
  });
});

// ─────────────────────────────────────────────────────────────────────────────
// summary-extract command
// ─────────────────────────────────────────────────────────────────────────────

describe('summary-extract command', () => {
  let tmpDir;

  beforeEach(() => {
    tmpDir = createTempProject();
  });

  afterEach(() => {
    cleanup(tmpDir);
  });

  test('missing file returns error', () => {
    const result = runGsdTools('summary-extract .planning/phases/01-test/01-01-SUMMARY.md', tmpDir);
    assert.ok(result.success, `Command should succeed: ${result.error}`);

    const output = JSON.parse(result.output);
    assert.strictEqual(output.error, 'File not found', 'should report missing file');
  });

  test('extracts all fields from SUMMARY.md', () => {
    const phaseDir = path.join(tmpDir, '.planning', 'phases', '01-foundation');
    fs.mkdirSync(phaseDir, { recursive: true });

    fs.writeFileSync(
      path.join(phaseDir, '01-01-SUMMARY.md'),
      `---
one-liner: Set up Prisma with User and Project models
key-files:
  - prisma/schema.prisma
  - src/lib/db.ts
tech-stack:
  added:
    - prisma
    - zod
patterns-established:
  - Repository pattern
  - Dependency injection
key-decisions:
  - Use Prisma over Drizzle: Better DX and ecosystem
  - Single database: Start simple, shard later
---

# Summary

Full summary content here.
`
    );

    const result = runGsdTools('summary-extract .planning/phases/01-foundation/01-01-SUMMARY.md', tmpDir);
    assert.ok(result.success, `Command failed: ${result.error}`);

    const output = JSON.parse(result.output);
    assert.strictEqual(output.path, '.planning/phases/01-foundation/01-01-SUMMARY.md', 'path correct');
    assert.strictEqual(output.one_liner, 'Set up Prisma with User and Project models', 'one-liner extracted');
    assert.deepStrictEqual(output.key_files, ['prisma/schema.prisma', 'src/lib/db.ts'], 'key files extracted');
    assert.deepStrictEqual(output.tech_added, ['prisma', 'zod'], 'tech added extracted');
    assert.deepStrictEqual(output.patterns, ['Repository pattern', 'Dependency injection'], 'patterns extracted');
    assert.strictEqual(output.decisions.length, 2, 'decisions extracted');
  });

  test('selective extraction with --fields', () => {
    const phaseDir = path.join(tmpDir, '.planning', 'phases', '01-foundation');
    fs.mkdirSync(phaseDir, { recursive: true });

    fs.writeFileSync(
      path.join(phaseDir, '01-01-SUMMARY.md'),
      `---
one-liner: Set up database
key-files:
  - prisma/schema.prisma
tech-stack:
  added:
    - prisma
patterns-established:
  - Repository pattern
key-decisions:
  - Use Prisma: Better DX
---
`
    );

    const result = runGsdTools('summary-extract .planning/phases/01-foundation/01-01-SUMMARY.md --fields one_liner,key_files', tmpDir);
    assert.ok(result.success, `Command failed: ${result.error}`);

    const output = JSON.parse(result.output);
    assert.strictEqual(output.one_liner, 'Set up database', 'one_liner included');
    assert.deepStrictEqual(output.key_files, ['prisma/schema.prisma'], 'key_files included');
    assert.strictEqual(output.tech_added, undefined, 'tech_added excluded');
    assert.strictEqual(output.patterns, undefined, 'patterns excluded');
    assert.strictEqual(output.decisions, undefined, 'decisions excluded');
  });

  test('handles missing frontmatter fields gracefully', () => {
    const phaseDir = path.join(tmpDir, '.planning', 'phases', '01-foundation');
    fs.mkdirSync(phaseDir, { recursive: true });

    fs.writeFileSync(
      path.join(phaseDir, '01-01-SUMMARY.md'),
      `---
one-liner: Minimal summary
---

# Summary
`
    );

    const result = runGsdTools('summary-extract .planning/phases/01-foundation/01-01-SUMMARY.md', tmpDir);
    assert.ok(result.success, `Command failed: ${result.error}`);

    const output = JSON.parse(result.output);
    assert.strictEqual(output.one_liner, 'Minimal summary', 'one-liner extracted');
    assert.deepStrictEqual(output.key_files, [], 'key_files defaults to empty');
    assert.deepStrictEqual(output.tech_added, [], 'tech_added defaults to empty');
    assert.deepStrictEqual(output.patterns, [], 'patterns defaults to empty');
    assert.deepStrictEqual(output.decisions, [], 'decisions defaults to empty');
  });

  test('parses key-decisions with rationale', () => {
    const phaseDir = path.join(tmpDir, '.planning', 'phases', '01-foundation');
    fs.mkdirSync(phaseDir, { recursive: true });

    fs.writeFileSync(
      path.join(phaseDir, '01-01-SUMMARY.md'),
      `---
key-decisions:
  - Use Prisma: Better DX than alternatives
  - JWT tokens: Stateless auth for scalability
---
`
    );

    const result = runGsdTools('summary-extract .planning/phases/01-foundation/01-01-SUMMARY.md', tmpDir);
    assert.ok(result.success, `Command failed: ${result.error}`);

    const output = JSON.parse(result.output);
    assert.strictEqual(output.decisions[0].summary, 'Use Prisma', 'decision summary parsed');
    assert.strictEqual(output.decisions[0].rationale, 'Better DX than alternatives', 'decision rationale parsed');
    assert.strictEqual(output.decisions[1].summary, 'JWT tokens', 'second decision summary');
    assert.strictEqual(output.decisions[1].rationale, 'Stateless auth for scalability', 'second decision rationale');
  });
});

// ─────────────────────────────────────────────────────────────────────────────
// init --include flag tests
// ─────────────────────────────────────────────────────────────────────────────

describe('init commands with --include flag', () => {
  let tmpDir;

  beforeEach(() => {
    tmpDir = createTempProject();
  });

  afterEach(() => {
    cleanup(tmpDir);
  });

  test('init execute-phase includes state and config content', () => {
    const phaseDir = path.join(tmpDir, '.planning', 'phases', '03-api');
    fs.mkdirSync(phaseDir, { recursive: true });
    fs.writeFileSync(path.join(phaseDir, '03-01-PLAN.md'), '# Plan');
    fs.writeFileSync(
      path.join(tmpDir, '.planning', 'STATE.md'),
      '# State\n\n**Current Phase:** 03\n**Status:** In progress'
    );
    fs.writeFileSync(
      path.join(tmpDir, '.planning', 'config.json'),
      JSON.stringify({ model_profile: 'balanced' })
    );

    const result = runGsdTools('init execute-phase 03 --include state,config', tmpDir);
    assert.ok(result.success, `Command failed: ${result.error}`);

    const output = JSON.parse(result.output);
    assert.ok(output.state_content, 'state_content should be included');
    assert.ok(output.state_content.includes('Current Phase'), 'state content correct');
    assert.ok(output.config_content, 'config_content should be included');
    assert.ok(output.config_content.includes('model_profile'), 'config content correct');
  });

  test('init execute-phase without --include omits content', () => {
    const phaseDir = path.join(tmpDir, '.planning', 'phases', '03-api');
    fs.mkdirSync(phaseDir, { recursive: true });
    fs.writeFileSync(path.join(phaseDir, '03-01-PLAN.md'), '# Plan');
    fs.writeFileSync(path.join(tmpDir, '.planning', 'STATE.md'), '# State');

    const result = runGsdTools('init execute-phase 03', tmpDir);
    assert.ok(result.success, `Command failed: ${result.error}`);

    const output = JSON.parse(result.output);
    assert.strictEqual(output.state_content, undefined, 'state_content should be omitted');
    assert.strictEqual(output.config_content, undefined, 'config_content should be omitted');
  });

  test('init plan-phase includes multiple file contents', () => {
    const phaseDir = path.join(tmpDir, '.planning', 'phases', '03-api');
    fs.mkdirSync(phaseDir, { recursive: true });
    fs.writeFileSync(path.join(tmpDir, '.planning', 'STATE.md'), '# Project State');
    fs.writeFileSync(path.join(tmpDir, '.planning', 'ROADMAP.md'), '# Roadmap v1.0');
    fs.writeFileSync(path.join(tmpDir, '.planning', 'REQUIREMENTS.md'), '# Requirements');
    fs.writeFileSync(path.join(phaseDir, '03-CONTEXT.md'), '# Phase Context');
    fs.writeFileSync(path.join(phaseDir, '03-RESEARCH.md'), '# Research Findings');

    const result = runGsdTools('init plan-phase 03 --include state,roadmap,requirements,context,research', tmpDir);
    assert.ok(result.success, `Command failed: ${result.error}`);

    const output = JSON.parse(result.output);
    assert.ok(output.state_content, 'state_content included');
    assert.ok(output.state_content.includes('Project State'), 'state content correct');
    assert.ok(output.roadmap_content, 'roadmap_content included');
    assert.ok(output.roadmap_content.includes('Roadmap v1.0'), 'roadmap content correct');
    assert.ok(output.requirements_content, 'requirements_content included');
    assert.ok(output.context_content, 'context_content included');
    assert.ok(output.research_content, 'research_content included');
  });

  test('init plan-phase includes verification and uat content', () => {
    const phaseDir = path.join(tmpDir, '.planning', 'phases', '03-api');
    fs.mkdirSync(phaseDir, { recursive: true });
    fs.writeFileSync(path.join(phaseDir, '03-VERIFICATION.md'), '# Verification Results');
    fs.writeFileSync(path.join(phaseDir, '03-UAT.md'), '# UAT Findings');

    const result = runGsdTools('init plan-phase 03 --include verification,uat', tmpDir);
    assert.ok(result.success, `Command failed: ${result.error}`);

    const output = JSON.parse(result.output);
    assert.ok(output.verification_content, 'verification_content included');
    assert.ok(output.verification_content.includes('Verification Results'), 'verification content correct');
    assert.ok(output.uat_content, 'uat_content included');
    assert.ok(output.uat_content.includes('UAT Findings'), 'uat content correct');
  });

  test('init progress includes state, roadmap, project, config', () => {
    fs.writeFileSync(path.join(tmpDir, '.planning', 'STATE.md'), '# State');
    fs.writeFileSync(path.join(tmpDir, '.planning', 'ROADMAP.md'), '# Roadmap');
    fs.writeFileSync(path.join(tmpDir, '.planning', 'PROJECT.md'), '# Project');
    fs.writeFileSync(
      path.join(tmpDir, '.planning', 'config.json'),
      JSON.stringify({ model_profile: 'quality' })
    );

    const result = runGsdTools('init progress --include state,roadmap,project,config', tmpDir);
    assert.ok(result.success, `Command failed: ${result.error}`);

    const output = JSON.parse(result.output);
    assert.ok(output.state_content, 'state_content included');
    assert.ok(output.roadmap_content, 'roadmap_content included');
    assert.ok(output.project_content, 'project_content included');
    assert.ok(output.config_content, 'config_content included');
  });

  test('missing files return null in content fields', () => {
    const phaseDir = path.join(tmpDir, '.planning', 'phases', '03-api');
    fs.mkdirSync(phaseDir, { recursive: true });
    fs.writeFileSync(path.join(phaseDir, '03-01-PLAN.md'), '# Plan');

    const result = runGsdTools('init execute-phase 03 --include state,config', tmpDir);
    assert.ok(result.success, `Command failed: ${result.error}`);

    const output = JSON.parse(result.output);
    assert.strictEqual(output.state_content, null, 'missing state returns null');
    assert.strictEqual(output.config_content, null, 'missing config returns null');
  });

  test('partial includes work correctly', () => {
    const phaseDir = path.join(tmpDir, '.planning', 'phases', '03-api');
    fs.mkdirSync(phaseDir, { recursive: true });
    fs.writeFileSync(path.join(phaseDir, '03-01-PLAN.md'), '# Plan');
    fs.writeFileSync(path.join(tmpDir, '.planning', 'STATE.md'), '# State');
    fs.writeFileSync(path.join(tmpDir, '.planning', 'ROADMAP.md'), '# Roadmap');

    // Only request state, not roadmap
    const result = runGsdTools('init execute-phase 03 --include state', tmpDir);
    assert.ok(result.success, `Command failed: ${result.error}`);

    const output = JSON.parse(result.output);
    assert.ok(output.state_content, 'state_content included');
    assert.strictEqual(output.roadmap_content, undefined, 'roadmap_content not requested, should be undefined');
  });
});

// ─────────────────────────────────────────────────────────────────────────────
// roadmap analyze command
// ─────────────────────────────────────────────────────────────────────────────

describe('roadmap analyze command', () => {
  let tmpDir;

  beforeEach(() => {
    tmpDir = createTempProject();
  });

  afterEach(() => {
    cleanup(tmpDir);
  });

  test('missing ROADMAP.md returns error', () => {
    const result = runGsdTools('roadmap analyze', tmpDir);
    assert.ok(result.success, `Command should succeed: ${result.error}`);

    const output = JSON.parse(result.output);
    assert.strictEqual(output.error, 'ROADMAP.md not found');
  });

  test('parses phases with goals and disk status', () => {
    fs.writeFileSync(
      path.join(tmpDir, '.planning', 'ROADMAP.md'),
      `# Roadmap v1.0

### Phase 1: Foundation
**Goal:** Set up infrastructure

### Phase 2: Authentication
**Goal:** Add user auth

### Phase 3: Features
**Goal:** Build core features
`
    );

    // Create phase dirs with varying completion
    const p1 = path.join(tmpDir, '.planning', 'phases', '01-foundation');
    fs.mkdirSync(p1, { recursive: true });
    fs.writeFileSync(path.join(p1, '01-01-PLAN.md'), '# Plan');
    fs.writeFileSync(path.join(p1, '01-01-SUMMARY.md'), '# Summary');

    const p2 = path.join(tmpDir, '.planning', 'phases', '02-authentication');
    fs.mkdirSync(p2, { recursive: true });
    fs.writeFileSync(path.join(p2, '02-01-PLAN.md'), '# Plan');

    const result = runGsdTools('roadmap analyze', tmpDir);
    assert.ok(result.success, `Command failed: ${result.error}`);

    const output = JSON.parse(result.output);
    assert.strictEqual(output.phase_count, 3, 'should find 3 phases');
    assert.strictEqual(output.phases[0].disk_status, 'complete', 'phase 1 complete');
    assert.strictEqual(output.phases[1].disk_status, 'planned', 'phase 2 planned');
    assert.strictEqual(output.phases[2].disk_status, 'no_directory', 'phase 3 no directory');
    assert.strictEqual(output.completed_phases, 1, '1 phase complete');
    assert.strictEqual(output.total_plans, 2, '2 total plans');
    assert.strictEqual(output.total_summaries, 1, '1 total summary');
    assert.strictEqual(output.progress_percent, 50, '50% complete');
    assert.strictEqual(output.current_phase, '2', 'current phase is 2');
  });

  test('extracts goals and dependencies', () => {
    fs.writeFileSync(
      path.join(tmpDir, '.planning', 'ROADMAP.md'),
      `# Roadmap

### Phase 1: Setup
**Goal:** Initialize project
**Depends on:** Nothing

### Phase 2: Build
**Goal:** Build features
**Depends on:** Phase 1
`
    );

    const result = runGsdTools('roadmap analyze', tmpDir);
    assert.ok(result.success, `Command failed: ${result.error}`);

    const output = JSON.parse(result.output);
    assert.strictEqual(output.phases[0].goal, 'Initialize project');
    assert.strictEqual(output.phases[0].depends_on, 'Nothing');
    assert.strictEqual(output.phases[1].goal, 'Build features');
    assert.strictEqual(output.phases[1].depends_on, 'Phase 1');
  });
});

// ─────────────────────────────────────────────────────────────────────────────
// phase add command
// ─────────────────────────────────────────────────────────────────────────────

describe('phase add command', () => {
  let tmpDir;

  beforeEach(() => {
    tmpDir = createTempProject();
  });

  afterEach(() => {
    cleanup(tmpDir);
  });

  test('adds phase after highest existing', () => {
    fs.writeFileSync(
      path.join(tmpDir, '.planning', 'ROADMAP.md'),
      `# Roadmap v1.0

### Phase 1: Foundation
**Goal:** Setup

### Phase 2: API
**Goal:** Build API

---
`
    );

    const result = runGsdTools('phase add User Dashboard', tmpDir);
    assert.ok(result.success, `Command failed: ${result.error}`);

    const output = JSON.parse(result.output);
    assert.strictEqual(output.phase_number, 3, 'should be phase 3');
    assert.strictEqual(output.slug, 'user-dashboard');

    // Verify directory created
    assert.ok(
      fs.existsSync(path.join(tmpDir, '.planning', 'phases', '03-user-dashboard')),
      'directory should be created'
    );

    // Verify ROADMAP updated
    const roadmap = fs.readFileSync(path.join(tmpDir, '.planning', 'ROADMAP.md'), 'utf-8');
    assert.ok(roadmap.includes('### Phase 3: User Dashboard'), 'roadmap should include new phase');
    assert.ok(roadmap.includes('**Depends on:** Phase 2'), 'should depend on previous');
  });

  test('handles empty roadmap', () => {
    fs.writeFileSync(
      path.join(tmpDir, '.planning', 'ROADMAP.md'),
      `# Roadmap v1.0\n`
    );

    const result = runGsdTools('phase add Initial Setup', tmpDir);
    assert.ok(result.success, `Command failed: ${result.error}`);

    const output = JSON.parse(result.output);
    assert.strictEqual(output.phase_number, 1, 'should be phase 1');
  });
});

// ─────────────────────────────────────────────────────────────────────────────
// phase insert command
// ─────────────────────────────────────────────────────────────────────────────

describe('phase insert command', () => {
  let tmpDir;

  beforeEach(() => {
    tmpDir = createTempProject();
  });

  afterEach(() => {
    cleanup(tmpDir);
  });

  test('inserts decimal phase after target', () => {
    fs.writeFileSync(
      path.join(tmpDir, '.planning', 'ROADMAP.md'),
      `# Roadmap

### Phase 1: Foundation
**Goal:** Setup

### Phase 2: API
**Goal:** Build API
`
    );
    fs.mkdirSync(path.join(tmpDir, '.planning', 'phases', '01-foundation'), { recursive: true });

    const result = runGsdTools('phase insert 1 Fix Critical Bug', tmpDir);
    assert.ok(result.success, `Command failed: ${result.error}`);

    const output = JSON.parse(result.output);
    assert.strictEqual(output.phase_number, '01.1', 'should be 01.1');
    assert.strictEqual(output.after_phase, '1');

    // Verify directory
    assert.ok(
      fs.existsSync(path.join(tmpDir, '.planning', 'phases', '01.1-fix-critical-bug')),
      'decimal phase directory should be created'
    );

    // Verify ROADMAP
    const roadmap = fs.readFileSync(path.join(tmpDir, '.planning', 'ROADMAP.md'), 'utf-8');
    assert.ok(roadmap.includes('Phase 01.1: Fix Critical Bug (INSERTED)'), 'roadmap should include inserted phase');
  });

  test('increments decimal when siblings exist', () => {
    fs.writeFileSync(
      path.join(tmpDir, '.planning', 'ROADMAP.md'),
      `# Roadmap

### Phase 1: Foundation
**Goal:** Setup

### Phase 2: API
**Goal:** Build API
`
    );
    fs.mkdirSync(path.join(tmpDir, '.planning', 'phases', '01-foundation'), { recursive: true });
    fs.mkdirSync(path.join(tmpDir, '.planning', 'phases', '01.1-hotfix'), { recursive: true });

    const result = runGsdTools('phase insert 1 Another Fix', tmpDir);
    assert.ok(result.success, `Command failed: ${result.error}`);

    const output = JSON.parse(result.output);
    assert.strictEqual(output.phase_number, '01.2', 'should be 01.2');
  });

  test('rejects missing phase', () => {
    fs.writeFileSync(
      path.join(tmpDir, '.planning', 'ROADMAP.md'),
      `# Roadmap\n### Phase 1: Test\n**Goal:** Test\n`
    );

    const result = runGsdTools('phase insert 99 Fix Something', tmpDir);
    assert.ok(!result.success, 'should fail for missing phase');
    assert.ok(result.error.includes('not found'), 'error mentions not found');
  });
});

// ─────────────────────────────────────────────────────────────────────────────
// phase remove command
// ─────────────────────────────────────────────────────────────────────────────

describe('phase remove command', () => {
  let tmpDir;

  beforeEach(() => {
    tmpDir = createTempProject();
  });

  afterEach(() => {
    cleanup(tmpDir);
  });

  test('removes phase directory and renumbers subsequent', () => {
    // Setup 3 phases
    fs.writeFileSync(
      path.join(tmpDir, '.planning', 'ROADMAP.md'),
      `# Roadmap

### Phase 1: Foundation
**Goal:** Setup
**Depends on:** Nothing

### Phase 2: Auth
**Goal:** Authentication
**Depends on:** Phase 1

### Phase 3: Features
**Goal:** Core features
**Depends on:** Phase 2
`
    );

    fs.mkdirSync(path.join(tmpDir, '.planning', 'phases', '01-foundation'), { recursive: true });
    const p2 = path.join(tmpDir, '.planning', 'phases', '02-auth');
    fs.mkdirSync(p2, { recursive: true });
    fs.writeFileSync(path.join(p2, '02-01-PLAN.md'), '# Plan');
    const p3 = path.join(tmpDir, '.planning', 'phases', '03-features');
    fs.mkdirSync(p3, { recursive: true });
    fs.writeFileSync(path.join(p3, '03-01-PLAN.md'), '# Plan');
    fs.writeFileSync(path.join(p3, '03-02-PLAN.md'), '# Plan 2');

    // Remove phase 2
    const result = runGsdTools('phase remove 2', tmpDir);
    assert.ok(result.success, `Command failed: ${result.error}`);

    const output = JSON.parse(result.output);
    assert.strictEqual(output.removed, '2');
    assert.strictEqual(output.directory_deleted, '02-auth');

    // Phase 3 should be renumbered to 02
    assert.ok(
      fs.existsSync(path.join(tmpDir, '.planning', 'phases', '02-features')),
      'phase 3 should be renumbered to 02-features'
    );
    assert.ok(
      !fs.existsSync(path.join(tmpDir, '.planning', 'phases', '03-features')),
      'old 03-features should not exist'
    );

    // Files inside should be renamed
    assert.ok(
      fs.existsSync(path.join(tmpDir, '.planning', 'phases', '02-features', '02-01-PLAN.md')),
      'plan file should be renumbered to 02-01'
    );
    assert.ok(
      fs.existsSync(path.join(tmpDir, '.planning', 'phases', '02-features', '02-02-PLAN.md')),
      'plan 2 should be renumbered to 02-02'
    );

    // ROADMAP should be updated
    const roadmap = fs.readFileSync(path.join(tmpDir, '.planning', 'ROADMAP.md'), 'utf-8');
    assert.ok(!roadmap.includes('Phase 2: Auth'), 'removed phase should not be in roadmap');
    assert.ok(roadmap.includes('Phase 2: Features'), 'phase 3 should be renumbered to 2');
  });

  test('rejects removal of phase with summaries unless --force', () => {
    const p1 = path.join(tmpDir, '.planning', 'phases', '01-test');
    fs.mkdirSync(p1, { recursive: true });
    fs.writeFileSync(path.join(p1, '01-01-PLAN.md'), '# Plan');
    fs.writeFileSync(path.join(p1, '01-01-SUMMARY.md'), '# Summary');
    fs.writeFileSync(
      path.join(tmpDir, '.planning', 'ROADMAP.md'),
      `# Roadmap\n### Phase 1: Test\n**Goal:** Test\n`
    );

    // Should fail without --force
    const result = runGsdTools('phase remove 1', tmpDir);
    assert.ok(!result.success, 'should fail without --force');
    assert.ok(result.error.includes('executed plan'), 'error mentions executed plans');

    // Should succeed with --force
    const forceResult = runGsdTools('phase remove 1 --force', tmpDir);
    assert.ok(forceResult.success, `Force remove failed: ${forceResult.error}`);
  });

  test('removes decimal phase and renumbers siblings', () => {
    fs.writeFileSync(
      path.join(tmpDir, '.planning', 'ROADMAP.md'),
      `# Roadmap\n### Phase 6: Main\n**Goal:** Main\n### Phase 6.1: Fix A\n**Goal:** Fix A\n### Phase 6.2: Fix B\n**Goal:** Fix B\n### Phase 6.3: Fix C\n**Goal:** Fix C\n`
    );

    fs.mkdirSync(path.join(tmpDir, '.planning', 'phases', '06-main'), { recursive: true });
    fs.mkdirSync(path.join(tmpDir, '.planning', 'phases', '06.1-fix-a'), { recursive: true });
    fs.mkdirSync(path.join(tmpDir, '.planning', 'phases', '06.2-fix-b'), { recursive: true });
    fs.mkdirSync(path.join(tmpDir, '.planning', 'phases', '06.3-fix-c'), { recursive: true });

    const result = runGsdTools('phase remove 6.2', tmpDir);
    assert.ok(result.success, `Command failed: ${result.error}`);

    // 06.3 should become 06.2
    assert.ok(
      fs.existsSync(path.join(tmpDir, '.planning', 'phases', '06.2-fix-c')),
      '06.3 should be renumbered to 06.2'
    );
    assert.ok(
      !fs.existsSync(path.join(tmpDir, '.planning', 'phases', '06.3-fix-c')),
      'old 06.3 should not exist'
    );
  });

  test('updates STATE.md phase count', () => {
    fs.writeFileSync(
      path.join(tmpDir, '.planning', 'ROADMAP.md'),
      `# Roadmap\n### Phase 1: A\n**Goal:** A\n### Phase 2: B\n**Goal:** B\n`
    );
    fs.writeFileSync(
      path.join(tmpDir, '.planning', 'STATE.md'),
      `# State\n\n**Current Phase:** 1\n**Total Phases:** 2\n`
    );
    fs.mkdirSync(path.join(tmpDir, '.planning', 'phases', '01-a'), { recursive: true });
    fs.mkdirSync(path.join(tmpDir, '.planning', 'phases', '02-b'), { recursive: true });

    runGsdTools('phase remove 2', tmpDir);

    const state = fs.readFileSync(path.join(tmpDir, '.planning', 'STATE.md'), 'utf-8');
    assert.ok(state.includes('**Total Phases:** 1'), 'total phases should be decremented');
  });
});

// ─────────────────────────────────────────────────────────────────────────────
// phase complete command
// ─────────────────────────────────────────────────────────────────────────────

describe('phase complete command', () => {
  let tmpDir;

  beforeEach(() => {
    tmpDir = createTempProject();
  });

  afterEach(() => {
    cleanup(tmpDir);
  });

  test('marks phase complete and transitions to next', () => {
    fs.writeFileSync(
      path.join(tmpDir, '.planning', 'ROADMAP.md'),
      `# Roadmap

- [ ] Phase 1: Foundation
- [ ] Phase 2: API

### Phase 1: Foundation
**Goal:** Setup
**Plans:** 1 plans

### Phase 2: API
**Goal:** Build API
`
    );
    fs.writeFileSync(
      path.join(tmpDir, '.planning', 'STATE.md'),
      `# State\n\n**Current Phase:** 01\n**Current Phase Name:** Foundation\n**Status:** In progress\n**Current Plan:** 01-01\n**Last Activity:** 2025-01-01\n**Last Activity Description:** Working on phase 1\n`
    );

    const p1 = path.join(tmpDir, '.planning', 'phases', '01-foundation');
    fs.mkdirSync(p1, { recursive: true });
    fs.writeFileSync(path.join(p1, '01-01-PLAN.md'), '# Plan');
    fs.writeFileSync(path.join(p1, '01-01-SUMMARY.md'), '# Summary');
    fs.mkdirSync(path.join(tmpDir, '.planning', 'phases', '02-api'), { recursive: true });

    const result = runGsdTools('phase complete 1', tmpDir);
    assert.ok(result.success, `Command failed: ${result.error}`);

    const output = JSON.parse(result.output);
    assert.strictEqual(output.completed_phase, '1');
    assert.strictEqual(output.plans_executed, '1/1');
    assert.strictEqual(output.next_phase, '02');
    assert.strictEqual(output.is_last_phase, false);

    // Verify STATE.md updated
    const state = fs.readFileSync(path.join(tmpDir, '.planning', 'STATE.md'), 'utf-8');
    assert.ok(state.includes('**Current Phase:** 02'), 'should advance to phase 02');
    assert.ok(state.includes('**Status:** Ready to plan'), 'status should be ready to plan');
    assert.ok(state.includes('**Current Plan:** Not started'), 'plan should be reset');

    // Verify ROADMAP checkbox
    const roadmap = fs.readFileSync(path.join(tmpDir, '.planning', 'ROADMAP.md'), 'utf-8');
    assert.ok(roadmap.includes('[x]'), 'phase should be checked off');
    assert.ok(roadmap.includes('completed'), 'completion date should be added');
  });

  test('detects last phase in milestone', () => {
    fs.writeFileSync(
      path.join(tmpDir, '.planning', 'ROADMAP.md'),
      `# Roadmap\n### Phase 1: Only Phase\n**Goal:** Everything\n`
    );
    fs.writeFileSync(
      path.join(tmpDir, '.planning', 'STATE.md'),
      `# State\n\n**Current Phase:** 01\n**Status:** In progress\n**Current Plan:** 01-01\n**Last Activity:** 2025-01-01\n**Last Activity Description:** Working\n`
    );

    const p1 = path.join(tmpDir, '.planning', 'phases', '01-only-phase');
    fs.mkdirSync(p1, { recursive: true });
    fs.writeFileSync(path.join(p1, '01-01-PLAN.md'), '# Plan');
    fs.writeFileSync(path.join(p1, '01-01-SUMMARY.md'), '# Summary');

    const result = runGsdTools('phase complete 1', tmpDir);
    assert.ok(result.success, `Command failed: ${result.error}`);

    const output = JSON.parse(result.output);
    assert.strictEqual(output.is_last_phase, true, 'should detect last phase');
    assert.strictEqual(output.next_phase, null, 'no next phase');

    const state = fs.readFileSync(path.join(tmpDir, '.planning', 'STATE.md'), 'utf-8');
    assert.ok(state.includes('Milestone complete'), 'status should be milestone complete');
  });
});

// ─────────────────────────────────────────────────────────────────────────────
// milestone complete command
// ─────────────────────────────────────────────────────────────────────────────

describe('milestone complete command', () => {
  let tmpDir;

  beforeEach(() => {
    tmpDir = createTempProject();
  });

  afterEach(() => {
    cleanup(tmpDir);
  });

  test('archives roadmap, requirements, creates MILESTONES.md', () => {
    fs.writeFileSync(
      path.join(tmpDir, '.planning', 'ROADMAP.md'),
      `# Roadmap v1.0 MVP\n\n### Phase 1: Foundation\n**Goal:** Setup\n`
    );
    fs.writeFileSync(
      path.join(tmpDir, '.planning', 'REQUIREMENTS.md'),
      `# Requirements\n\n- [ ] User auth\n- [ ] Dashboard\n`
    );
    fs.writeFileSync(
      path.join(tmpDir, '.planning', 'STATE.md'),
      `# State\n\n**Status:** In progress\n**Last Activity:** 2025-01-01\n**Last Activity Description:** Working\n`
    );

    const p1 = path.join(tmpDir, '.planning', 'phases', '01-foundation');
    fs.mkdirSync(p1, { recursive: true });
    fs.writeFileSync(
      path.join(p1, '01-01-SUMMARY.md'),
      `---\none-liner: Set up project infrastructure\n---\n# Summary\n`
    );

    const result = runGsdTools('milestone complete v1.0 --name MVP Foundation', tmpDir);
    assert.ok(result.success, `Command failed: ${result.error}`);

    const output = JSON.parse(result.output);
    assert.strictEqual(output.version, 'v1.0');
    assert.strictEqual(output.phases, 1);
    assert.ok(output.archived.roadmap, 'roadmap should be archived');
    assert.ok(output.archived.requirements, 'requirements should be archived');

    // Verify archive files exist
    assert.ok(
      fs.existsSync(path.join(tmpDir, '.planning', 'milestones', 'v1.0-ROADMAP.md')),
      'archived roadmap should exist'
    );
    assert.ok(
      fs.existsSync(path.join(tmpDir, '.planning', 'milestones', 'v1.0-REQUIREMENTS.md')),
      'archived requirements should exist'
    );

    // Verify MILESTONES.md created
    assert.ok(
      fs.existsSync(path.join(tmpDir, '.planning', 'MILESTONES.md')),
      'MILESTONES.md should be created'
    );
    const milestones = fs.readFileSync(path.join(tmpDir, '.planning', 'MILESTONES.md'), 'utf-8');
    assert.ok(milestones.includes('v1.0 MVP Foundation'), 'milestone entry should contain name');
    assert.ok(milestones.includes('Set up project infrastructure'), 'accomplishments should be listed');
  });

  test('appends to existing MILESTONES.md', () => {
    fs.writeFileSync(
      path.join(tmpDir, '.planning', 'MILESTONES.md'),
      `# Milestones\n\n## v0.9 Alpha (Shipped: 2025-01-01)\n\n---\n\n`
    );
    fs.writeFileSync(
      path.join(tmpDir, '.planning', 'ROADMAP.md'),
      `# Roadmap v1.0\n`
    );
    fs.writeFileSync(
      path.join(tmpDir, '.planning', 'STATE.md'),
      `# State\n\n**Status:** In progress\n**Last Activity:** 2025-01-01\n**Last Activity Description:** Working\n`
    );

    const result = runGsdTools('milestone complete v1.0 --name Beta', tmpDir);
    assert.ok(result.success, `Command failed: ${result.error}`);

    const milestones = fs.readFileSync(path.join(tmpDir, '.planning', 'MILESTONES.md'), 'utf-8');
    assert.ok(milestones.includes('v0.9 Alpha'), 'existing entry should be preserved');
    assert.ok(milestones.includes('v1.0 Beta'), 'new entry should be appended');
  });
});

// ─────────────────────────────────────────────────────────────────────────────
// validate consistency command
// ─────────────────────────────────────────────────────────────────────────────

describe('validate consistency command', () => {
  let tmpDir;

  beforeEach(() => {
    tmpDir = createTempProject();
  });

  afterEach(() => {
    cleanup(tmpDir);
  });

  test('passes for consistent project', () => {
    fs.writeFileSync(
      path.join(tmpDir, '.planning', 'ROADMAP.md'),
      `# Roadmap\n### Phase 1: A\n### Phase 2: B\n### Phase 3: C\n`
    );
    fs.mkdirSync(path.join(tmpDir, '.planning', 'phases', '01-a'), { recursive: true });
    fs.mkdirSync(path.join(tmpDir, '.planning', 'phases', '02-b'), { recursive: true });
    fs.mkdirSync(path.join(tmpDir, '.planning', 'phases', '03-c'), { recursive: true });

    const result = runGsdTools('validate consistency', tmpDir);
    assert.ok(result.success, `Command failed: ${result.error}`);

    const output = JSON.parse(result.output);
    assert.strictEqual(output.passed, true, 'should pass');
    assert.strictEqual(output.warning_count, 0, 'no warnings');
  });

  test('warns about phase on disk but not in roadmap', () => {
    fs.writeFileSync(
      path.join(tmpDir, '.planning', 'ROADMAP.md'),
      `# Roadmap\n### Phase 1: A\n`
    );
    fs.mkdirSync(path.join(tmpDir, '.planning', 'phases', '01-a'), { recursive: true });
    fs.mkdirSync(path.join(tmpDir, '.planning', 'phases', '02-orphan'), { recursive: true });

    const result = runGsdTools('validate consistency', tmpDir);
    assert.ok(result.success, `Command failed: ${result.error}`);

    const output = JSON.parse(result.output);
    assert.ok(output.warning_count > 0, 'should have warnings');
    assert.ok(
      output.warnings.some(w => w.includes('disk but not in ROADMAP')),
      'should warn about orphan directory'
    );
  });

  test('warns about gaps in phase numbering', () => {
    fs.writeFileSync(
      path.join(tmpDir, '.planning', 'ROADMAP.md'),
      `# Roadmap\n### Phase 1: A\n### Phase 3: C\n`
    );
    fs.mkdirSync(path.join(tmpDir, '.planning', 'phases', '01-a'), { recursive: true });
    fs.mkdirSync(path.join(tmpDir, '.planning', 'phases', '03-c'), { recursive: true });

    const result = runGsdTools('validate consistency', tmpDir);
    assert.ok(result.success, `Command failed: ${result.error}`);

    const output = JSON.parse(result.output);
    assert.ok(
      output.warnings.some(w => w.includes('Gap in phase numbering')),
      'should warn about gap'
    );
  });
});

// ─────────────────────────────────────────────────────────────────────────────
// progress command
// ─────────────────────────────────────────────────────────────────────────────

describe('progress command', () => {
  let tmpDir;

  beforeEach(() => {
    tmpDir = createTempProject();
  });

  afterEach(() => {
    cleanup(tmpDir);
  });

  test('renders JSON progress', () => {
    fs.writeFileSync(
      path.join(tmpDir, '.planning', 'ROADMAP.md'),
      `# Roadmap v1.0 MVP\n`
    );
    const p1 = path.join(tmpDir, '.planning', 'phases', '01-foundation');
    fs.mkdirSync(p1, { recursive: true });
    fs.writeFileSync(path.join(p1, '01-01-PLAN.md'), '# Plan');
    fs.writeFileSync(path.join(p1, '01-01-SUMMARY.md'), '# Done');
    fs.writeFileSync(path.join(p1, '01-02-PLAN.md'), '# Plan 2');

    const result = runGsdTools('progress json', tmpDir);
    assert.ok(result.success, `Command failed: ${result.error}`);

    const output = JSON.parse(result.output);
    assert.strictEqual(output.total_plans, 2, '2 total plans');
    assert.strictEqual(output.total_summaries, 1, '1 summary');
    assert.strictEqual(output.percent, 50, '50%');
    assert.strictEqual(output.phases.length, 1, '1 phase');
    assert.strictEqual(output.phases[0].status, 'In Progress', 'phase in progress');
  });

  test('renders bar format', () => {
    fs.writeFileSync(
      path.join(tmpDir, '.planning', 'ROADMAP.md'),
      `# Roadmap v1.0\n`
    );
    const p1 = path.join(tmpDir, '.planning', 'phases', '01-test');
    fs.mkdirSync(p1, { recursive: true });
    fs.writeFileSync(path.join(p1, '01-01-PLAN.md'), '# Plan');
    fs.writeFileSync(path.join(p1, '01-01-SUMMARY.md'), '# Done');

    const result = runGsdTools('progress bar --raw', tmpDir);
    assert.ok(result.success, `Command failed: ${result.error}`);
    assert.ok(result.output.includes('1/1'), 'should include count');
    assert.ok(result.output.includes('100%'), 'should include 100%');
  });

  test('renders table format', () => {
    fs.writeFileSync(
      path.join(tmpDir, '.planning', 'ROADMAP.md'),
      `# Roadmap v1.0 MVP\n`
    );
    const p1 = path.join(tmpDir, '.planning', 'phases', '01-foundation');
    fs.mkdirSync(p1, { recursive: true });
    fs.writeFileSync(path.join(p1, '01-01-PLAN.md'), '# Plan');

    const result = runGsdTools('progress table --raw', tmpDir);
    assert.ok(result.success, `Command failed: ${result.error}`);
    assert.ok(result.output.includes('Phase'), 'should have table header');
    assert.ok(result.output.includes('foundation'), 'should include phase name');
  });
});

// ─────────────────────────────────────────────────────────────────────────────
// todo complete command
// ─────────────────────────────────────────────────────────────────────────────

describe('todo complete command', () => {
  let tmpDir;

  beforeEach(() => {
    tmpDir = createTempProject();
  });

  afterEach(() => {
    cleanup(tmpDir);
  });

  test('moves todo from pending to completed', () => {
    const pendingDir = path.join(tmpDir, '.planning', 'todos', 'pending');
    fs.mkdirSync(pendingDir, { recursive: true });
    fs.writeFileSync(
      path.join(pendingDir, 'add-dark-mode.md'),
      `title: Add dark mode\narea: ui\ncreated: 2025-01-01\n`
    );

    const result = runGsdTools('todo complete add-dark-mode.md', tmpDir);
    assert.ok(result.success, `Command failed: ${result.error}`);

    const output = JSON.parse(result.output);
    assert.strictEqual(output.completed, true);

    // Verify moved
    assert.ok(
      !fs.existsSync(path.join(tmpDir, '.planning', 'todos', 'pending', 'add-dark-mode.md')),
      'should be removed from pending'
    );
    assert.ok(
      fs.existsSync(path.join(tmpDir, '.planning', 'todos', 'completed', 'add-dark-mode.md')),
      'should be in completed'
    );

    // Verify completion timestamp added
    const content = fs.readFileSync(
      path.join(tmpDir, '.planning', 'todos', 'completed', 'add-dark-mode.md'),
      'utf-8'
    );
    assert.ok(content.startsWith('completed:'), 'should have completed timestamp');
  });

  test('fails for nonexistent todo', () => {
    const result = runGsdTools('todo complete nonexistent.md', tmpDir);
    assert.ok(!result.success, 'should fail');
    assert.ok(result.error.includes('not found'), 'error mentions not found');
  });
});

// ─────────────────────────────────────────────────────────────────────────────
// scaffold command
// ─────────────────────────────────────────────────────────────────────────────

describe('scaffold command', () => {
  let tmpDir;

  beforeEach(() => {
    tmpDir = createTempProject();
  });

  afterEach(() => {
    cleanup(tmpDir);
  });

  test('scaffolds context file', () => {
    fs.mkdirSync(path.join(tmpDir, '.planning', 'phases', '03-api'), { recursive: true });

    const result = runGsdTools('scaffold context --phase 3', tmpDir);
    assert.ok(result.success, `Command failed: ${result.error}`);

    const output = JSON.parse(result.output);
    assert.strictEqual(output.created, true);

    // Verify file content
    const content = fs.readFileSync(
      path.join(tmpDir, '.planning', 'phases', '03-api', '03-CONTEXT.md'),
      'utf-8'
    );
    assert.ok(content.includes('Phase 3'), 'should reference phase number');
    assert.ok(content.includes('Decisions'), 'should have decisions section');
    assert.ok(content.includes('Discretion Areas'), 'should have discretion section');
  });

  test('scaffolds UAT file', () => {
    fs.mkdirSync(path.join(tmpDir, '.planning', 'phases', '03-api'), { recursive: true });

    const result = runGsdTools('scaffold uat --phase 3', tmpDir);
    assert.ok(result.success, `Command failed: ${result.error}`);

    const output = JSON.parse(result.output);
    assert.strictEqual(output.created, true);

    const content = fs.readFileSync(
      path.join(tmpDir, '.planning', 'phases', '03-api', '03-UAT.md'),
      'utf-8'
    );
    assert.ok(content.includes('User Acceptance Testing'), 'should have UAT heading');
    assert.ok(content.includes('Test Results'), 'should have test results section');
  });

  test('scaffolds verification file', () => {
    fs.mkdirSync(path.join(tmpDir, '.planning', 'phases', '03-api'), { recursive: true });

    const result = runGsdTools('scaffold verification --phase 3', tmpDir);
    assert.ok(result.success, `Command failed: ${result.error}`);

    const output = JSON.parse(result.output);
    assert.strictEqual(output.created, true);

    const content = fs.readFileSync(
      path.join(tmpDir, '.planning', 'phases', '03-api', '03-VERIFICATION.md'),
      'utf-8'
    );
    assert.ok(content.includes('Goal-Backward Verification'), 'should have verification heading');
  });

  test('scaffolds phase directory', () => {
    const result = runGsdTools('scaffold phase-dir --phase 5 --name User Dashboard', tmpDir);
    assert.ok(result.success, `Command failed: ${result.error}`);

    const output = JSON.parse(result.output);
    assert.strictEqual(output.created, true);
    assert.ok(
      fs.existsSync(path.join(tmpDir, '.planning', 'phases', '05-user-dashboard')),
      'directory should be created'
    );
  });

  test('does not overwrite existing files', () => {
    const phaseDir = path.join(tmpDir, '.planning', 'phases', '03-api');
    fs.mkdirSync(phaseDir, { recursive: true });
    fs.writeFileSync(path.join(phaseDir, '03-CONTEXT.md'), '# Existing content');

    const result = runGsdTools('scaffold context --phase 3', tmpDir);
    assert.ok(result.success, `Command failed: ${result.error}`);

    const output = JSON.parse(result.output);
    assert.strictEqual(output.created, false, 'should not overwrite');
    assert.strictEqual(output.reason, 'already_exists');
  });
});

// ─────────────────────────────────────────────────────────────────────────────
// Manifest test helpers
// ─────────────────────────────────────────────────────────────────────────────

/**
 * Create a temp directory with manifest and config for manifest command tests.
 * @param {string} tmpDir - temp project root (from createTempProject)
 * @param {object} manifestFeatures - features object for feature-manifest.json
 * @param {object} configObj - config.json contents
 * @param {number} [manifestVersion=1] - manifest_version field
 */
function createManifestTestEnv(tmpDir, manifestFeatures, configObj, manifestVersion = 1) {
  const manifestDir = path.join(tmpDir, '.claude', 'get-shit-done');
  fs.mkdirSync(manifestDir, { recursive: true });
  fs.writeFileSync(
    path.join(manifestDir, 'feature-manifest.json'),
    JSON.stringify({ manifest_version: manifestVersion, features: manifestFeatures }, null, 2)
  );
  fs.mkdirSync(path.join(tmpDir, '.planning'), { recursive: true });
  fs.writeFileSync(
    path.join(tmpDir, '.planning', 'config.json'),
    JSON.stringify(configObj, null, 2)
  );
  return tmpDir;
}

// Minimal test manifest with health_check feature
function healthCheckFeature() {
  return {
    health_check: {
      scope: 'project',
      introduced: '1.12.0',
      config_key: 'health_check',
      schema: {
        frequency: {
          type: 'string',
          enum: ['milestone-only', 'on-resume', 'every-phase', 'explicit-only'],
          default: 'milestone-only',
          description: 'How often health checks run',
        },
        stale_threshold_days: {
          type: 'number',
          default: 7,
          description: 'Days before artifacts are considered stale',
        },
        blocking_checks: {
          type: 'boolean',
          default: false,
          description: 'Whether health warnings block execution',
        },
      },
      init_prompts: [
        {
          field: 'frequency',
          question: 'How often should health checks run?',
          options: [
            { value: 'milestone-only', label: 'Milestone only (default)' },
            { value: 'on-resume', label: 'On resume' },
          ],
        },
      ],
    },
  };
}

// Two-feature manifest for counting tests
function twoFeatureManifest() {
  return {
    health_check: healthCheckFeature().health_check,
    devops: {
      scope: 'project',
      introduced: '1.12.0',
      config_key: 'devops',
      schema: {
        ci_provider: {
          type: 'string',
          enum: ['none', 'github-actions', 'gitlab-ci'],
          default: 'none',
          description: 'CI/CD provider',
        },
        commit_convention: {
          type: 'string',
          enum: ['freeform', 'conventional'],
          default: 'freeform',
          description: 'Commit message convention',
        },
      },
      init_prompts: [],
    },
  };
}

// ─────────────────────────────────────────────────────────────────────────────
// manifest diff-config command
// ─────────────────────────────────────────────────────────────────────────────

describe('manifest diff-config command', () => {
  let tmpDir;

  beforeEach(() => {
    tmpDir = createTempProject();
  });

  afterEach(() => {
    cleanup(tmpDir);
  });

  test('detects missing feature section', () => {
    createManifestTestEnv(tmpDir, healthCheckFeature(), { mode: 'yolo' });

    const result = runGsdTools('manifest diff-config', tmpDir);
    assert.ok(result.success, `Command failed: ${result.error}`);

    const output = JSON.parse(result.output);
    assert.ok(
      output.missing_features.some(f => f.feature === 'health_check'),
      'missing_features should contain health_check'
    );
  });

  test('detects missing field in existing section', () => {
    createManifestTestEnv(tmpDir, healthCheckFeature(), {
      health_check: {},
    });

    const result = runGsdTools('manifest diff-config', tmpDir);
    assert.ok(result.success, `Command failed: ${result.error}`);

    const output = JSON.parse(result.output);
    assert.strictEqual(output.missing_features.length, 0, 'health_check section exists');
    const fieldNames = output.missing_fields.map(f => f.field);
    assert.ok(fieldNames.includes('frequency'), 'frequency should be missing');
    assert.ok(fieldNames.includes('stale_threshold_days'), 'stale_threshold_days should be missing');
    assert.ok(fieldNames.includes('blocking_checks'), 'blocking_checks should be missing');
    // Verify default values are reported
    const freqField = output.missing_fields.find(f => f.field === 'frequency');
    assert.strictEqual(freqField.default, 'milestone-only', 'default for frequency correct');
    assert.strictEqual(freqField.expected_type, 'string', 'expected type correct');
  });

  test('detects type mismatch', () => {
    createManifestTestEnv(tmpDir, healthCheckFeature(), {
      health_check: { frequency: 123, stale_threshold_days: 7, blocking_checks: false },
    });

    const result = runGsdTools('manifest diff-config', tmpDir);
    assert.ok(result.success, `Command failed: ${result.error}`);

    const output = JSON.parse(result.output);
    assert.ok(output.type_mismatches.length > 0, 'should have type mismatches');
    const mismatch = output.type_mismatches.find(m => m.field === 'frequency');
    assert.ok(mismatch, 'frequency type mismatch should be reported');
    assert.strictEqual(mismatch.expected, 'string', 'expected string');
    assert.strictEqual(mismatch.actual, 'number', 'actual number');
  });

  test('detects enum mismatch', () => {
    createManifestTestEnv(tmpDir, healthCheckFeature(), {
      health_check: { frequency: 'invalid-value', stale_threshold_days: 7, blocking_checks: false },
    });

    const result = runGsdTools('manifest diff-config', tmpDir);
    assert.ok(result.success, `Command failed: ${result.error}`);

    const output = JSON.parse(result.output);
    assert.ok(output.enum_mismatches.length > 0, 'should have enum mismatches');
    const mismatch = output.enum_mismatches.find(m => m.field === 'frequency');
    assert.ok(mismatch, 'frequency enum mismatch should be reported');
    assert.strictEqual(mismatch.actual, 'invalid-value', 'actual value correct');
    assert.ok(Array.isArray(mismatch.expected_values), 'expected_values should be array');
  });

  test('reports unknown fields as informational', () => {
    createManifestTestEnv(tmpDir, healthCheckFeature(), {
      custom_setting: true,
      health_check: { frequency: 'milestone-only', stale_threshold_days: 7, blocking_checks: false },
    });

    const result = runGsdTools('manifest diff-config', tmpDir);
    assert.ok(result.success, `Command failed: ${result.error}`);

    const output = JSON.parse(result.output);
    assert.ok(
      output.unknown_fields.some(f => f.path === 'custom_setting'),
      'unknown_fields should contain custom_setting'
    );
  });

  test('reports manifest and config versions', () => {
    createManifestTestEnv(tmpDir, healthCheckFeature(), {
      manifest_version: 1,
      health_check: { frequency: 'milestone-only', stale_threshold_days: 7, blocking_checks: false },
    });

    const result = runGsdTools('manifest diff-config', tmpDir);
    assert.ok(result.success, `Command failed: ${result.error}`);

    const output = JSON.parse(result.output);
    assert.strictEqual(output.manifest_version, 1, 'manifest_version from manifest');
    assert.strictEqual(output.config_manifest_version, 1, 'config_manifest_version from config');
  });

  test('handles config without manifest_version', () => {
    createManifestTestEnv(tmpDir, healthCheckFeature(), {
      health_check: { frequency: 'milestone-only', stale_threshold_days: 7, blocking_checks: false },
    });

    const result = runGsdTools('manifest diff-config', tmpDir);
    assert.ok(result.success, `Command failed: ${result.error}`);

    const output = JSON.parse(result.output);
    assert.strictEqual(output.config_manifest_version, null, 'config_manifest_version should be null');
  });
});

// ─────────────────────────────────────────────────────────────────────────────
// manifest validate command
// ─────────────────────────────────────────────────────────────────────────────

describe('manifest validate command', () => {
  let tmpDir;

  beforeEach(() => {
    tmpDir = createTempProject();
  });

  afterEach(() => {
    cleanup(tmpDir);
  });

  test('valid config passes validation', () => {
    createManifestTestEnv(tmpDir, healthCheckFeature(), {
      health_check: { frequency: 'milestone-only', stale_threshold_days: 7, blocking_checks: false },
    });

    const result = runGsdTools('manifest validate', tmpDir);
    assert.ok(result.success, `Command failed: ${result.error}`);

    const output = JSON.parse(result.output);
    assert.strictEqual(output.valid, true, 'should be valid');
    assert.strictEqual(output.errors.length, 0, 'no errors');
  });

  test('config with unknown fields passes validation', () => {
    createManifestTestEnv(tmpDir, healthCheckFeature(), {
      custom_field: true,
      health_check: { frequency: 'milestone-only', stale_threshold_days: 7, blocking_checks: false },
    });

    const result = runGsdTools('manifest validate', tmpDir);
    assert.ok(result.success, `Command failed: ${result.error}`);

    const output = JSON.parse(result.output);
    assert.strictEqual(output.valid, true, 'should be valid despite unknown fields');
    assert.ok(
      output.warnings.some(w => w.type === 'unknown_field'),
      'should have unknown_field warning'
    );
  });

  test('type mismatch produces error', () => {
    createManifestTestEnv(tmpDir, healthCheckFeature(), {
      health_check: { frequency: 42, stale_threshold_days: 7, blocking_checks: false },
    });

    const result = runGsdTools('manifest validate', tmpDir);
    assert.ok(result.success, `Command failed: ${result.error}`);

    const output = JSON.parse(result.output);
    assert.strictEqual(output.valid, false, 'should be invalid');
    assert.ok(
      output.errors.some(e => e.type === 'type_mismatch'),
      'errors should include type_mismatch'
    );
  });

  test('missing feature is warning not error', () => {
    createManifestTestEnv(tmpDir, healthCheckFeature(), {
      mode: 'yolo',
    });

    const result = runGsdTools('manifest validate', tmpDir);
    assert.ok(result.success, `Command failed: ${result.error}`);

    const output = JSON.parse(result.output);
    assert.strictEqual(output.valid, true, 'missing feature should NOT cause invalid');
    assert.ok(
      output.warnings.some(w => w.type === 'missing_feature'),
      'should have missing_feature warning'
    );
  });

  test('counts features correctly', () => {
    createManifestTestEnv(tmpDir, twoFeatureManifest(), {
      health_check: { frequency: 'milestone-only', stale_threshold_days: 7, blocking_checks: false },
    });

    const result = runGsdTools('manifest validate', tmpDir);
    assert.ok(result.success, `Command failed: ${result.error}`);

    const output = JSON.parse(result.output);
    assert.strictEqual(output.features_checked, 2, 'manifest has 2 features');
    assert.strictEqual(output.features_present, 1, 'config has 1 feature section');
    assert.strictEqual(output.features_missing, 1, '1 feature missing');
  });
});

// ─────────────────────────────────────────────────────────────────────────────
// manifest get-prompts command
// ─────────────────────────────────────────────────────────────────────────────

describe('manifest get-prompts command', () => {
  let tmpDir;

  beforeEach(() => {
    tmpDir = createTempProject();
  });

  afterEach(() => {
    cleanup(tmpDir);
  });

  test('returns prompts for known feature', () => {
    createManifestTestEnv(tmpDir, healthCheckFeature(), {});

    const result = runGsdTools('manifest get-prompts health_check', tmpDir);
    assert.ok(result.success, `Command failed: ${result.error}`);

    const output = JSON.parse(result.output);
    assert.strictEqual(output.feature, 'health_check', 'feature name correct');
    assert.ok(Array.isArray(output.prompts), 'prompts should be array');
    assert.ok(output.prompts.length > 0, 'should have at least one prompt');
    assert.ok(output.schema, 'should include schema');
    assert.ok(output.schema.frequency, 'schema should contain frequency field');
  });

  test('errors on unknown feature', () => {
    createManifestTestEnv(tmpDir, healthCheckFeature(), {});

    const result = runGsdTools('manifest get-prompts nonexistent', tmpDir);
    assert.ok(!result.success, 'should fail for unknown feature');
    assert.ok(
      result.error.includes('Unknown feature') || result.error.includes('nonexistent'),
      'error should mention unknown feature'
    );
  });

  test('errors when no feature specified', () => {
    createManifestTestEnv(tmpDir, healthCheckFeature(), {});

    const result = runGsdTools('manifest get-prompts', tmpDir);
    assert.ok(!result.success, 'should fail when no feature specified');
    assert.ok(
      result.error.includes('required') || result.error.includes('Feature name'),
      'error should mention feature name required'
    );
  });
});

// ─────────────────────────────────────────────────────────────────────────────
// manifest self-test (real manifest)
// ─────────────────────────────────────────────────────────────────────────────

describe('manifest self-test (real manifest)', () => {
  const REPO_ROOT = path.resolve(__dirname, '..', '..');
  const MANIFEST_PATH = path.join(REPO_ROOT, 'get-shit-done', 'feature-manifest.json');

  test('real manifest is valid JSON with expected structure', () => {
    assert.ok(fs.existsSync(MANIFEST_PATH), `Manifest should exist at ${MANIFEST_PATH}`);

    const raw = fs.readFileSync(MANIFEST_PATH, 'utf-8');
    let manifest;
    assert.doesNotThrow(() => { manifest = JSON.parse(raw); }, 'Manifest should be valid JSON');

    // Top-level structure
    assert.strictEqual(typeof manifest.manifest_version, 'number', 'manifest_version should be integer');
    assert.ok(manifest.features, 'should have features object');
    assert.strictEqual(typeof manifest.features, 'object', 'features should be object');

    // Exactly 7 features
    const featureNames = Object.keys(manifest.features);
    assert.strictEqual(featureNames.length, 7, 'should have exactly 7 features');
    assert.ok(featureNames.includes('health_check'), 'should have health_check');
    assert.ok(featureNames.includes('devops'), 'should have devops');
    assert.ok(featureNames.includes('release'), 'should have release');
    assert.ok(featureNames.includes('signal_lifecycle'), 'should have signal_lifecycle');
    assert.ok(featureNames.includes('signal_collection'), 'should have signal_collection');
    assert.ok(featureNames.includes('spike'), 'should have spike');
    assert.ok(featureNames.includes('automation'), 'should have automation');

    // Each feature has required top-level fields
    for (const [name, feature] of Object.entries(manifest.features)) {
      assert.ok(feature.scope, `${name} should have scope`);
      assert.ok(feature.introduced, `${name} should have introduced`);
      assert.ok(feature.config_key, `${name} should have config_key`);
      assert.ok(feature.schema, `${name} should have schema`);
      assert.ok(typeof feature.schema === 'object', `${name}.schema should be object`);
      assert.ok(Object.keys(feature.schema).length > 0, `${name}.schema should be non-empty`);
      assert.ok(Array.isArray(feature.init_prompts), `${name} should have init_prompts array`);

      // Each field in schema has required metadata
      for (const [fieldName, fieldDef] of Object.entries(feature.schema)) {
        assert.ok(fieldDef.type, `${name}.${fieldName} should have type`);
        assert.ok(fieldDef.hasOwnProperty('default'), `${name}.${fieldName} should have default`);
        assert.ok(fieldDef.description, `${name}.${fieldName} should have description`);
      }
    }
  });

  test('real manifest defaults match loadConfig() defaults', () => {
    assert.ok(fs.existsSync(MANIFEST_PATH), `Manifest should exist at ${MANIFEST_PATH}`);
    const manifest = JSON.parse(fs.readFileSync(MANIFEST_PATH, 'utf-8'));

    // Critical defaults that MUST align between manifest and loadConfig()
    // loadConfig() does NOT produce feature section defaults -- it handles top-level config only.
    // The manifest defaults represent what new projects get when features are initialized.
    // We verify them against the documented canonical values.
    const expectedDefaults = {
      'health_check.frequency': 'milestone-only',
      'health_check.stale_threshold_days': 7,
      'health_check.blocking_checks': false,
      'devops.ci_provider': 'none',
      'devops.commit_convention': 'freeform',
      'release.version_file': 'none',
      'release.branch': 'main',
    };

    const drifts = [];

    for (const [path, expectedDefault] of Object.entries(expectedDefaults)) {
      const [featureName, fieldName] = path.split('.');
      const feature = manifest.features[featureName];
      assert.ok(feature, `Feature ${featureName} should exist in manifest`);
      const fieldSchema = feature.schema[fieldName];
      assert.ok(fieldSchema, `Field ${featureName}.${fieldName} should exist in schema`);

      if (fieldSchema.default !== expectedDefault) {
        drifts.push(
          `Default drift: ${path} -- manifest says '${fieldSchema.default}', expected '${expectedDefault}'`
        );
      }
    }

    assert.strictEqual(
      drifts.length,
      0,
      drifts.length > 0
        ? `Defaults alignment failures:\n  ${drifts.join('\n  ')}`
        : 'All defaults aligned'
    );
  });
});

// ─────────────────────────────────────────────────────────────────────────────
// manifest apply-migration command
// ─────────────────────────────────────────────────────────────────────────────

describe('manifest apply-migration command', () => {
  let tmpDir;

  beforeEach(() => {
    tmpDir = createTempProject();
  });

  afterEach(() => {
    cleanup(tmpDir);
  });

  test('adds missing feature sections with defaults', () => {
    // Config missing health_check entirely
    createManifestTestEnv(tmpDir, healthCheckFeature(), {
      mode: 'yolo',
      manifest_version: 1,
    });

    const result = runGsdTools('manifest apply-migration --raw', tmpDir);
    assert.ok(result.success, `Command failed: ${result.error}`);

    const output = JSON.parse(result.output);
    assert.ok(output.total_changes > 0, 'should have changes');
    assert.ok(
      output.changes.some(c => c.type === 'feature_added' && c.feature === 'health_check'),
      'should have feature_added change for health_check'
    );

    // Verify config was actually updated on disk
    const config = JSON.parse(fs.readFileSync(path.join(tmpDir, '.planning', 'config.json'), 'utf-8'));
    assert.ok(config.health_check, 'config should now have health_check section');
    assert.strictEqual(config.health_check.frequency, 'milestone-only', 'frequency should be default');
    assert.strictEqual(config.health_check.stale_threshold_days, 7, 'stale_threshold_days should be default');
    assert.strictEqual(config.health_check.blocking_checks, false, 'blocking_checks should be default');
  });

  test('adds missing fields to existing sections', () => {
    // Config has health_check but missing blocking_checks
    createManifestTestEnv(tmpDir, healthCheckFeature(), {
      manifest_version: 1,
      health_check: {
        frequency: 'milestone-only',
        stale_threshold_days: 7,
      },
    });

    const result = runGsdTools('manifest apply-migration --raw', tmpDir);
    assert.ok(result.success, `Command failed: ${result.error}`);

    const output = JSON.parse(result.output);
    assert.ok(
      output.changes.some(c => c.type === 'field_added' && c.field === 'blocking_checks'),
      'should have field_added change for blocking_checks'
    );

    const config = JSON.parse(fs.readFileSync(path.join(tmpDir, '.planning', 'config.json'), 'utf-8'));
    assert.strictEqual(config.health_check.blocking_checks, false, 'blocking_checks should be added with default');
  });

  test('coerces string boolean to boolean', () => {
    createManifestTestEnv(tmpDir, healthCheckFeature(), {
      manifest_version: 1,
      health_check: {
        frequency: 'milestone-only',
        stale_threshold_days: 7,
        blocking_checks: 'true',
      },
    });

    const result = runGsdTools('manifest apply-migration --raw', tmpDir);
    assert.ok(result.success, `Command failed: ${result.error}`);

    const output = JSON.parse(result.output);
    assert.ok(
      output.changes.some(c => c.type === 'type_coerced' && c.field === 'blocking_checks'),
      'should have type_coerced change for blocking_checks'
    );

    const config = JSON.parse(fs.readFileSync(path.join(tmpDir, '.planning', 'config.json'), 'utf-8'));
    assert.strictEqual(config.health_check.blocking_checks, true, 'blocking_checks should be coerced to boolean true');
  });

  test('coerces string number to number', () => {
    createManifestTestEnv(tmpDir, healthCheckFeature(), {
      manifest_version: 1,
      health_check: {
        frequency: 'milestone-only',
        stale_threshold_days: '7',
        blocking_checks: false,
      },
    });

    const result = runGsdTools('manifest apply-migration --raw', tmpDir);
    assert.ok(result.success, `Command failed: ${result.error}`);

    const output = JSON.parse(result.output);
    assert.ok(
      output.changes.some(c => c.type === 'type_coerced' && c.field === 'stale_threshold_days'),
      'should have type_coerced change for stale_threshold_days'
    );

    const config = JSON.parse(fs.readFileSync(path.join(tmpDir, '.planning', 'config.json'), 'utf-8'));
    assert.strictEqual(config.health_check.stale_threshold_days, 7, 'stale_threshold_days should be coerced to number 7');
  });

  test('updates manifest_version', () => {
    createManifestTestEnv(tmpDir, healthCheckFeature(), {
      manifest_version: 0,
      health_check: {
        frequency: 'milestone-only',
        stale_threshold_days: 7,
        blocking_checks: false,
      },
    });

    const result = runGsdTools('manifest apply-migration --raw', tmpDir);
    assert.ok(result.success, `Command failed: ${result.error}`);

    const output = JSON.parse(result.output);
    assert.ok(
      output.changes.some(c => c.type === 'manifest_version_updated'),
      'should have manifest_version_updated change'
    );

    const config = JSON.parse(fs.readFileSync(path.join(tmpDir, '.planning', 'config.json'), 'utf-8'));
    assert.strictEqual(config.manifest_version, 1, 'manifest_version should be updated to manifest version');
  });

  test('no changes when config is complete', () => {
    createManifestTestEnv(tmpDir, healthCheckFeature(), {
      manifest_version: 1,
      health_check: {
        frequency: 'milestone-only',
        stale_threshold_days: 7,
        blocking_checks: false,
      },
    });

    const result = runGsdTools('manifest apply-migration --raw', tmpDir);
    assert.ok(result.success, `Command failed: ${result.error}`);

    const output = JSON.parse(result.output);
    assert.strictEqual(output.total_changes, 0, 'should have no changes');
  });

  test('preserves existing values', () => {
    createManifestTestEnv(tmpDir, healthCheckFeature(), {
      manifest_version: 1,
      health_check: {
        frequency: 'every-phase',
        stale_threshold_days: 7,
        blocking_checks: false,
      },
    });

    const result = runGsdTools('manifest apply-migration --raw', tmpDir);
    assert.ok(result.success, `Command failed: ${result.error}`);

    const config = JSON.parse(fs.readFileSync(path.join(tmpDir, '.planning', 'config.json'), 'utf-8'));
    assert.strictEqual(config.health_check.frequency, 'every-phase', 'frequency should NOT be overwritten with default');
  });

  test('atomic write creates no .tmp residue', () => {
    createManifestTestEnv(tmpDir, healthCheckFeature(), {
      mode: 'yolo',
      manifest_version: 0,
    });

    const result = runGsdTools('manifest apply-migration --raw', tmpDir);
    assert.ok(result.success, `Command failed: ${result.error}`);

    const tmpFileExists = fs.existsSync(path.join(tmpDir, '.planning', 'config.json.tmp'));
    assert.strictEqual(tmpFileExists, false, 'no .tmp file should remain after atomic write');
  });

  test('reports all change types in output', () => {
    // Config with: missing devops feature, missing blocking_checks field, string stale_threshold_days
    createManifestTestEnv(tmpDir, twoFeatureManifest(), {
      manifest_version: 0,
      health_check: {
        frequency: 'milestone-only',
        stale_threshold_days: '7',
      },
    });

    const result = runGsdTools('manifest apply-migration --raw', tmpDir);
    assert.ok(result.success, `Command failed: ${result.error}`);

    const output = JSON.parse(result.output);
    const changeTypes = output.changes.map(c => c.type);
    assert.ok(changeTypes.includes('feature_added'), 'should include feature_added');
    assert.ok(changeTypes.includes('field_added'), 'should include field_added');
    assert.ok(changeTypes.includes('type_coerced'), 'should include type_coerced');
    assert.ok(changeTypes.includes('manifest_version_updated'), 'should include manifest_version_updated');
    assert.ok(output.total_changes >= 4, 'should have at least 4 changes');
  });
});

// ─────────────────────────────────────────────────────────────────────────────
// manifest log-migration command
// ─────────────────────────────────────────────────────────────────────────────

describe('manifest log-migration command', () => {
  let tmpDir;

  beforeEach(() => {
    tmpDir = createTempProject();
  });

  afterEach(() => {
    cleanup(tmpDir);
  });

  test('creates migration-log.md when it does not exist', () => {
    const changes = JSON.stringify([
      { type: 'feature_added', config_key: 'release', fields_added: ['version_file', 'changelog'] }
    ]);
    const result = runGsdTools(
      `manifest log-migration --from 1.12.0 --to 1.15.0 --changes '${changes}' --raw`,
      tmpDir
    );
    assert.ok(result.success, `Command failed: ${result.error}`);

    const logPath = path.join(tmpDir, '.planning', 'migration-log.md');
    assert.ok(fs.existsSync(logPath), 'migration-log.md should be created');

    const content = fs.readFileSync(logPath, 'utf-8');
    assert.ok(content.includes('# Migration Log'), 'should have header');
    assert.ok(content.includes('1.12.0 -> 1.15.0'), 'should have version range');
    assert.ok(content.includes('`release`'), 'should reference release config_key');
  });

  test('appends entry to existing migration-log.md', () => {
    const logPath = path.join(tmpDir, '.planning', 'migration-log.md');
    const existingContent = '# Migration Log\n\nTracks version upgrades applied to this project.\n\n## 1.0.0 -> 1.12.0 (2026-01-01T00:00:00.000Z)\n\n### Changes Applied\n- Added `health_check` section (frequency, stale_threshold_days, blocking_checks)\n\n---\n\n*Log is append-only.*\n';
    fs.writeFileSync(logPath, existingContent, 'utf-8');

    const changes = JSON.stringify([
      { type: 'field_added', feature: 'devops', field: 'environments', default_value: [] }
    ]);
    const result = runGsdTools(
      `manifest log-migration --from 1.12.0 --to 1.15.0 --changes '${changes}' --raw`,
      tmpDir
    );
    assert.ok(result.success, `Command failed: ${result.error}`);

    const content = fs.readFileSync(logPath, 'utf-8');
    // New entry should come before old entry
    const newEntryPos = content.indexOf('1.12.0 -> 1.15.0');
    const oldEntryPos = content.indexOf('1.0.0 -> 1.12.0');
    assert.ok(newEntryPos < oldEntryPos, 'new entry should be prepended before old entry');
  });

  test('formats feature_added changes correctly', () => {
    const changes = JSON.stringify([
      { type: 'feature_added', config_key: 'release', fields_added: ['version_file', 'changelog'] }
    ]);
    const result = runGsdTools(
      `manifest log-migration --from 1.12.0 --to 1.15.0 --changes '${changes}' --raw`,
      tmpDir
    );
    assert.ok(result.success, `Command failed: ${result.error}`);

    const logPath = path.join(tmpDir, '.planning', 'migration-log.md');
    const content = fs.readFileSync(logPath, 'utf-8');
    assert.ok(content.includes('Added `release` section (version_file, changelog)'), 'should format feature_added with fields');
  });

  test('formats field_added changes correctly', () => {
    const changes = JSON.stringify([
      { type: 'field_added', feature: 'devops', field: 'environments', default_value: [] }
    ]);
    const result = runGsdTools(
      `manifest log-migration --from 1.12.0 --to 1.15.0 --changes '${changes}' --raw`,
      tmpDir
    );
    assert.ok(result.success, `Command failed: ${result.error}`);

    const logPath = path.join(tmpDir, '.planning', 'migration-log.md');
    const content = fs.readFileSync(logPath, 'utf-8');
    assert.ok(content.includes('Added `devops.environments`:'), 'should format field_added with feature.field');
  });

  test('formats type_coerced changes correctly', () => {
    const changes = JSON.stringify([
      { type: 'type_coerced', feature: 'health_check', field: 'blocking_checks', from: 'true', to: true }
    ]);
    const result = runGsdTools(
      `manifest log-migration --from 1.12.0 --to 1.15.0 --changes '${changes}' --raw`,
      tmpDir
    );
    assert.ok(result.success, `Command failed: ${result.error}`);

    const logPath = path.join(tmpDir, '.planning', 'migration-log.md');
    const content = fs.readFileSync(logPath, 'utf-8');
    assert.ok(content.includes('Coerced `health_check.blocking_checks`'), 'should format type_coerced');
    assert.ok(content.includes('"true"'), 'should show from value');
    assert.ok(content.includes('true'), 'should show to value');
  });

  test('formats manifest_version_updated correctly', () => {
    const changes = JSON.stringify([
      { type: 'manifest_version_updated', from: 0, to: 1 }
    ]);
    const result = runGsdTools(
      `manifest log-migration --from 1.12.0 --to 1.15.0 --changes '${changes}' --raw`,
      tmpDir
    );
    assert.ok(result.success, `Command failed: ${result.error}`);

    const logPath = path.join(tmpDir, '.planning', 'migration-log.md');
    const content = fs.readFileSync(logPath, 'utf-8');
    assert.ok(content.includes('Updated manifest_version: 0 -> 1'), 'should show version from/to');
  });

  test('reports logged: true with path', () => {
    const changes = JSON.stringify([
      { type: 'feature_added', config_key: 'release', fields_added: ['version_file'] }
    ]);
    const result = runGsdTools(
      `manifest log-migration --from 1.12.0 --to 1.15.0 --changes '${changes}' --raw`,
      tmpDir
    );
    assert.ok(result.success, `Command failed: ${result.error}`);

    const parsed = JSON.parse(result.output);
    assert.strictEqual(parsed.logged, true, 'should report logged: true');
    assert.ok(parsed.path, 'should include path field');
    assert.ok(parsed.path.includes('migration-log.md'), 'path should reference migration-log.md');
  });
});

// ─────────────────────────────────────────────────────────────────────────────
// manifest auto-detect command
// ─────────────────────────────────────────────────────────────────────────────

describe('manifest auto-detect command', () => {
  let tmpDir;

  beforeEach(() => {
    tmpDir = createTempProject();
  });

  afterEach(() => {
    cleanup(tmpDir);
  });

  // Helper: create manifest with auto_detect rules in the temp project
  function setupAutoDetectEnv(tmpDir, features) {
    const manifestDir = path.join(tmpDir, '.claude', 'get-shit-done');
    fs.mkdirSync(manifestDir, { recursive: true });
    fs.writeFileSync(
      path.join(manifestDir, 'feature-manifest.json'),
      JSON.stringify({ manifest_version: 1, features }, null, 2)
    );
  }

  // Devops feature with auto_detect rules
  function devopsFeatureWithAutoDetect() {
    return {
      devops: {
        scope: 'project',
        introduced: '1.12.0',
        config_key: 'devops',
        schema: {
          ci_provider: { type: 'string', default: 'none' },
          deploy_target: { type: 'string', default: 'none' },
          commit_convention: { type: 'string', default: 'freeform' },
        },
        auto_detect: {
          ci_provider: [
            { check: 'dir_exists', path: '.github/workflows', value: 'github-actions' },
            { check: 'file_exists', path: '.gitlab-ci.yml', value: 'gitlab-ci' },
          ],
          deploy_target: [
            { check: 'file_exists', path: 'Dockerfile', value: 'docker' },
            { check: 'file_exists', path: 'vercel.json', value: 'vercel' },
          ],
        },
      },
    };
  }

  // Release feature with auto_detect rules
  function releaseFeatureWithAutoDetect() {
    return {
      release: {
        scope: 'project',
        introduced: '1.15.0',
        config_key: 'release',
        schema: {
          version_file: { type: 'string', default: 'none' },
        },
        auto_detect: {
          version_file: [
            { check: 'file_exists', path: 'package.json', value: 'package.json' },
            { check: 'file_exists', path: 'Cargo.toml', value: 'Cargo.toml' },
          ],
        },
      },
    };
  }

  test('detects CI provider from .github/workflows directory', () => {
    setupAutoDetectEnv(tmpDir, devopsFeatureWithAutoDetect());
    // Create the detection target
    fs.mkdirSync(path.join(tmpDir, '.github', 'workflows'), { recursive: true });

    const result = runGsdTools('manifest auto-detect devops --raw', tmpDir);
    assert.ok(result.success, `Command failed: ${result.error}`);

    const parsed = JSON.parse(result.output);
    assert.strictEqual(parsed.detected.ci_provider, 'github-actions', 'should detect github-actions');
  });

  test('detects deploy target from Dockerfile', () => {
    setupAutoDetectEnv(tmpDir, devopsFeatureWithAutoDetect());
    // Create Dockerfile
    fs.writeFileSync(path.join(tmpDir, 'Dockerfile'), 'FROM node:20\n');

    const result = runGsdTools('manifest auto-detect devops --raw', tmpDir);
    assert.ok(result.success, `Command failed: ${result.error}`);

    const parsed = JSON.parse(result.output);
    assert.strictEqual(parsed.detected.deploy_target, 'docker', 'should detect docker');
  });

  test('detects multiple fields simultaneously', () => {
    setupAutoDetectEnv(tmpDir, devopsFeatureWithAutoDetect());
    // Create both detection targets
    fs.mkdirSync(path.join(tmpDir, '.github', 'workflows'), { recursive: true });
    fs.writeFileSync(path.join(tmpDir, 'Dockerfile'), 'FROM node:20\n');

    const result = runGsdTools('manifest auto-detect devops --raw', tmpDir);
    assert.ok(result.success, `Command failed: ${result.error}`);

    const parsed = JSON.parse(result.output);
    assert.strictEqual(parsed.detected.ci_provider, 'github-actions', 'should detect ci_provider');
    assert.strictEqual(parsed.detected.deploy_target, 'docker', 'should detect deploy_target');
  });

  test('returns empty detected for feature with no auto_detect rules', () => {
    // health_check has no auto_detect
    setupAutoDetectEnv(tmpDir, {
      health_check: {
        scope: 'project',
        introduced: '1.12.0',
        config_key: 'health_check',
        schema: { frequency: { type: 'string', default: 'milestone-only' } },
      },
    });

    const result = runGsdTools('manifest auto-detect health_check --raw', tmpDir);
    assert.ok(result.success, `Command failed: ${result.error}`);

    const parsed = JSON.parse(result.output);
    assert.deepStrictEqual(parsed.detected, {}, 'should return empty detected object');
  });

  test('detects version_file from package.json', () => {
    setupAutoDetectEnv(tmpDir, releaseFeatureWithAutoDetect());
    // Create package.json
    fs.writeFileSync(path.join(tmpDir, 'package.json'), '{"name": "test", "version": "1.0.0"}\n');

    const result = runGsdTools('manifest auto-detect release --raw', tmpDir);
    assert.ok(result.success, `Command failed: ${result.error}`);

    const parsed = JSON.parse(result.output);
    assert.strictEqual(parsed.detected.version_file, 'package.json', 'should detect package.json');
  });

  test('file_exists does not match directories', () => {
    setupAutoDetectEnv(tmpDir, devopsFeatureWithAutoDetect());
    // Create a DIRECTORY named Dockerfile (not a file)
    fs.mkdirSync(path.join(tmpDir, 'Dockerfile'), { recursive: true });

    const result = runGsdTools('manifest auto-detect devops --raw', tmpDir);
    assert.ok(result.success, `Command failed: ${result.error}`);

    const parsed = JSON.parse(result.output);
    assert.strictEqual(parsed.detected.deploy_target, undefined, 'should NOT detect directory as file');
  });

  test('dir_exists does not match files', () => {
    setupAutoDetectEnv(tmpDir, devopsFeatureWithAutoDetect());
    // Create .github/workflows as a FILE (not a directory)
    fs.mkdirSync(path.join(tmpDir, '.github'), { recursive: true });
    fs.writeFileSync(path.join(tmpDir, '.github', 'workflows'), 'not a directory');

    const result = runGsdTools('manifest auto-detect devops --raw', tmpDir);
    assert.ok(result.success, `Command failed: ${result.error}`);

    const parsed = JSON.parse(result.output);
    assert.strictEqual(parsed.detected.ci_provider, undefined, 'should NOT detect file as directory');
  });
});

// ─────────────────────────────────────────────────────────────────────────────
// Backlog test helpers
// ─────────────────────────────────────────────────────────────────────────────

/**
 * Create a backlog item file directly in the temp project.
 * Used by list/update/stats tests to avoid dependency on the add command.
 */
function createBacklogItem(tmpDir, overrides = {}) {
  const itemsDir = path.join(tmpDir, '.planning', 'backlog', 'items');
  fs.mkdirSync(itemsDir, { recursive: true });
  const date = '2026-02-22';
  const slug = (overrides.title || 'test-item').toLowerCase().replace(/\s+/g, '-').replace(/[^a-z0-9-]/g, '');
  const id = overrides.id || `blog-${date}-${slug}`;
  const filename = overrides.filename || `${date}-${slug}.md`;
  const tags = overrides.tags || [];
  const tagsStr = tags.length > 0 ? `[${tags.join(', ')}]` : '[]';
  const content = `---
id: ${id}
title: ${overrides.title || 'Test item'}
tags: ${tagsStr}
theme: ${overrides.theme || 'general'}
priority: ${overrides.priority || 'MEDIUM'}
status: ${overrides.status || 'captured'}
source: ${overrides.source || 'command'}
promoted_to: ${overrides.promoted_to || 'null'}
milestone: ${overrides.milestone || 'null'}
created: ${overrides.created || '2026-02-22T10:00:00.000Z'}
updated: ${overrides.updated || '2026-02-22T10:00:00.000Z'}
---

## Description

Test backlog item.
`;
  fs.writeFileSync(path.join(itemsDir, filename), content, 'utf-8');
  return { id, filename, itemsDir };
}

// ─────────────────────────────────────────────────────────────────────────────
// backlog add command
// ─────────────────────────────────────────────────────────────────────────────

describe('backlog add command', () => {
  let tmpDir;

  beforeEach(() => {
    tmpDir = createTempProject();
  });

  afterEach(() => {
    cleanup(tmpDir);
  });

  test('creates backlog item with all frontmatter fields', () => {
    const result = runGsdTools(
      'backlog add --title "Add auth refresh" --tags "auth,security" --priority HIGH --theme "authentication" --source "conversation"',
      tmpDir
    );
    assert.ok(result.success, `Command failed: ${result.error}`);

    const output = JSON.parse(result.output);
    assert.strictEqual(output.created, true, 'should report created');
    assert.ok(output.id.startsWith('blog-'), 'id should start with blog-');

    // Read the created file and verify frontmatter
    const itemsDir = path.join(tmpDir, '.planning', 'backlog', 'items');
    const files = fs.readdirSync(itemsDir);
    assert.strictEqual(files.length, 1, 'should have one file');

    const content = fs.readFileSync(path.join(itemsDir, files[0]), 'utf-8');
    assert.ok(content.includes('id: '), 'should have id field');
    assert.ok(content.includes('title: Add auth refresh'), 'should have title');
    assert.ok(content.includes('auth') && content.includes('security'), 'should have tags');
    assert.ok(content.includes('theme: authentication'), 'should have theme');
    assert.ok(content.includes('priority: HIGH'), 'should have priority');
    assert.ok(content.includes('status: captured'), 'should have status');
    assert.ok(content.includes('source: conversation'), 'should have source');
    assert.ok(content.includes('promoted_to:'), 'should have promoted_to');
    assert.ok(content.includes('created:'), 'should have created');
    assert.ok(content.includes('updated:'), 'should have updated');
  });

  test('uses correct filename format (date-slug.md)', () => {
    const result = runGsdTools('backlog add --title "Fix login bug"', tmpDir);
    assert.ok(result.success, `Command failed: ${result.error}`);

    const itemsDir = path.join(tmpDir, '.planning', 'backlog', 'items');
    const files = fs.readdirSync(itemsDir);
    assert.strictEqual(files.length, 1);

    // Filename should match YYYY-MM-DD-fix-login-bug.md
    const filename = files[0];
    assert.ok(/^\d{4}-\d{2}-\d{2}-fix-login-bug\.md$/.test(filename), `Filename ${filename} should match date-slug pattern`);
  });

  test('handles filename collision with numeric suffix', () => {
    // Create first item
    const result1 = runGsdTools('backlog add --title "Duplicate idea"', tmpDir);
    assert.ok(result1.success, `First add failed: ${result1.error}`);

    // Create second item with same title
    const result2 = runGsdTools('backlog add --title "Duplicate idea"', tmpDir);
    assert.ok(result2.success, `Second add failed: ${result2.error}`);

    const itemsDir = path.join(tmpDir, '.planning', 'backlog', 'items');
    const files = fs.readdirSync(itemsDir).sort();
    assert.strictEqual(files.length, 2, 'should have two files');

    // First should be date-slug.md, second should be date-slug-2.md
    assert.ok(files.some(f => f.match(/^\d{4}-\d{2}-\d{2}-duplicate-idea\.md$/)), 'first file should be date-slug.md');
    assert.ok(files.some(f => f.match(/^\d{4}-\d{2}-\d{2}-duplicate-idea-2\.md$/)), 'second file should be date-slug-2.md');
  });

  test('defaults priority to MEDIUM when not specified', () => {
    const result = runGsdTools('backlog add --title "Some idea"', tmpDir);
    assert.ok(result.success, `Command failed: ${result.error}`);

    const itemsDir = path.join(tmpDir, '.planning', 'backlog', 'items');
    const files = fs.readdirSync(itemsDir);
    const content = fs.readFileSync(path.join(itemsDir, files[0]), 'utf-8');
    assert.ok(content.includes('priority: MEDIUM'), 'should default priority to MEDIUM');
  });

  test('defaults source to command when not specified', () => {
    const result = runGsdTools('backlog add --title "Some idea"', tmpDir);
    assert.ok(result.success, `Command failed: ${result.error}`);

    const itemsDir = path.join(tmpDir, '.planning', 'backlog', 'items');
    const files = fs.readdirSync(itemsDir);
    const content = fs.readFileSync(path.join(itemsDir, files[0]), 'utf-8');
    assert.ok(content.includes('source: command'), 'should default source to command');
  });

  test('creates .planning/backlog/items/ directory if missing', () => {
    // tmpDir has .planning/phases but NOT .planning/backlog
    const backlogDir = path.join(tmpDir, '.planning', 'backlog', 'items');
    assert.ok(!fs.existsSync(backlogDir), 'backlog dir should not exist yet');

    const result = runGsdTools('backlog add --title "First item"', tmpDir);
    assert.ok(result.success, `Command failed: ${result.error}`);

    assert.ok(fs.existsSync(backlogDir), 'backlog dir should be created');
    const files = fs.readdirSync(backlogDir);
    assert.strictEqual(files.length, 1, 'should have one file');
  });
});

// ─────────────────────────────────────────────────────────────────────────────
// backlog list command
// ─────────────────────────────────────────────────────────────────────────────

describe('backlog list command', () => {
  let tmpDir;

  beforeEach(() => {
    tmpDir = createTempProject();
  });

  afterEach(() => {
    cleanup(tmpDir);
  });

  test('returns empty list when no items', () => {
    const result = runGsdTools('backlog list', tmpDir);
    assert.ok(result.success, `Command failed: ${result.error}`);

    const output = JSON.parse(result.output);
    assert.strictEqual(output.count, 0, 'count should be 0');
    assert.deepStrictEqual(output.items, [], 'items should be empty array');
  });

  test('returns all items', () => {
    createBacklogItem(tmpDir, { title: 'Item one', filename: '2026-02-22-item-one.md', id: 'blog-2026-02-22-item-one' });
    createBacklogItem(tmpDir, { title: 'Item two', filename: '2026-02-22-item-two.md', id: 'blog-2026-02-22-item-two' });

    const result = runGsdTools('backlog list', tmpDir);
    assert.ok(result.success, `Command failed: ${result.error}`);

    const output = JSON.parse(result.output);
    assert.strictEqual(output.count, 2, 'count should be 2');
    assert.strictEqual(output.items.length, 2, 'should return 2 items');
  });

  test('filters by priority', () => {
    createBacklogItem(tmpDir, { title: 'High item', filename: '2026-02-22-high-item.md', id: 'blog-2026-02-22-high-item', priority: 'HIGH' });
    createBacklogItem(tmpDir, { title: 'Low item', filename: '2026-02-22-low-item.md', id: 'blog-2026-02-22-low-item', priority: 'LOW' });

    const result = runGsdTools('backlog list --priority HIGH', tmpDir);
    assert.ok(result.success, `Command failed: ${result.error}`);

    const output = JSON.parse(result.output);
    assert.strictEqual(output.count, 1, 'should have 1 HIGH item');
    assert.strictEqual(output.items[0].priority, 'HIGH', 'item should be HIGH priority');
  });

  test('filters by status', () => {
    createBacklogItem(tmpDir, { title: 'Captured item', filename: '2026-02-22-captured-item.md', id: 'blog-2026-02-22-captured-item', status: 'captured' });
    createBacklogItem(tmpDir, { title: 'Triaged item', filename: '2026-02-22-triaged-item.md', id: 'blog-2026-02-22-triaged-item', status: 'triaged' });

    const result = runGsdTools('backlog list --status triaged', tmpDir);
    assert.ok(result.success, `Command failed: ${result.error}`);

    const output = JSON.parse(result.output);
    assert.strictEqual(output.count, 1, 'should have 1 triaged item');
    assert.strictEqual(output.items[0].status, 'triaged', 'item should be triaged');
  });

  test('filters by tags', () => {
    createBacklogItem(tmpDir, { title: 'Auth item', filename: '2026-02-22-auth-item.md', id: 'blog-2026-02-22-auth-item', tags: ['auth', 'api'] });
    createBacklogItem(tmpDir, { title: 'UI item', filename: '2026-02-22-ui-item.md', id: 'blog-2026-02-22-ui-item', tags: ['ui'] });

    const result = runGsdTools('backlog list --tags "auth"', tmpDir);
    assert.ok(result.success, `Command failed: ${result.error}`);

    const output = JSON.parse(result.output);
    assert.strictEqual(output.count, 1, 'should have 1 auth-tagged item');
    assert.ok(output.items[0].tags.includes('auth'), 'item should have auth tag');
  });
});

// ─────────────────────────────────────────────────────────────────────────────
// backlog update command
// ─────────────────────────────────────────────────────────────────────────────

describe('backlog update command', () => {
  let tmpDir;

  beforeEach(() => {
    tmpDir = createTempProject();
  });

  afterEach(() => {
    cleanup(tmpDir);
  });

  test('updates frontmatter fields', () => {
    const { id } = createBacklogItem(tmpDir, { title: 'Update me', priority: 'HIGH', status: 'captured' });

    const result = runGsdTools(`backlog update ${id} --priority LOW --status triaged`, tmpDir);
    assert.ok(result.success, `Command failed: ${result.error}`);

    const output = JSON.parse(result.output);
    assert.strictEqual(output.updated, true, 'should report updated');

    // Read file and verify changes
    const itemsDir = path.join(tmpDir, '.planning', 'backlog', 'items');
    const files = fs.readdirSync(itemsDir);
    const content = fs.readFileSync(path.join(itemsDir, files[0]), 'utf-8');
    assert.ok(content.includes('priority: LOW'), 'priority should be LOW');
    assert.ok(content.includes('status: triaged'), 'status should be triaged');
  });

  test('updates the updated timestamp', () => {
    const originalTimestamp = '2026-01-01T10:00:00.000Z';
    const { id } = createBacklogItem(tmpDir, {
      title: 'Timestamp test',
      created: originalTimestamp,
      updated: originalTimestamp,
    });

    const result = runGsdTools(`backlog update ${id} --status triaged`, tmpDir);
    assert.ok(result.success, `Command failed: ${result.error}`);

    const itemsDir = path.join(tmpDir, '.planning', 'backlog', 'items');
    const files = fs.readdirSync(itemsDir);
    const content = fs.readFileSync(path.join(itemsDir, files[0]), 'utf-8');

    // Extract updated field
    const updatedMatch = content.match(/^updated:\s*(.+)$/m);
    assert.ok(updatedMatch, 'should have updated field');
    assert.notStrictEqual(updatedMatch[1].trim(), originalTimestamp, 'updated timestamp should be newer than original');
  });
});

// ─────────────────────────────────────────────────────────────────────────────
// backlog stats command
// ─────────────────────────────────────────────────────────────────────────────

describe('backlog stats command', () => {
  let tmpDir;

  beforeEach(() => {
    tmpDir = createTempProject();
  });

  afterEach(() => {
    cleanup(tmpDir);
  });

  test('returns counts by status and priority', () => {
    createBacklogItem(tmpDir, { title: 'High captured 1', filename: '2026-02-22-hc1.md', id: 'blog-hc1', priority: 'HIGH', status: 'captured' });
    createBacklogItem(tmpDir, { title: 'High captured 2', filename: '2026-02-22-hc2.md', id: 'blog-hc2', priority: 'HIGH', status: 'captured' });
    createBacklogItem(tmpDir, { title: 'Low triaged', filename: '2026-02-22-lt.md', id: 'blog-lt', priority: 'LOW', status: 'triaged' });

    const result = runGsdToolsWithEnv('backlog stats', tmpDir, {
      GSD_HOME: path.join(tmpDir, '__nonexistent_gsd_home__'),
    });
    assert.ok(result.success, `Command failed: ${result.error}`);

    const output = JSON.parse(result.output);
    assert.strictEqual(output.total, 3, 'total should be 3');
    assert.strictEqual(output.by_status.captured, 2, 'captured count should be 2');
    assert.strictEqual(output.by_status.triaged, 1, 'triaged count should be 1');
    assert.strictEqual(output.by_priority.HIGH, 2, 'HIGH count should be 2');
    assert.strictEqual(output.by_priority.LOW, 1, 'LOW count should be 1');
  });

  test('returns zero counts when no items', () => {
    const result = runGsdToolsWithEnv('backlog stats', tmpDir, {
      GSD_HOME: path.join(tmpDir, '__nonexistent_gsd_home__'),
    });
    assert.ok(result.success, `Command failed: ${result.error}`);

    const output = JSON.parse(result.output);
    assert.strictEqual(output.total, 0, 'total should be 0');
  });
});

// ─────────────────────────────────────────────────────────────────────────────
// todo auto-defaults
// ─────────────────────────────────────────────────────────────────────────────

describe('todo auto-defaults', () => {
  let tmpDir;

  beforeEach(() => {
    tmpDir = createTempProject();
  });

  afterEach(() => {
    cleanup(tmpDir);
  });

  test('cmdListTodos includes priority, source, status with defaults', () => {
    // Create todo file with ONLY created, title, area -- no priority/source/status
    const pendingDir = path.join(tmpDir, '.planning', 'todos', 'pending');
    fs.mkdirSync(pendingDir, { recursive: true });
    fs.writeFileSync(path.join(pendingDir, 'test-todo.md'), `---
created: 2026-02-22
title: Test todo
area: general
---

## Description

A test todo item.
`, 'utf-8');

    const result = runGsdTools('list-todos', tmpDir);
    assert.ok(result.success, `Command failed: ${result.error}`);

    const output = JSON.parse(result.output);
    assert.strictEqual(output.count, 1, 'should have 1 todo');
    const todo = output.todos[0];
    assert.strictEqual(todo.priority, 'MEDIUM', 'should default priority to MEDIUM');
    assert.strictEqual(todo.source, 'unknown', 'should default source to unknown');
    assert.strictEqual(todo.status, 'pending', 'should default status to pending');
  });

  test('cmdInitTodos includes priority, source, status with defaults', () => {
    // Create todo file with ONLY created, title, area
    const pendingDir = path.join(tmpDir, '.planning', 'todos', 'pending');
    fs.mkdirSync(pendingDir, { recursive: true });
    fs.writeFileSync(path.join(pendingDir, 'test-todo.md'), `---
created: 2026-02-22
title: Test todo for init
area: architecture
---

## Description

A test todo item for init.
`, 'utf-8');

    const result = runGsdTools('init todos', tmpDir);
    assert.ok(result.success, `Command failed: ${result.error}`);

    const output = JSON.parse(result.output);
    assert.ok(output.todos.length >= 1, 'should have at least 1 todo');
    const todo = output.todos[0];
    assert.strictEqual(todo.priority, 'MEDIUM', 'should default priority to MEDIUM');
    assert.strictEqual(todo.source, 'unknown', 'should default source to unknown');
    assert.strictEqual(todo.status, 'pending', 'should default status to pending');
  });
});

// ─────────────────────────────────────────────────────────────────────────────
// Helper: run gsd-tools with custom environment variables
// ─────────────────────────────────────────────────────────────────────────────

function runGsdToolsWithEnv(args, cwd, env) {
  try {
    const result = execSync(`node "${TOOLS_PATH}" ${args}`, {
      cwd,
      encoding: 'utf-8',
      stdio: ['pipe', 'pipe', 'pipe'],
      env: { ...process.env, ...env },
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

// ─────────────────────────────────────────────────────────────────────────────
// backlog group command
// ─────────────────────────────────────────────────────────────────────────────

describe('backlog group command', () => {
  let tmpDir;

  beforeEach(() => {
    tmpDir = createTempProject();
  });

  afterEach(() => {
    cleanup(tmpDir);
  });

  test('groups items by theme (default)', () => {
    createBacklogItem(tmpDir, { title: 'Auth login', filename: '2026-02-22-auth-login.md', id: 'blog-auth-login', theme: 'authentication' });
    createBacklogItem(tmpDir, { title: 'Auth refresh', filename: '2026-02-22-auth-refresh.md', id: 'blog-auth-refresh', theme: 'authentication' });
    createBacklogItem(tmpDir, { title: 'Better modals', filename: '2026-02-22-better-modals.md', id: 'blog-better-modals', theme: 'ux' });

    const result = runGsdTools('backlog group', tmpDir);
    assert.ok(result.success, `Command failed: ${result.error}`);

    const output = JSON.parse(result.output);
    assert.ok(output.groups, 'should have groups object');
    assert.strictEqual(output.groups['authentication'].length, 2, 'authentication group should have 2 items');
    assert.strictEqual(output.groups['ux'].length, 1, 'ux group should have 1 item');
  });

  test('groups items by tags', () => {
    createBacklogItem(tmpDir, { title: 'Auth API', filename: '2026-02-22-auth-api.md', id: 'blog-auth-api', tags: ['auth', 'api'] });
    createBacklogItem(tmpDir, { title: 'Auth UI', filename: '2026-02-22-auth-ui.md', id: 'blog-auth-ui', tags: ['auth', 'ui'] });

    const result = runGsdTools('backlog group --by tags', tmpDir);
    assert.ok(result.success, `Command failed: ${result.error}`);

    const output = JSON.parse(result.output);
    assert.ok(output.groups, 'should have groups object');
    assert.strictEqual(output.groups['auth'].length, 2, 'auth tag should have 2 items');
    assert.strictEqual(output.groups['api'].length, 1, 'api tag should have 1 item');
    assert.strictEqual(output.groups['ui'].length, 1, 'ui tag should have 1 item');
  });

  test('defaults to theme when no --by specified', () => {
    createBacklogItem(tmpDir, { title: 'Theme item', filename: '2026-02-22-theme-item.md', id: 'blog-theme-item', theme: 'testing' });

    const result = runGsdTools('backlog group', tmpDir);
    assert.ok(result.success, `Command failed: ${result.error}`);

    const output = JSON.parse(result.output);
    assert.strictEqual(output.group_by, 'theme', 'group_by should be theme by default');
  });
});

// ─────────────────────────────────────────────────────────────────────────────
// backlog promote command
// ─────────────────────────────────────────────────────────────────────────────

describe('backlog promote command', () => {
  let tmpDir;

  beforeEach(() => {
    tmpDir = createTempProject();
  });

  afterEach(() => {
    cleanup(tmpDir);
  });

  test('updates status to planned and sets promoted_to', () => {
    const { id } = createBacklogItem(tmpDir, { title: 'Promote me', status: 'captured' });

    const result = runGsdTools(`backlog promote ${id} --to REQ-42`, tmpDir);
    assert.ok(result.success, `Command failed: ${result.error}`);

    const output = JSON.parse(result.output);
    assert.strictEqual(output.promoted, true, 'should report promoted');
    assert.strictEqual(output.status, 'planned', 'status should be planned');
    assert.strictEqual(output.promoted_to, 'REQ-42', 'promoted_to should be REQ-42');

    // Read file and verify
    const itemsDir = path.join(tmpDir, '.planning', 'backlog', 'items');
    const files = fs.readdirSync(itemsDir);
    const content = fs.readFileSync(path.join(itemsDir, files[0]), 'utf-8');
    assert.ok(content.includes('status: planned'), 'file should have status: planned');
    assert.ok(content.includes('promoted_to: REQ-42'), 'file should have promoted_to: REQ-42');
  });

  test('sets status to planned without --to', () => {
    const { id } = createBacklogItem(tmpDir, { title: 'Promote no target', status: 'captured' });

    const result = runGsdTools(`backlog promote ${id}`, tmpDir);
    assert.ok(result.success, `Command failed: ${result.error}`);

    const output = JSON.parse(result.output);
    assert.strictEqual(output.promoted, true, 'should report promoted');
    assert.strictEqual(output.status, 'planned', 'status should be planned');
    assert.strictEqual(output.promoted_to, null, 'promoted_to should be null');

    // Read file and verify
    const itemsDir = path.join(tmpDir, '.planning', 'backlog', 'items');
    const files = fs.readdirSync(itemsDir);
    const content = fs.readFileSync(path.join(itemsDir, files[0]), 'utf-8');
    assert.ok(content.includes('status: planned'), 'file should have status: planned');
  });

  test('fails for nonexistent item ID', () => {
    const result = runGsdTools('backlog promote nonexistent-id', tmpDir);
    assert.strictEqual(result.success, false, 'should fail for nonexistent item');
    assert.ok(result.error.includes('not found') || result.error.includes('Error'), 'should contain error message');
  });
});

// ─────────────────────────────────────────────────────────────────────────────
// backlog index command
// ─────────────────────────────────────────────────────────────────────────────

describe('backlog index command', () => {
  let tmpDir;

  beforeEach(() => {
    tmpDir = createTempProject();
  });

  afterEach(() => {
    cleanup(tmpDir);
  });

  test('generates index.md with table of all items', () => {
    createBacklogItem(tmpDir, { title: 'High item', filename: '2026-02-22-high-item.md', id: 'blog-high-item', priority: 'HIGH' });
    createBacklogItem(tmpDir, { title: 'Low item', filename: '2026-02-22-low-item.md', id: 'blog-low-item', priority: 'LOW' });

    const result = runGsdTools('backlog index', tmpDir);
    assert.ok(result.success, `Command failed: ${result.error}`);

    const indexPath = path.join(tmpDir, '.planning', 'backlog', 'index.md');
    assert.ok(fs.existsSync(indexPath), 'index.md should exist');

    const content = fs.readFileSync(indexPath, 'utf-8');
    assert.ok(content.includes('# Backlog Index'), 'should have title');
    assert.ok(content.includes('blog-high-item'), 'should contain high item');
    assert.ok(content.includes('blog-low-item'), 'should contain low item');
    assert.ok(content.includes('| ID |'), 'should have table header');

    // HIGH should appear before LOW (sorted by priority)
    const highPos = content.indexOf('blog-high-item');
    const lowPos = content.indexOf('blog-low-item');
    assert.ok(highPos < lowPos, 'HIGH priority item should appear before LOW priority item');
  });

  test('index sorts by priority then date', () => {
    createBacklogItem(tmpDir, {
      title: 'High old', filename: '2026-02-20-high-old.md', id: 'blog-high-old',
      priority: 'HIGH', created: '2026-02-20T10:00:00.000Z',
    });
    createBacklogItem(tmpDir, {
      title: 'Low new', filename: '2026-02-22-low-new.md', id: 'blog-low-new',
      priority: 'LOW', created: '2026-02-22T10:00:00.000Z',
    });
    createBacklogItem(tmpDir, {
      title: 'High new', filename: '2026-02-22-high-new.md', id: 'blog-high-new',
      priority: 'HIGH', created: '2026-02-22T10:00:00.000Z',
    });

    const result = runGsdTools('backlog index', tmpDir);
    assert.ok(result.success, `Command failed: ${result.error}`);

    const indexPath = path.join(tmpDir, '.planning', 'backlog', 'index.md');
    const content = fs.readFileSync(indexPath, 'utf-8');

    // Expected order: HIGH-new (2026-02-22), HIGH-old (2026-02-20), LOW-new (2026-02-22)
    const highNewPos = content.indexOf('blog-high-new');
    const highOldPos = content.indexOf('blog-high-old');
    const lowNewPos = content.indexOf('blog-low-new');

    assert.ok(highNewPos < highOldPos, 'HIGH new (2026-02-22) should come before HIGH old (2026-02-20)');
    assert.ok(highOldPos < lowNewPos, 'HIGH old should come before LOW new');
  });
});

// ─────────────────────────────────────────────────────────────────────────────
// backlog --global flag
// ─────────────────────────────────────────────────────────────────────────────

describe('backlog --global flag', () => {
  let tmpDir;
  let globalDir;

  beforeEach(() => {
    tmpDir = createTempProject();
    globalDir = fs.mkdtempSync(path.join(require('os').tmpdir(), 'gsd-global-'));
  });

  afterEach(() => {
    cleanup(tmpDir);
    cleanup(globalDir);
  });

  test('backlog add --global creates item in GSD_HOME/backlog/items/', () => {
    const result = runGsdToolsWithEnv(
      'backlog add --title "Global idea" --global',
      tmpDir,
      { GSD_HOME: globalDir }
    );
    assert.ok(result.success, `Command failed: ${result.error}`);

    const globalItemsDir = path.join(globalDir, 'backlog', 'items');
    assert.ok(fs.existsSync(globalItemsDir), 'global items dir should exist');
    const files = fs.readdirSync(globalItemsDir).filter(f => f.endsWith('.md'));
    assert.strictEqual(files.length, 1, 'should have one global item');
  });

  test('backlog list --global reads from global directory', () => {
    // Create item directly in global dir
    const globalItemsDir = path.join(globalDir, 'backlog', 'items');
    fs.mkdirSync(globalItemsDir, { recursive: true });
    fs.writeFileSync(path.join(globalItemsDir, '2026-02-22-global-test.md'), `---
id: blog-global-test
title: Global test item
tags: []
theme: general
priority: HIGH
status: captured
source: command
promoted_to: null
created: 2026-02-22T10:00:00.000Z
updated: 2026-02-22T10:00:00.000Z
---

## Description

Global test item.
`, 'utf-8');

    const result = runGsdToolsWithEnv(
      'backlog list --global',
      tmpDir,
      { GSD_HOME: globalDir }
    );
    assert.ok(result.success, `Command failed: ${result.error}`);

    const output = JSON.parse(result.output);
    assert.strictEqual(output.count, 1, 'should have 1 global item');
    assert.strictEqual(output.items[0].id, 'blog-global-test', 'should return global item');
  });

  test('backlog index --global generates index in GSD_HOME/backlog/', () => {
    // Create item in global dir
    const globalItemsDir = path.join(globalDir, 'backlog', 'items');
    fs.mkdirSync(globalItemsDir, { recursive: true });
    fs.writeFileSync(path.join(globalItemsDir, '2026-02-22-global-idx.md'), `---
id: blog-global-idx
title: Global index item
tags: []
theme: general
priority: MEDIUM
status: captured
source: command
promoted_to: null
created: 2026-02-22T10:00:00.000Z
updated: 2026-02-22T10:00:00.000Z
---

## Description

Global index test.
`, 'utf-8');

    const result = runGsdToolsWithEnv(
      'backlog index --global',
      tmpDir,
      { GSD_HOME: globalDir }
    );
    assert.ok(result.success, `Command failed: ${result.error}`);

    const indexPath = path.join(globalDir, 'backlog', 'index.md');
    assert.ok(fs.existsSync(indexPath), 'global index.md should exist');
    const content = fs.readFileSync(indexPath, 'utf-8');
    assert.ok(content.includes('blog-global-idx'), 'index should contain global item');
  });
});

// ─────────────────────────────────────────────────────────────────────────────
// Phase 26-01: Milestone field + multi-status filter TDD tests
// ─────────────────────────────────────────────────────────────────────────────

describe('milestone field in backlog add', () => {
  let tmpDir;

  beforeEach(() => {
    tmpDir = createTempProject();
  });

  afterEach(() => {
    cleanup(tmpDir);
  });

  test('backlog add creates item with milestone: null in frontmatter', () => {
    const result = runGsdTools(
      'backlog add --title "Test milestone default"',
      tmpDir
    );
    assert.ok(result.success, `Command failed: ${result.error}`);

    const itemsDir = path.join(tmpDir, '.planning', 'backlog', 'items');
    const files = fs.readdirSync(itemsDir);
    assert.strictEqual(files.length, 1, 'should have one file');

    const content = fs.readFileSync(path.join(itemsDir, files[0]), 'utf-8');
    assert.ok(content.includes('milestone: null'), 'should have milestone: null in frontmatter');
  });
});

describe('milestone field in readBacklogItems', () => {
  let tmpDir;

  beforeEach(() => {
    tmpDir = createTempProject();
  });

  afterEach(() => {
    cleanup(tmpDir);
  });

  test('item with milestone: null in file returns JS null', () => {
    createBacklogItem(tmpDir, { title: 'Null milestone', milestone: null });

    const result = runGsdTools('backlog list', tmpDir);
    assert.ok(result.success, `Command failed: ${result.error}`);

    const output = JSON.parse(result.output);
    assert.strictEqual(output.items[0].milestone, null, 'milestone should be JS null');
  });

  test('item with milestone: v1.5 in file returns string v1.5', () => {
    createBacklogItem(tmpDir, { title: 'Versioned milestone', milestone: 'v1.5' });

    const result = runGsdTools('backlog list', tmpDir);
    assert.ok(result.success, `Command failed: ${result.error}`);

    const output = JSON.parse(result.output);
    assert.strictEqual(output.items[0].milestone, 'v1.5', 'milestone should be v1.5');
  });
});

describe('milestone field in backlog promote', () => {
  let tmpDir;

  beforeEach(() => {
    tmpDir = createTempProject();
  });

  afterEach(() => {
    cleanup(tmpDir);
  });

  test('promote with --milestone writes milestone and promoted_to to file', () => {
    const { id } = createBacklogItem(tmpDir, { title: 'Promote with milestone', status: 'captured' });

    const result = runGsdTools(
      `backlog promote ${id} --to AUTH-01 --milestone v1.5`,
      tmpDir
    );
    assert.ok(result.success, `Command failed: ${result.error}`);

    const output = JSON.parse(result.output);
    assert.strictEqual(output.milestone, 'v1.5', 'output should include milestone');

    // Read file and verify
    const itemsDir = path.join(tmpDir, '.planning', 'backlog', 'items');
    const files = fs.readdirSync(itemsDir);
    const content = fs.readFileSync(path.join(itemsDir, files[0]), 'utf-8');
    assert.ok(content.includes('milestone: v1.5'), 'file should have milestone: v1.5');
    assert.ok(content.includes('promoted_to: AUTH-01'), 'file should have promoted_to: AUTH-01');
    assert.ok(content.includes('status: planned'), 'file should have status: planned');
  });

  test('promote without --milestone leaves milestone unchanged', () => {
    const { id } = createBacklogItem(tmpDir, { title: 'Promote no milestone', status: 'captured' });

    const result = runGsdTools(
      `backlog promote ${id} --to AUTH-02`,
      tmpDir
    );
    assert.ok(result.success, `Command failed: ${result.error}`);

    // Read file and verify milestone still null
    const itemsDir = path.join(tmpDir, '.planning', 'backlog', 'items');
    const files = fs.readdirSync(itemsDir);
    const content = fs.readFileSync(path.join(itemsDir, files[0]), 'utf-8');
    assert.ok(content.includes('milestone: null'), 'milestone should remain null');
  });
});

describe('milestone field in backlog update CLI', () => {
  let tmpDir;

  beforeEach(() => {
    tmpDir = createTempProject();
  });

  afterEach(() => {
    cleanup(tmpDir);
  });

  test('backlog update --milestone writes milestone to file', () => {
    const { id } = createBacklogItem(tmpDir, { title: 'Update milestone' });

    const result = runGsdTools(
      `backlog update ${id} --milestone v1.5`,
      tmpDir
    );
    assert.ok(result.success, `Command failed: ${result.error}`);

    const itemsDir = path.join(tmpDir, '.planning', 'backlog', 'items');
    const files = fs.readdirSync(itemsDir);
    const content = fs.readFileSync(path.join(itemsDir, files[0]), 'utf-8');
    assert.ok(content.includes('milestone: v1.5'), 'file should have milestone: v1.5');
  });
});

describe('milestone column in backlog index', () => {
  let tmpDir;

  beforeEach(() => {
    tmpDir = createTempProject();
  });

  afterEach(() => {
    cleanup(tmpDir);
  });

  test('index table includes Milestone column with version', () => {
    createBacklogItem(tmpDir, {
      title: 'Milestone item',
      filename: '2026-02-22-milestone-item.md',
      id: 'blog-milestone-item',
      milestone: 'v1.5',
    });

    const result = runGsdTools('backlog index --raw', tmpDir);
    assert.ok(result.success, `Command failed: ${result.error}`);

    const indexPath = path.join(tmpDir, '.planning', 'backlog', 'index.md');
    const content = fs.readFileSync(indexPath, 'utf-8');
    assert.ok(content.includes('Milestone'), 'table header should include Milestone');
    assert.ok(content.includes('v1.5'), 'row should show v1.5 milestone');
  });

  test('index table shows dash for null milestone', () => {
    createBacklogItem(tmpDir, {
      title: 'No milestone item',
      filename: '2026-02-22-no-milestone.md',
      id: 'blog-no-milestone',
    });

    const result = runGsdTools('backlog index --raw', tmpDir);
    assert.ok(result.success, `Command failed: ${result.error}`);

    const indexPath = path.join(tmpDir, '.planning', 'backlog', 'index.md');
    const content = fs.readFileSync(indexPath, 'utf-8');
    assert.ok(content.includes('Milestone'), 'table header should include Milestone');
    // The null milestone row should have a dash
    const lines = content.split('\n');
    const dataRow = lines.find(l => l.includes('blog-no-milestone'));
    assert.ok(dataRow, 'should have row for item');
    // Verify it does NOT show 'null' as text but rather empty or dash
    assert.ok(!dataRow.includes('| null |'), 'should not show literal "null" in milestone column');
  });
});

describe('multi-status filter in backlog list', () => {
  let tmpDir;

  beforeEach(() => {
    tmpDir = createTempProject();
  });

  afterEach(() => {
    cleanup(tmpDir);
  });

  test('backlog list --status captured,triaged returns items matching either', () => {
    createBacklogItem(tmpDir, { title: 'Captured item', filename: '2026-02-22-cap.md', id: 'blog-cap', status: 'captured' });
    createBacklogItem(tmpDir, { title: 'Triaged item', filename: '2026-02-22-tri.md', id: 'blog-tri', status: 'triaged' });
    createBacklogItem(tmpDir, { title: 'Planned item', filename: '2026-02-22-plan.md', id: 'blog-plan', status: 'planned' });

    const result = runGsdTools('backlog list --status captured,triaged', tmpDir);
    assert.ok(result.success, `Command failed: ${result.error}`);

    const output = JSON.parse(result.output);
    assert.strictEqual(output.count, 2, 'should return 2 items (captured + triaged)');
    const ids = output.items.map(i => i.id).sort();
    assert.deepStrictEqual(ids, ['blog-cap', 'blog-tri'], 'should return captured and triaged items');
  });

  test('backlog list --status planned still works for single status', () => {
    createBacklogItem(tmpDir, { title: 'Captured item', filename: '2026-02-22-cap2.md', id: 'blog-cap2', status: 'captured' });
    createBacklogItem(tmpDir, { title: 'Planned item', filename: '2026-02-22-plan2.md', id: 'blog-plan2', status: 'planned' });

    const result = runGsdTools('backlog list --status planned', tmpDir);
    assert.ok(result.success, `Command failed: ${result.error}`);

    const output = JSON.parse(result.output);
    assert.strictEqual(output.count, 1, 'should return 1 planned item');
    assert.strictEqual(output.items[0].id, 'blog-plan2', 'should be the planned item');
  });
});

describe('createBacklogItem helper milestone field', () => {
  let tmpDir;

  beforeEach(() => {
    tmpDir = createTempProject();
  });

  afterEach(() => {
    cleanup(tmpDir);
  });

  test('default createBacklogItem includes milestone: null', () => {
    createBacklogItem(tmpDir, {});

    const itemsDir = path.join(tmpDir, '.planning', 'backlog', 'items');
    const files = fs.readdirSync(itemsDir);
    const content = fs.readFileSync(path.join(itemsDir, files[0]), 'utf-8');
    assert.ok(content.includes('milestone: null'), 'should have milestone: null');
  });

  test('createBacklogItem with milestone override writes version', () => {
    createBacklogItem(tmpDir, { milestone: 'v1.5' });

    const itemsDir = path.join(tmpDir, '.planning', 'backlog', 'items');
    const files = fs.readdirSync(itemsDir);
    const content = fs.readFileSync(path.join(itemsDir, files[0]), 'utf-8');
    assert.ok(content.includes('milestone: v1.5'), 'should have milestone: v1.5');
  });
});

describe('backward compatibility: pre-Phase-26 items without milestone', () => {
  let tmpDir;

  beforeEach(() => {
    tmpDir = createTempProject();
  });

  afterEach(() => {
    cleanup(tmpDir);
  });

  test('item without milestone field parses with milestone: null default', () => {
    // Manually create a pre-Phase-26 item (no milestone line)
    const itemsDir = path.join(tmpDir, '.planning', 'backlog', 'items');
    fs.mkdirSync(itemsDir, { recursive: true });
    fs.writeFileSync(path.join(itemsDir, '2026-02-22-old-item.md'), `---
id: blog-old-item
title: Old item
tags: []
theme: general
priority: MEDIUM
status: captured
source: command
promoted_to: null
created: 2026-02-22T10:00:00.000Z
updated: 2026-02-22T10:00:00.000Z
---

## Description

Pre-Phase-26 item without milestone field.
`, 'utf-8');

    const result = runGsdTools('backlog list', tmpDir);
    assert.ok(result.success, `Command failed: ${result.error}`);

    const output = JSON.parse(result.output);
    assert.strictEqual(output.items[0].milestone, null, 'milestone should default to null for old items');
  });

  test('promote on item without milestone preserves fields and adds milestone', () => {
    // Create item without milestone field
    const itemsDir = path.join(tmpDir, '.planning', 'backlog', 'items');
    fs.mkdirSync(itemsDir, { recursive: true });
    fs.writeFileSync(path.join(itemsDir, '2026-02-22-old-promote.md'), `---
id: blog-old-promote
title: Old promote item
tags: [auth]
theme: security
priority: HIGH
status: captured
source: conversation
promoted_to: null
created: 2026-02-22T10:00:00.000Z
updated: 2026-02-22T10:00:00.000Z
---

## Description

Old item to promote.
`, 'utf-8');

    const result = runGsdTools(
      'backlog promote blog-old-promote --to REQ-01 --milestone v2.0',
      tmpDir
    );
    assert.ok(result.success, `Command failed: ${result.error}`);

    const content = fs.readFileSync(path.join(itemsDir, '2026-02-22-old-promote.md'), 'utf-8');
    assert.ok(content.includes('milestone: v2.0'), 'should have milestone: v2.0');
    assert.ok(content.includes('id: blog-old-promote'), 'id should be intact');
    assert.ok(content.includes('title: Old promote item'), 'title should be intact');
    assert.ok(content.includes('auth'), 'tags should be intact');
    assert.ok(content.includes('status: planned'), 'status should be planned');
    assert.ok(content.includes('promoted_to: REQ-01'), 'promoted_to should be REQ-01');
  });

  test('update --milestone on item without prior milestone adds it', () => {
    // Create item without milestone field
    const itemsDir = path.join(tmpDir, '.planning', 'backlog', 'items');
    fs.mkdirSync(itemsDir, { recursive: true });
    fs.writeFileSync(path.join(itemsDir, '2026-02-22-old-update.md'), `---
id: blog-old-update
title: Old update item
tags: []
theme: general
priority: MEDIUM
status: captured
source: command
promoted_to: null
created: 2026-02-22T10:00:00.000Z
updated: 2026-02-22T10:00:00.000Z
---

## Description

Old item to update.
`, 'utf-8');

    const result = runGsdTools(
      'backlog update blog-old-update --milestone v1.5',
      tmpDir
    );
    assert.ok(result.success, `Command failed: ${result.error}`);

    const content = fs.readFileSync(path.join(itemsDir, '2026-02-22-old-update.md'), 'utf-8');
    assert.ok(content.includes('milestone: v1.5'), 'should have milestone: v1.5');
    assert.ok(content.includes('id: blog-old-update'), 'id should be intact');
    assert.ok(content.includes('title: Old update item'), 'title should be intact');
    assert.ok(content.includes('priority: MEDIUM'), 'priority should be intact');
  });
});

// ─────────────────────────────────────────────────────────────────────────────
// BINT-05: reader enumeration verification
// ─────────────────────────────────────────────────────────────────────────────

describe('BINT-05: reader enumeration verification', () => {
  let tmpDir;

  beforeEach(() => {
    tmpDir = createTempProject();
  });

  afterEach(() => {
    cleanup(tmpDir);
  });

  // ── Mixed-schema reader tests (B3-B4, B7) ──────────────────────────────

  test('backlog group handles items with and without milestone field', () => {
    // Item WITH milestone field (via createBacklogItem helper)
    createBacklogItem(tmpDir, {
      title: 'With milestone',
      filename: '2026-02-22-with-milestone.md',
      id: 'blog-with-milestone',
      milestone: 'v1.5',
      theme: 'feature',
    });

    // Item WITHOUT milestone field (pre-Phase-26 format, manually created)
    const itemsDir = path.join(tmpDir, '.planning', 'backlog', 'items');
    fs.writeFileSync(path.join(itemsDir, '2026-02-22-no-milestone.md'), `---
id: blog-no-milestone
title: No milestone
tags: []
theme: feature
priority: MEDIUM
status: captured
source: command
promoted_to: null
created: 2026-02-22T10:00:00.000Z
updated: 2026-02-22T10:00:00.000Z
---

## Description

Pre-Phase-26 item without milestone line.
`, 'utf-8');

    const result = runGsdTools('backlog group --by theme', tmpDir);
    assert.ok(result.success, `Command failed: ${result.error}`);

    const output = JSON.parse(result.output);
    assert.strictEqual(output.total_items, 2, 'should count both items');
    assert.ok(output.groups['feature'], 'should have feature group');
    assert.strictEqual(output.groups['feature'].length, 2, 'feature group should have 2 items');
  });

  test('backlog stats counts items regardless of milestone field presence', () => {
    // Item WITH milestone field
    createBacklogItem(tmpDir, {
      title: 'Has milestone',
      filename: '2026-02-22-has-milestone.md',
      id: 'blog-has-milestone',
      milestone: 'v1.5',
      status: 'captured',
    });

    // Item WITHOUT milestone field (pre-Phase-26 format)
    const itemsDir = path.join(tmpDir, '.planning', 'backlog', 'items');
    fs.writeFileSync(path.join(itemsDir, '2026-02-22-lacks-milestone.md'), `---
id: blog-lacks-milestone
title: Lacks milestone
tags: []
theme: general
priority: HIGH
status: triaged
source: command
promoted_to: null
created: 2026-02-22T10:00:00.000Z
updated: 2026-02-22T10:00:00.000Z
---

## Description

Pre-Phase-26 item without milestone line.
`, 'utf-8');

    // Use GSD_HOME pointing to nonexistent dir to isolate from global items
    const result = runGsdToolsWithEnv('backlog stats', tmpDir, {
      GSD_HOME: path.join(tmpDir, '__nonexistent_gsd_home__'),
    });
    assert.ok(result.success, `Command failed: ${result.error}`);

    const output = JSON.parse(result.output);
    assert.strictEqual(output.total, 2, 'total should count both items');
    assert.strictEqual(output.by_status.captured, 1, 'captured count should be 1');
    assert.strictEqual(output.by_status.triaged, 1, 'triaged count should be 1');
    assert.strictEqual(output.by_priority.MEDIUM, 1, 'MEDIUM count should be 1');
    assert.strictEqual(output.by_priority.HIGH, 1, 'HIGH count should be 1');
  });

  test('backlog index includes Milestone column for mixed items', () => {
    // Item WITH milestone
    createBacklogItem(tmpDir, {
      title: 'Milestone item',
      filename: '2026-02-22-milestone-item.md',
      id: 'blog-milestone-item',
      milestone: 'v1.5',
      priority: 'HIGH',
    });

    // Item WITHOUT milestone field (pre-Phase-26 format)
    const itemsDir = path.join(tmpDir, '.planning', 'backlog', 'items');
    fs.writeFileSync(path.join(itemsDir, '2026-02-22-no-ms-item.md'), `---
id: blog-no-ms-item
title: No milestone item
tags: []
theme: general
priority: LOW
status: captured
source: command
promoted_to: null
created: 2026-02-22T10:00:00.000Z
updated: 2026-02-22T10:00:00.000Z
---

## Description

Pre-Phase-26 item without milestone line.
`, 'utf-8');

    const result = runGsdTools('backlog index', tmpDir);
    assert.ok(result.success, `Command failed: ${result.error}`);

    const indexPath = path.join(tmpDir, '.planning', 'backlog', 'index.md');
    assert.ok(fs.existsSync(indexPath), 'index.md should exist');

    const content = fs.readFileSync(indexPath, 'utf-8');
    assert.ok(content.includes('| Milestone |'), 'table header should include Milestone column');
    assert.ok(content.includes('v1.5'), 'row with milestone should show v1.5');
    // Item without milestone should show em-dash fallback
    assert.ok(content.includes('\u2014'), 'row without milestone should show em-dash fallback');
  });

  // ── Todo system isolation tests (T1-T2) ────────────────────────────────

  test('cmdListTodos output is unchanged by backlog schema changes', () => {
    // Create a standard pending todo file (no milestone field)
    const pendingDir = path.join(tmpDir, '.planning', 'todos', 'pending');
    fs.mkdirSync(pendingDir, { recursive: true });
    fs.writeFileSync(path.join(pendingDir, 'isolation-test.md'), `---
created: 2026-02-22
title: Todo isolation test
area: testing
priority: HIGH
source: conversation
status: pending
---

## Description

This todo should not have a milestone field.
`, 'utf-8');

    const result = runGsdTools('list-todos', tmpDir);
    assert.ok(result.success, `Command failed: ${result.error}`);

    const output = JSON.parse(result.output);
    assert.strictEqual(output.count, 1, 'should have 1 todo');
    const todo = output.todos[0];
    assert.strictEqual(todo.title, 'Todo isolation test', 'title should match');
    assert.strictEqual(todo.area, 'testing', 'area should match');
    assert.strictEqual(todo.priority, 'HIGH', 'priority should match');
    assert.strictEqual(todo.source, 'conversation', 'source should match');
    assert.strictEqual(todo.status, 'pending', 'status should match');
    // Verify NO milestone field in todo object
    assert.strictEqual(todo.milestone, undefined, 'todo should NOT have milestone field');
    assert.ok(!('milestone' in todo), 'milestone key should not exist in todo object');
  });

  test('todo with auto-defaults does not gain milestone field', () => {
    // Create a minimal todo file (only title and area, no priority/source/status)
    const pendingDir = path.join(tmpDir, '.planning', 'todos', 'pending');
    fs.mkdirSync(pendingDir, { recursive: true });
    fs.writeFileSync(path.join(pendingDir, 'minimal-todo.md'), `---
created: 2026-02-22
title: Minimal todo
area: general
---

## Description

Minimal todo with only title and area.
`, 'utf-8');

    const result = runGsdTools('init todos', tmpDir);
    assert.ok(result.success, `Command failed: ${result.error}`);

    const output = JSON.parse(result.output);
    assert.ok(output.todos, 'should have todos array');
    assert.strictEqual(output.todo_count, 1, 'should have 1 todo');
    const todo = output.todos[0];
    // Auto-defaults should be applied
    assert.strictEqual(todo.priority, 'MEDIUM', 'should default priority to MEDIUM');
    assert.strictEqual(todo.source, 'unknown', 'should default source to unknown');
    assert.strictEqual(todo.status, 'pending', 'should default status to pending');
    // NO milestone field should exist
    assert.strictEqual(todo.milestone, undefined, 'todo should NOT have milestone field');
    assert.ok(!('milestone' in todo), 'milestone key should not exist in todo object');
  });
});

describe('signal frontmatter validation', () => {
  let tmpDir;

  beforeEach(() => {
    tmpDir = createTempProject();
  });

  afterEach(() => {
    cleanup(tmpDir);
  });

  test('valid critical signal with all fields', () => {
    const signalPath = path.join(tmpDir, 'critical-signal.md');
    fs.writeFileSync(signalPath, `---
id: sig-2026-02-28-test-critical
type: signal
project: test-project
tags: [schema, validation]
created: 2026-02-28T10:00:00Z
severity: critical
signal_type: deviation
evidence:
  supporting:
    - "Build failed 3 times"
  counter:
    - "None observed"
confidence: high
confidence_basis: "Repeated failures observed"
lifecycle_state: detected
signal_category: negative
---

# Test Critical Signal
`);

    const result = runGsdTools(`frontmatter validate ${signalPath} --schema signal`, tmpDir);
    assert.ok(result.success, `Command failed: ${result.error}`);
    const output = JSON.parse(result.output);
    assert.strictEqual(output.valid, true, 'critical signal with all fields should be valid');
    assert.strictEqual(output.schema, 'signal');
    assert.strictEqual(output.missing.length, 0, 'no missing fields');
  });

  test('valid notable signal without evidence produces warnings', () => {
    const signalPath = path.join(tmpDir, 'notable-signal.md');
    fs.writeFileSync(signalPath, `---
id: sig-2026-02-28-test-notable
type: signal
project: test-project
tags: [schema]
created: 2026-02-28T10:00:00Z
severity: notable
signal_type: deviation
---

# Test Notable Signal
`);

    const result = runGsdTools(`frontmatter validate ${signalPath} --schema signal`, tmpDir);
    assert.ok(result.success, `Command failed: ${result.error}`);
    const output = JSON.parse(result.output);
    assert.strictEqual(output.valid, true, 'notable signal without evidence should be valid');
    assert.ok(output.warnings.length > 0, 'should have warnings for missing recommended fields');
  });

  test('valid minor signal with minimal fields', () => {
    const signalPath = path.join(tmpDir, 'minor-signal.md');
    fs.writeFileSync(signalPath, `---
id: sig-2026-02-28-test-minor
type: signal
project: test-project
tags: [minor]
created: 2026-02-28T10:00:00Z
severity: minor
signal_type: deviation
---

# Test Minor Signal
`);

    const result = runGsdTools(`frontmatter validate ${signalPath} --schema signal`, tmpDir);
    assert.ok(result.success, `Command failed: ${result.error}`);
    const output = JSON.parse(result.output);
    assert.strictEqual(output.valid, true, 'minor signal with only required fields should be valid');
  });

  test('invalid signal missing required field signal_type', () => {
    const signalPath = path.join(tmpDir, 'invalid-signal.md');
    fs.writeFileSync(signalPath, `---
id: sig-2026-02-28-test-invalid
type: signal
project: test-project
tags: [test]
created: 2026-02-28T10:00:00Z
severity: notable
---

# Missing signal_type
`);

    const result = runGsdTools(`frontmatter validate ${signalPath} --schema signal`, tmpDir);
    assert.ok(result.success, `Command failed: ${result.error}`);
    const output = JSON.parse(result.output);
    assert.strictEqual(output.valid, false, 'signal missing signal_type should be invalid');
    assert.ok(output.missing.includes('signal_type'), 'missing should include signal_type');
  });

  test('invalid critical signal without evidence', () => {
    const signalPath = path.join(tmpDir, 'critical-no-evidence.md');
    fs.writeFileSync(signalPath, `---
id: sig-2026-02-28-critical-no-ev
type: signal
project: test-project
tags: [critical]
created: 2026-02-28T10:00:00Z
severity: critical
signal_type: deviation
lifecycle_state: detected
---

# Critical without evidence
`);

    const result = runGsdTools(`frontmatter validate ${signalPath} --schema signal`, tmpDir);
    assert.ok(result.success, `Command failed: ${result.error}`);
    const output = JSON.parse(result.output);
    assert.strictEqual(output.valid, false, 'new critical signal without evidence should be invalid');
    assert.ok(output.missing.includes('evidence'), 'missing should include evidence');
  });

  test('backward compatibility with date-slug format signal', () => {
    const signalPath = path.join(tmpDir, 'date-slug-signal.md');
    fs.writeFileSync(signalPath, `---
id: sig-2026-02-28-example-pattern
type: signal
project: get-shit-done-reflect
tags: [backward-compat, test]
created: 2026-02-28T10:00:00Z
severity: notable
signal_type: deviation
phase: 31
plan: 3
polarity: negative
source: executor
occurrence_count: 1
related_signals: []
runtime: claude-code
model: claude-opus-4-20250514
---

# Date-slug format signal
`);

    const result = runGsdTools(`frontmatter validate ${signalPath} --schema signal`, tmpDir);
    assert.ok(result.success, `Command failed: ${result.error}`);
    const output = JSON.parse(result.output);
    assert.strictEqual(output.valid, true, 'date-slug format signal should be valid');
    assert.ok(output.warnings.length > 0, 'should warn about missing recommended fields');
  });

  test('backward compat: critical signal without lifecycle_state downgrades evidence to warning', () => {
    const signalPath = path.join(tmpDir, 'pre-existing-critical.md');
    fs.writeFileSync(signalPath, `---
id: sig-2026-02-11-kb-data-loss-migration-gap
type: signal
project: get-shit-done-reflect
tags: [knowledge-base, migration]
created: 2026-02-11T10:00:00Z
severity: critical
signal_type: deviation
phase: 25
polarity: negative
source: executor
---

# Pre-existing critical signal without evidence
`);

    const result = runGsdTools(`frontmatter validate ${signalPath} --schema signal`, tmpDir);
    assert.ok(result.success, `Command failed: ${result.error}`);
    const output = JSON.parse(result.output);
    assert.strictEqual(output.valid, true, 'pre-existing critical signal without lifecycle_state should be valid');
    assert.strictEqual(output.missing.length, 0, 'no missing fields in backward compat mode');
    const warningStr = output.warnings.join(',');
    assert.ok(warningStr.includes('backward_compat: evidence'), 'should include backward_compat warning for evidence');
  });

  test('new critical signal with lifecycle_state but no evidence fails', () => {
    const signalPath = path.join(tmpDir, 'new-critical-no-evidence.md');
    fs.writeFileSync(signalPath, `---
id: sig-2026-02-28-new-critical
type: signal
project: test-project
tags: [schema]
created: 2026-02-28T10:00:00Z
severity: critical
signal_type: deviation
lifecycle_state: detected
signal_category: negative
---

# New critical signal without evidence
`);

    const result = runGsdTools(`frontmatter validate ${signalPath} --schema signal`, tmpDir);
    assert.ok(result.success, `Command failed: ${result.error}`);
    const output = JSON.parse(result.output);
    assert.strictEqual(output.valid, false, 'new critical signal with lifecycle_state but no evidence should fail');
    assert.ok(output.missing.includes('evidence'), 'missing should include evidence');
  });

  test('new critical signal with empty evidence object fails', () => {
    const signalPath = path.join(tmpDir, 'critical-empty-evidence.md');
    fs.writeFileSync(signalPath, `---
id: sig-2026-02-28-empty-evidence
type: signal
project: test-project
tags: [schema]
created: 2026-02-28T10:00:00Z
severity: critical
signal_type: deviation
lifecycle_state: detected
signal_category: negative
evidence:
  supporting: []
  counter: []
confidence: medium
confidence_basis: "untested"
---

# Critical signal with empty evidence
`);

    const result = runGsdTools(`frontmatter validate ${signalPath} --schema signal`, tmpDir);
    assert.ok(result.success, `Command failed: ${result.error}`);
    const output = JSON.parse(result.output);
    assert.strictEqual(output.valid, false, 'critical signal with empty evidence should be invalid');
    assert.ok(output.missing.some(m => m.includes('evidence')), 'missing should include evidence (empty)');
  });

  test('backward compat mode does NOT apply when lifecycle_state is present', () => {
    const signalPath = path.join(tmpDir, 'triaged-critical-no-evidence.md');
    fs.writeFileSync(signalPath, `---
id: sig-2026-02-11-kb-data-loss-migration-gap
type: signal
project: get-shit-done-reflect
tags: [knowledge-base, migration]
created: 2026-02-11T10:00:00Z
severity: critical
signal_type: deviation
lifecycle_state: triaged
phase: 25
polarity: negative
source: executor
---

# Triaged critical signal still needs evidence
`);

    const result = runGsdTools(`frontmatter validate ${signalPath} --schema signal`, tmpDir);
    assert.ok(result.success, `Command failed: ${result.error}`);
    const output = JSON.parse(result.output);
    assert.strictEqual(output.valid, false, 'critical signal with lifecycle_state but no evidence should fail even with old created date');
    assert.ok(output.missing.includes('evidence'), 'missing should include evidence');
  });

  test('warnings for missing recommended fields', () => {
    const signalPath = path.join(tmpDir, 'minimal-valid.md');
    fs.writeFileSync(signalPath, `---
id: sig-2026-02-28-minimal
type: signal
project: test-project
tags: [minimal]
created: 2026-02-28T10:00:00Z
severity: minor
signal_type: deviation
---

# Minimal valid signal
`);

    const result = runGsdTools(`frontmatter validate ${signalPath} --schema signal`, tmpDir);
    assert.ok(result.success, `Command failed: ${result.error}`);
    const output = JSON.parse(result.output);
    assert.strictEqual(output.valid, true, 'should be valid');
    assert.ok(output.warnings.length > 0, 'should have warnings');
    const warningStr = output.warnings.join(',');
    assert.ok(warningStr.includes('lifecycle_state'), 'should warn about missing lifecycle_state');
    assert.ok(warningStr.includes('confidence'), 'should warn about missing confidence');
  });
});
