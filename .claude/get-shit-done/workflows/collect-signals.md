<purpose>
Orchestrate multi-sensor signal collection for a completed phase. Discovers sensor agents dynamically from the file system, spawns enabled sensors in parallel, collects their structured JSON output, and passes it to the signal synthesizer for quality-gated KB persistence.

<!-- Architecture notes:
  - SENSOR CONTRACT: Defines the interface between the orchestrator and sensor agents.
    - Input: Sensor receives phase number, phase directory path, project name, model profile
    - Output: JSON wrapped in ## SENSOR OUTPUT / ## END SENSOR OUTPUT delimiters
      with structure { sensor: string, phase: number, signals: array }
    - Error handling: On failure, return empty signals array -- never crash or return non-JSON
    - Timeout: Declared via `timeout_seconds` frontmatter field (default 45s); orchestrator
      enforces; on timeout, treated as empty array with inline warning
    - Config: `config_schema` frontmatter field (optional, null for current sensors;
      Phase 39 CI sensor expected to be first sensor that actually declares config knobs)
    - Blind spots: `<blind_spots>` section in agent spec body (prose documentation,
      not structured data -- makes theory-ladenness visible)

  - AUTO-DISCOVERY: Sensors are discovered by scanning for gsd-*-sensor.md files in the
    agents directory. Adding a new sensor is a single-file operation: create
    agents/gsd-{name}-sensor.md conforming to the contract above.

  - Sensors return JSON to orchestrator -- they do NOT write to KB (single-writer principle)
  - Sensor model selection: auto = derive from model_profile; explicit = use specified model
  - The orchestrator passes file PATHS to sensors, not file CONTENTS (prevents context bloat)
  - JSON extraction uses ## SENSOR OUTPUT / ## END SENSOR OUTPUT delimiters with fallback to fenced code block search
  - This pattern differs from map-codebase: mappers write files and return confirmations, sensors return data (JSON) to the orchestrator. The delimiter protocol ensures reliable data transfer across Task() boundaries.
-->
</purpose>

<core_principle>
Signal collection is a retrospective pass -- it reads execution artifacts (PLANs, SUMMARYs, VERIFICATION) without modifying them. The workflow validates prerequisites, discovers available sensors from the file system, reads sensor configuration, spawns enabled sensors in parallel via Task(), collects their JSON output with timeout enforcement, tracks per-sensor stats, and delegates synthesis to the signal synthesizer agent.
</core_principle>

<required_reading>
Read STATE.md before any operation to load project context.
Read config.json for model_profile and commit_docs settings.
</required_reading>

<process>

<step name="validate_input">
Receive phase number as argument. Validate and locate the phase directory:

```bash
PHASE_ARG="$1"
PADDED_PHASE=$(printf "%02d" ${PHASE_ARG} 2>/dev/null || echo "${PHASE_ARG}")
PHASE_DIR=$(ls -d .planning/phases/${PADDED_PHASE}-* .planning/phases/${PHASE_ARG}-* 2>/dev/null | head -1)

if [ -z "$PHASE_DIR" ]; then
  echo "ERROR: No phase directory found matching phase '${PHASE_ARG}'"
  echo "Check .planning/phases/ for available phases."
  exit 1
fi

echo "Phase directory: $PHASE_DIR"
```

Error if no matching directory exists.
</step>

<step name="locate_artifacts">
Find all execution artifacts in the phase directory:

```bash
# Find all PLAN.md and SUMMARY.md files
PLANS=$(ls -1 "$PHASE_DIR"/*-PLAN.md 2>/dev/null)
SUMMARIES=$(ls -1 "$PHASE_DIR"/*-SUMMARY.md 2>/dev/null)
VERIFICATION=$(ls -1 "$PHASE_DIR"/*-VERIFICATION.md 2>/dev/null)

PLAN_COUNT=$(echo "$PLANS" | grep -c '.' 2>/dev/null || echo 0)
SUMMARY_COUNT=$(echo "$SUMMARIES" | grep -c '.' 2>/dev/null || echo 0)

echo "Plans found: $PLAN_COUNT"
echo "Summaries found: $SUMMARY_COUNT"
echo "Verification: ${VERIFICATION:-none}"
```

Count how many plans have summaries (completed plans only).
</step>

<step name="check_prerequisites">
At least one SUMMARY.md must exist -- signals can only be detected from completed plans:

```bash
if [ "$SUMMARY_COUNT" -eq 0 ]; then
  echo "No completed plans to analyze."
  echo "Run /gsd:execute-phase $PHASE_ARG first to execute plans, then collect signals."
  exit 0
fi
```

Report: "Analyzing {N} completed plans for phase {X}"
</step>

<step name="load_config">
Read planning configuration:

```bash
MODEL_PROFILE=$(cat .planning/config.json 2>/dev/null | grep -o '"model_profile"[[:space:]]*:[[:space:]]*"[^"]*"' | grep -o '"[^"]*"$' | tr -d '"' || echo "balanced")
COMMIT_PLANNING_DOCS=$(cat .planning/config.json 2>/dev/null | grep -o '"commit_docs"[[:space:]]*:[[:space:]]*[^,}]*' | grep -o 'true\|false' || echo "true")
git check-ignore -q .planning 2>/dev/null && COMMIT_PLANNING_DOCS=false

PROJECT_NAME=$(basename "$(pwd)" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]/-/g' | sed 's/--*/-/g' | sed 's/^-//;s/-$//')
```

Store `MODEL_PROFILE`, `COMMIT_PLANNING_DOCS`, and `PROJECT_NAME` for use in agent spawn.
</step>

<step name="discover_sensors">
Scan the agents directory for sensor agent specs matching the `gsd-*-sensor.md` naming convention. This is the auto-discovery mechanism that eliminates hardcoded sensor spawning.

```bash
# Discover all sensor agent specs from the file system
SENSOR_FILES=$(ls -1 ./.claude/agents/gsd-*-sensor.md 2>/dev/null)

if [ -z "$SENSOR_FILES" ]; then
  echo "WARNING: No sensor agent specs found in ./.claude/agents/"
  echo "Expected files matching pattern: gsd-*-sensor.md"
  exit 1
fi

DISCOVERED_SENSORS=""
for SENSOR_FILE in $SENSOR_FILES; do
  # Extract sensor name from filename: gsd-{name}-sensor.md -> {name}
  SENSOR_NAME=$(basename "$SENSOR_FILE" | sed 's/^gsd-//' | sed 's/-sensor\.md$//')

  # Parse frontmatter for contract fields
  # Extract timeout_seconds (default 45 if not declared)
  TIMEOUT=$(grep -m1 'timeout_seconds:' "$SENSOR_FILE" | grep -o '[0-9]*' || echo "45")
  [ -z "$TIMEOUT" ] && TIMEOUT=45

  # Extract config_schema presence (optional)
  HAS_CONFIG_SCHEMA=$(grep -c 'config_schema:' "$SENSOR_FILE" 2>/dev/null || echo "0")

  # Build discovered sensor entry: name|spec_path|timeout_seconds
  DISCOVERED_SENSORS="${DISCOVERED_SENSORS}${SENSOR_NAME}|${SENSOR_FILE}|${TIMEOUT}\n"
done

# Report discovery results
SENSOR_COUNT=$(echo -e "$DISCOVERED_SENSORS" | grep -c '|' 2>/dev/null || echo 0)
SENSOR_NAMES=$(echo -e "$DISCOVERED_SENSORS" | grep '|' | cut -d'|' -f1 | tr '\n' ', ' | sed 's/,$//')
echo "Discovered ${SENSOR_COUNT} sensors: ${SENSOR_NAMES}"
```

For each discovered sensor, the entry contains: name, spec_path, timeout_seconds.
If frontmatter parsing fails for a sensor, log a warning, skip that sensor, and continue with the rest.
</step>

<step name="load_sensor_config">
For each discovered sensor, check config for enable/disable overrides. Sensors not listed in config default to enabled -- this is the "drop a file" design: adding a new sensor agent spec automatically makes it active without config changes.

```bash
# Read sensor config overrides from project config
SENSOR_CONFIG=$(cat .planning/config.json 2>/dev/null | node -e "
  const c = JSON.parse(require('fs').readFileSync('/dev/stdin','utf8'));
  const sc = c.signal_collection || {};
  const sensors = sc.sensors || {};
  console.log(JSON.stringify(sensors));
" 2>/dev/null || echo '{}')

SYNTHESIZER_MODEL=$(cat .planning/config.json 2>/dev/null | node -e "
  const c = JSON.parse(require('fs').readFileSync('/dev/stdin','utf8'));
  const sc = c.signal_collection || {};
  console.log(sc.synthesizer_model || 'auto');
" 2>/dev/null || echo 'auto')
```

For each discovered sensor, cross-reference with config:
- If `config.signal_collection.sensors[name]` exists: use its `enabled` and `model` values
- If no config entry exists for a sensor: default to `{enabled: true, model: "auto"}`
- To disable a sensor, user adds explicit `"sensor_name": {"enabled": false}` to config

Build `ENABLED_SENSORS` and `DISABLED_SENSORS` lists from cross-referencing discovery with config.

```bash
# Cross-reference discovered sensors with config
ENABLED_SENSORS=""
DISABLED_SENSORS=""

for ENTRY in $(echo -e "$DISCOVERED_SENSORS" | grep '|'); do
  NAME=$(echo "$ENTRY" | cut -d'|' -f1)
  SPEC_PATH=$(echo "$ENTRY" | cut -d'|' -f2)
  TIMEOUT=$(echo "$ENTRY" | cut -d'|' -f3)

  # Check if config has an entry for this sensor
  SENSOR_ENABLED=$(echo "$SENSOR_CONFIG" | node -e "
    const cfg = JSON.parse(require('fs').readFileSync('/dev/stdin','utf8'));
    const entry = cfg['${NAME}'];
    // No config entry = default enabled; explicit enabled field controls override
    console.log(entry && entry.enabled === false ? 'false' : 'true');
  " 2>/dev/null || echo 'true')

  SENSOR_MODEL=$(echo "$SENSOR_CONFIG" | node -e "
    const cfg = JSON.parse(require('fs').readFileSync('/dev/stdin','utf8'));
    const entry = cfg['${NAME}'];
    console.log((entry && entry.model) || 'auto');
  " 2>/dev/null || echo 'auto')

  if [ "$SENSOR_ENABLED" = "true" ]; then
    ENABLED_SENSORS="${ENABLED_SENSORS}${NAME}|${SPEC_PATH}|${TIMEOUT}|${SENSOR_MODEL}\n"
  else
    DISABLED_SENSORS="${DISABLED_SENSORS}${NAME}\n"
  fi
done

ENABLED_NAMES=$(echo -e "$ENABLED_SENSORS" | grep '|' | cut -d'|' -f1 | tr '\n' ', ' | sed 's/,$//')
DISABLED_NAMES=$(echo -e "$DISABLED_SENSORS" | grep -v '^$' | tr '\n' ', ' | sed 's/,$//')
echo "Enabled: ${ENABLED_NAMES:-none}. Disabled: ${DISABLED_NAMES:-none}."
```

Determine model for each sensor based on the `model` field:
- `"auto"`: Use the orchestrator's `MODEL_PROFILE` to select (quality = opus, balanced = sonnet)
- Specific model string: Use that model directly

Resolve sensor models:

```bash
# Resolve "auto" to concrete model based on MODEL_PROFILE
resolve_model() {
  local model_setting="$1"
  if [ "$model_setting" = "auto" ]; then
    if [ "$MODEL_PROFILE" = "quality" ]; then
      echo "opus"
    else
      echo "sonnet"
    fi
  else
    echo "$model_setting"
  fi
}
```
</step>

<step name="spawn_sensors">
For each ENABLED sensor, spawn a Task() with `run_in_background=true`. This is a dynamic loop -- no sensor names are hardcoded in the spawning logic.

```
# Record spawn timestamps for timeout tracking
SPAWN_TIME=$(date +%s)

for ENTRY in ENABLED_SENSORS:
  NAME = ENTRY.name
  SPEC_PATH = ENTRY.spec_path
  TIMEOUT = ENTRY.timeout_seconds
  MODEL = resolve_model(ENTRY.model)

  # subagent_type is dynamically constructed: "gsd-" + NAME + "-sensor"
  Task(
    subagent_type=SENSOR_AGENT_TYPE,
    model=RESOLVED_MODEL,
    run_in_background=true,
    description="Collect signals for phase {PADDED_PHASE}",
    prompt="Analyze phase {PADDED_PHASE} execution artifacts.
      Phase directory: {PHASE_DIR}
      Project name: {PROJECT_NAME}
      Model profile: {MODEL_PROFILE}

      Read the relevant files from the phase directory.
      Apply signal-detection.md rules.
      Return your results as a JSON object with format:
      { sensor: '{NAME}', phase: N, signals: [...] }
      Each signal needs: summary, signal_type, signal_category, severity, tags, evidence, confidence, confidence_basis, context."
  )
```

Note: Pass FILE PATHS and let the sensor read them itself. Do NOT read artifact contents into variables and pass them in the prompt. This prevents orchestrator context bloat (sensors have Read/Bash/Glob/Grep tools).

Track spawned sensor names and spawn timestamps for output collection and timeout enforcement.
</step>

<step name="collect_sensor_outputs">
Wait for all background tasks to complete. For each sensor's response, extract JSON using the structured delimiter protocol. Enforce per-sensor timeouts and track execution stats.

1. Look for `## SENSOR OUTPUT` and `## END SENSOR OUTPUT` markers in the agent response
2. Extract the JSON block between these markers (specifically the ```json...``` fenced code block)
3. Parse the JSON into a structured object: `{ sensor: string, phase: number, signals: array }`
4. **Fallback:** If delimiters are not found, attempt to find a ```json...``` code block containing `"sensor"` as a fallback. Log a warning: "Sensor {name} response missing structured delimiters -- using fallback JSON extraction"
5. **Failure:** If no JSON can be extracted, log the failure: "Sensor {name} returned unparseable output -- skipping" and continue with other sensors

**Per-sensor timeout tracking:**
- Record spawn timestamp at spawn time
- When collecting output, compare elapsed time against the sensor's declared `timeout_seconds`
- If a sensor's output is not received within its timeout: treat as returning empty array
- Log inline warning: "WARNING: {name}-sensor timed out ({timeout}s), signals may be incomplete"

**Per-sensor stats tracking via Phase 37 mechanism:**
After each sensor output is collected (success or failure), track stats:

```bash
# On successful sensor output collection:
node ./.claude/get-shit-done/bin/gsd-tools.js automation track-event "sensor_{NAME}" fire

# On sensor failure (parse error, agent error):
node ./.claude/get-shit-done/bin/gsd-tools.js automation track-event "sensor_{NAME}" skip "parse-error"
# or
node ./.claude/get-shit-done/bin/gsd-tools.js automation track-event "sensor_{NAME}" skip "agent-error"

# On sensor timeout:
node ./.claude/get-shit-done/bin/gsd-tools.js automation track-event "sensor_{NAME}" skip "timeout"
```

Collect all successfully parsed sensor JSON arrays into a merged list: `MERGED_SENSOR_JSON`.

Track counts:
- `TOTAL_CANDIDATES`: Total signals across all sensors
- `SENSORS_COMPLETED`: Number of sensors that returned valid JSON
- `SENSORS_FAILED`: Number of sensors that failed or returned unparseable output
- `SENSORS_FALLBACK`: Number of sensors that required fallback extraction (missing delimiters)
- `SENSORS_TIMED_OUT`: Number of sensors that exceeded their declared timeout
</step>

<step name="enrich_signal_metadata">
New signals SHOULD include enrichment fields auto-populated from the runtime environment. These fields support future cross-project signal sharing by providing environment context.

**Enrichment fields for new signals:**

```yaml
source: local
environment:
  os: "$(uname -s | tr '[:upper:]' '[:lower:]')"
  node_version: "$(node --version 2>/dev/null || echo 'unknown')"
  config_profile: "$(node -e \"try{console.log(JSON.parse(require('fs').readFileSync('.planning/config.json','utf8')).model_profile||'unknown')}catch{console.log('unknown')}\" 2>/dev/null || echo 'unknown')"
```

- `source: local` indicates the signal was generated from the local project KB. Future cross-project signal sharing will use `source: external`.
- `environment` fields are auto-populated and help diagnose whether a signal is environment-specific or universal.
- Do NOT backfill existing signals with these fields -- only new signals carry enrichment metadata.

Note: The `source` enrichment field (`local`/`external`) is distinct from the existing signal schema `source` field (`auto`/`manual`) which tracks detection method. In signal frontmatter, use `origin: local` to avoid collision with the detection-method `source` field.
</step>

<step name="spawn_synthesizer">
Spawn the synthesizer as a foreground Task() (NOT background -- we need its report):

```
Task(
  subagent_type="gsd-signal-synthesizer",
  model="{synthesizer_model}",
  description="Synthesize signals for phase {PADDED_PHASE}",
  prompt="Synthesize and persist signals for phase {PADDED_PHASE}.
    Project name: {PROJECT_NAME}

    Raw signal candidates from sensors:
    {MERGED_SENSOR_JSON}

    Read the KB index (at .planning/knowledge/index.md or ~/.gsd/knowledge/index.md fallback) for dedup checking.
    Apply all quality gates: trace filter, cross-sensor dedup, KB dedup, rigor enforcement, per-phase cap.
    Write qualifying signals to the KB signals directory (.planning/knowledge/signals/{PROJECT_NAME}/ or ~/.gsd/knowledge/signals/{PROJECT_NAME}/ fallback).
    Rebuild index with: bash get-shit-done/bin/kb-rebuild-index.sh (or ~/.gsd/bin/kb-rebuild-index.sh fallback)
    Return your Synthesizer Report when complete."
)
```

The synthesizer model follows the `synthesizer_model` config field (default `"auto"`, resolved same as sensor models).
</step>

<step name="receive_report">
The signal synthesizer agent returns a structured Synthesizer Report containing:
- Total candidates received (from sensors)
- Signals filtered (trace, duplicate, failed rigor)
- Signals persisted (with IDs, types, severities)
- Signal files written (paths)
- Per-sensor breakdown
- Notes and observations

Parse the report for the results presentation step.
</step>

<step name="present_results">
Display user-friendly results using GSD UI patterns with per-sensor breakdowns:

```
GSD > SIGNAL COLLECTION COMPLETE

Phase {X}: {Name}
Plans analyzed: {N}
Sensors run: {enabled_list} ({disabled_list}: disabled)

### Per-Sensor Results
| Sensor | Candidates | Merged | Written |
|--------|------------|--------|---------|
| {name} | N | N | N |

### Synthesizer Summary
{synthesizer report content}
```

If zero signals detected:
```
No signals detected for phase {X}. Clean execution.
```

Include sensor health notes:
- If any sensors used fallback extraction: "Note: {N} sensor(s) used fallback JSON extraction"
- If any sensors failed: "Warning: {N} sensor(s) failed -- results may be incomplete"
- If any sensors timed out: "Warning: {N} sensor(s) timed out -- results may be incomplete"

Include standing caveat at end of collection output:
"Sensors: {enabled_list}. For sensor limitations, see agent specs or run `gsd sensors blind-spots`."
</step>

<step name="rebuild_index">
If signals were written, ensure the KB index is up to date (in case the synthesizer did not rebuild it):

```bash
if [ "$SIGNALS_WRITTEN" -gt 0 ]; then
  # KB path resolution -- project-local primary, user-global fallback
  if [ -d ".planning/knowledge" ]; then
    bash get-shit-done/bin/kb-rebuild-index.sh
  else
    bash ~/.gsd/bin/kb-rebuild-index.sh
  fi
fi
```
</step>

<step name="commit_signals">
If signals were written and `COMMIT_PLANNING_DOCS` is true, commit the new signal files:

```bash
if [ "$COMMIT_PLANNING_DOCS" = "true" ] && [ "$SIGNALS_WRITTEN" -gt 0 ]; then
  # Stage individual signal files
  # KB path resolution -- project-local primary, user-global fallback
  if [ -d ".planning/knowledge" ]; then KB_DIR=".planning/knowledge"; else KB_DIR="$HOME/.gsd/knowledge"; fi
  for signal_file in $(ls $KB_DIR/signals/${PROJECT_NAME}/*.md 2>/dev/null); do
    git add "$signal_file"
  done
  # Stage updated index
  git add $KB_DIR/index.md
  git commit -m "docs(signals): collect phase ${PADDED_PHASE} signals

- ${SIGNALS_WRITTEN} signals persisted
- Sensors: ${SENSORS_COMPLETED} completed, ${SENSORS_FAILED} failed
- Index rebuilt"
fi
```

Skip if `COMMIT_PLANNING_DOCS` is false or no signals were written.
</step>

</process>

<error_handling>
**No phase directory:** Report error with available phases and exit.
**No summaries:** Report "no completed plans" and exit cleanly (not an error).
**No sensors discovered:** Report error -- at least one sensor agent spec must exist.
**Single sensor failure:** Log the failure, track via track-event with skip reason, continue with remaining sensors. Only fail the whole workflow if ALL sensors fail.
**Single sensor timeout:** Log inline warning, track via track-event with "timeout" skip reason, treat as empty array, continue with remaining sensors.
**All sensors failed:** Report "all sensors failed" with error details. Suggest manual `/gsd:signal` for individual entries.
**Synthesizer failure:** Report what was attempted and suggest manual `/gsd:signal` for individual entries.
**KB directory missing:** Synthesizer creates it (mkdir -p) during signal write step.
**JSON extraction failure:** Use fallback extraction (fenced code block search). If fallback also fails, skip that sensor and continue.
**Frontmatter parse failure:** Log warning "Sensor {name} has malformed frontmatter -- skipping", continue with remaining sensors.
</error_handling>
