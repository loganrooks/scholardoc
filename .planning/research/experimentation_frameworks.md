# Experimentation & Evaluation Frameworks for ML/NLP Pipelines

**Project:** ScholarDoc
**Researched:** 2026-01-28
**Overall confidence:** MEDIUM (mix of well-documented tools and novel agent patterns)

---

## 1. Experiment Tracking Frameworks

### Recommendation: Lightweight Custom + JSON Baselines (not MLflow/W&B)

ScholarDoc is not a model-training project. It is a deterministic extraction pipeline with heuristic parameters (thresholds, regex patterns, spellcheck selectors). The heavyweight ML experiment trackers solve the wrong problem here.

| Framework | Fit for ScholarDoc | Why |
|-----------|-------------------|-----|
| **MLflow** | POOR | Designed for model training runs, hyperparameter sweeps, model registry. Overkill for heuristic pipeline tuning. |
| **Weights & Biases** | POOR | Same reason. Cloud-dependent. Tracks loss curves, not extraction F1 across document corpora. |
| **DVC** | MODERATE | Data versioning is relevant (ground truth YAML files, PDF corpora). Pipeline DAGs could model extraction stages. But adds Git-external complexity. |
| **pytest-benchmark** | GOOD | Already in the Python ecosystem. Can track performance regression. Integrates with CI. |
| **Custom JSON baselines** | BEST | ScholarDoc already has `ground_truth/baselines/` and `evaluate.py --baseline --fail-on-regression`. This is the right pattern. Extend it, don't replace it. |

**Rationale:** The existing ground truth framework already implements the core evaluation loop (load GT, match elements, compute metrics, compare to baseline, fail on regression). The gap is not tooling -- it is process and structure around experimentation.

**Confidence:** HIGH -- based on direct inspection of the codebase and understanding of the problem domain.

### What to Borrow from MLflow/DVC

Even though full adoption is wrong, steal these ideas:

1. **Run IDs and metadata**: Each experiment run should produce a JSON artifact with a unique ID, timestamp, git SHA, parameters changed, and metrics.
2. **Parameter logging**: Record which parameters were varied (e.g., `spellcheck_threshold=0.7`, `ocr_engine=tesseract`).
3. **Artifact storage**: Save the full output alongside metrics so runs are reproducible.
4. **Comparison views**: A script that loads N run JSONs and produces a comparison table.

### Sources

- [MLflow vs DVC comparison](https://mljourney.com/model-versioning-strategies-dvc-vs-mlflow-vs-weights-biases/)
- [Best ML experiment tracking tools](https://neptune.ai/blog/best-ml-experiment-tracking-tools)
- [pytest-benchmark](https://github.com/ionelmc/pytest-benchmark)

---

## 2. Hypothesis-Experiment-Evaluation-Decision Workflow

### The Scientific Loop for Extraction Pipelines

The pattern that fits ScholarDoc:

```
OBSERVE  -->  HYPOTHESIZE  -->  EXPERIMENT  -->  EVALUATE  -->  DECIDE
   |              |                |               |             |
   |  "Footnotes  | "Block-based   | Run pipeline  | F1 improved | Write ADR-004
   |   missed on  |  filtering     | against GT    | from 0.72   | adopting
   |   page 47"   |  will catch    | corpus with   | to 0.85"    | block-based
   |              |  inline notes" | new heuristic |             | filtering
```

### Structured Experiment Protocol

Each experiment should follow a standard template:

```yaml
experiment:
  id: "EXP-2026-001"
  hypothesis: "Using block-level bounding box overlap > 0.3 to detect footnote regions will improve footnote recall without degrading precision."
  baseline: "baselines/current.json"
  parameter_changes:
    footnote_detection.overlap_threshold: 0.3  # was 0.5
  corpus: "ground_truth/documents/*.yaml"
  success_criteria:
    footnote_recall: ">= 0.85"
    footnote_precision: ">= 0.80"
    overall_f1: ">= baseline"

results:
  metrics: "experiments/EXP-2026-001/metrics.json"
  status: "PASS | FAIL | INCONCLUSIVE"
  decision: "ADOPT | REJECT | NEEDS_MORE_DATA"
  adr: "docs/adr/ADR-004.md"  # if adopted
```

### Decision Framework

| Result | Action |
|--------|--------|
| Metrics improve, no regressions | Write ADR, merge to main |
| Metrics improve but regression in one area | Document tradeoff, decide if acceptable |
| Metrics unchanged | Reject hypothesis, document learning |
| Metrics worsen | Reject, investigate why hypothesis was wrong |
| Inconclusive (small corpus, noisy results) | Flag for more GT annotation, re-run later |

**Confidence:** MEDIUM -- synthesized from ML experimentation best practices and scientific agent literature. The specific YAML format is a recommendation, not an established standard.

### Sources

- [AI Scientist-v2: tree-based experimentation](https://pub.sakana.ai/ai-scientist-v2/paper/paper.pdf)
- [R&D-Agent framework](https://openreview.net/pdf?id=APjCXYORXO)
- [Agent Laboratory](https://agentlaboratory.github.io/)

---

## 3. Automated Regression Testing Against Ground Truth

### Current State (ScholarDoc already has most of this)

The existing `ground_truth/` framework provides:
- Schema-validated YAML ground truth files
- Element matching (normalize, match, compute metrics)
- Baseline comparison with `--fail-on-regression`
- CLI evaluation tool

### What is Missing

1. **CI integration**: No evidence of automated regression runs on every commit.
2. **Stratified evaluation**: No per-category breakdown (footnotes vs headings vs body text) tracked over time.
3. **Historical tracking**: Baselines are point-in-time snapshots, not a time series.
4. **Corpus coverage metrics**: No tracking of "how much of the corpus is annotated" or "which document types are under-represented."

### Recommended Additions

#### A. CI Regression Gate

```bash
# In CI pipeline (GitHub Actions or similar)
uv run python -m ground_truth.scripts.evaluate \
    --ground-truth ground_truth/documents/*.yaml \
    --baseline ground_truth/baselines/current.json \
    --fail-on-regression \
    --output ground_truth/baselines/ci-run-$(git rev-parse --short HEAD).json
```

#### B. Stratified Metrics Dashboard

Track per-element-type metrics over time:

```
Run     | Date       | Git SHA  | Footnote F1 | Heading F1 | Body F1 | Overall F1
--------|------------|----------|-------------|------------|---------|----------
EXP-001 | 2026-01-15 | abc1234  | 0.72        | 0.91       | 0.88    | 0.84
EXP-002 | 2026-01-20 | def5678  | 0.85        | 0.91       | 0.87    | 0.87
```

#### C. Corpus Coverage Tracking

```yaml
corpus_coverage:
  total_pages_annotated: 47
  total_pages_available: 2300
  coverage_by_type:
    footnotes: 32 pages
    headings: 47 pages
    greek_text: 8 pages
    apparatus_criticus: 3 pages
  gaps:
    - "No annotated examples of multi-column layouts"
    - "Only 3 pages with critical apparatus"
```

#### D. Synthetic Ground Truth (Needle Insertion)

For areas where manual annotation is expensive, consider inserting synthetic "needles" -- known text fragments placed in known positions -- to test extraction accuracy without full annotation. This is particularly useful for regression testing OCR quality.

**Confidence:** HIGH for the CI integration and stratified metrics (well-established patterns). MEDIUM for needle insertion (newer technique, less proven for document extraction).

### Sources

- [Ground truth curation best practices (AWS)](https://aws.amazon.com/blogs/machine-learning/ground-truth-curation-and-metric-interpretation-best-practices-for-evaluating-generative-ai-question-answering-using-fmeval/)
- [Iterative ground truth refinement (PMC)](https://pmc.ncbi.nlm.nih.gov/articles/PMC5543376/)
- [RAG evaluation in CI/CD](https://www.confident-ai.com/blog/how-to-evaluate-rag-applications-in-ci-cd-pipelines-with-deepeval)
- [pytest-benchmark CI integration](https://bencher.dev/learn/track-in-ci/python/pytest-benchmark/)

---

## 4. Claude Code Agent Protocols for Systematic Experimentation

### The Core Insight

Claude Code agents can follow the scientific loop if given:
1. A structured protocol (what steps to follow)
2. Standardized inputs (experiment spec YAML)
3. Executable evaluation (CLI tools that return machine-readable output)
4. Decision criteria (thresholds for pass/fail)

### Proposed Agent Architecture

```
                    +-----------------------+
                    |  Experiment Orchestrator|
                    |  (human or /gsd command)|
                    +-----------+-----------+
                                |
                    +-----------v-----------+
                    |  Hypothesis Agent      |
                    |  - Reads current metrics|
                    |  - Identifies weak areas |
                    |  - Proposes experiment  |
                    +-----------+-----------+
                                |
                    +-----------v-----------+
                    |  Executor Agent        |
                    |  - Implements change    |
                    |  - Runs evaluation CLI  |
                    |  - Captures metrics JSON|
                    +-----------+-----------+
                                |
                    +-----------v-----------+
                    |  Evaluator Agent       |
                    |  - Compares to baseline |
                    |  - Checks success criteria|
                    |  - Recommends decision  |
                    +-----------+-----------+
                                |
                    +-----------v-----------+
                    |  Decision Agent        |
                    |  - Writes ADR if adopted|
                    |  - Updates baseline     |
                    |  - Logs experiment      |
                    +-----------------------+
```

### Agent Protocol Specification

Each agent needs a Claude Code agent markdown file (`.claude/agents/`) with:

#### Hypothesis Agent (`gsd-hypothesis-agent.md`)
- **Input**: Current baseline metrics JSON, corpus coverage report, list of known issues
- **Output**: Experiment spec YAML (hypothesis, parameter changes, success criteria)
- **Tools**: Read (metrics files), Grep (codebase for current parameter values), WebSearch (for techniques)
- **Key constraint**: Must propose ONE testable change. No multi-variable experiments.

#### Executor Agent (`gsd-experiment-executor.md`)
- **Input**: Experiment spec YAML
- **Output**: Metrics JSON, diff of code changes
- **Tools**: Write/Edit (implement change), Bash (run evaluation CLI)
- **Key constraint**: Must create a git branch per experiment. Must not modify baseline.

#### Evaluator Agent (`gsd-experiment-evaluator.md`)
- **Input**: Experiment metrics JSON, baseline JSON, success criteria from spec
- **Output**: Evaluation report (PASS/FAIL/INCONCLUSIVE with evidence)
- **Tools**: Read (JSON files), Bash (diff/comparison scripts)
- **Key constraint**: Must check ALL success criteria, not just overall F1. Must flag regressions in any category.

### Standardized I/O Contract

```
experiments/
  EXP-2026-001/
    spec.yaml          # Input: what to test
    branch.txt         # Git branch name
    diff.patch          # Code changes made
    metrics.json        # Raw evaluation output
    evaluation.md       # Agent's analysis
    decision.md         # ADOPT/REJECT + rationale
```

### Practical Considerations

1. **Single-variable experiments**: Agents must change ONE thing at a time. Multi-variable changes make it impossible to attribute improvements.
2. **Deterministic evaluation**: The evaluation CLI must produce identical results for identical inputs. No randomness in the pipeline.
3. **Human-in-the-loop**: The decision to merge should remain human-approved. Agents recommend, humans decide.
4. **Experiment log**: A running log (`experiments/LOG.md`) tracking all experiments, outcomes, and learnings.

**Confidence:** MEDIUM -- the agent architecture is novel and draws from emerging LLM-agent-for-science literature. The specific protocol is a recommendation based on how Claude Code agents work in practice. No established standard exists for this pattern.

### Sources

- [LLM-based scientific agents survey](https://arxiv.org/html/2503.24047v1)
- [Agent Laboratory](https://agentlaboratory.github.io/)
- [Nature: LLMs in the scientific method](https://www.nature.com/articles/s44387-025-00019-5)

---

## 5. Best Practices for Experiment Tracking and Evidence-Based Decisions

### Tracking Experiments

**Use a flat JSON log, not a database.** For a project of ScholarDoc's scale (tens of experiments, not thousands), a simple append-only JSON lines file is sufficient and version-controllable:

```jsonl
{"id":"EXP-001","date":"2026-01-15","git_sha":"abc1234","hypothesis":"block filtering","params":{"overlap_threshold":0.3},"metrics":{"footnote_f1":0.85,"overall_f1":0.87},"decision":"ADOPT","adr":"ADR-004"}
{"id":"EXP-002","date":"2026-01-20","git_sha":"def5678","hypothesis":"tesseract reocr","params":{"ocr_engine":"tesseract"},"metrics":{"footnote_f1":0.83,"overall_f1":0.86},"decision":"REJECT","reason":"regression in footnote detection"}
```

### Comparing Across Runs

A simple Python script that reads the JSONL file and produces:
1. A markdown comparison table (for human review)
2. A "best run per metric" summary
3. Trend lines showing metric evolution over time

### Evidence-Based ADR Pattern

When an experiment succeeds, the ADR should include:

```markdown
# ADR-004: Adopt Block-Based Footnote Filtering

## Status: Accepted

## Context
Footnote recall was 0.72 (EXP-001 baseline). Inline footnotes in philosophy texts were being missed.

## Experiment
EXP-002: Changed overlap_threshold from 0.5 to 0.3.
- Footnote recall: 0.72 -> 0.85 (+18%)
- Footnote precision: 0.82 -> 0.80 (-2%)
- Overall F1: 0.84 -> 0.87 (+4%)

## Decision
Accept. The 2% precision loss is acceptable given 18% recall gain.
Precision loss is concentrated in edge cases (single-line footnotes that overlap body text).

## Consequences
- Update default overlap_threshold to 0.3
- Add regression test for the 3 false-positive cases identified
- Monitor precision in future experiments
```

### Anti-Patterns to Avoid

| Anti-Pattern | Why Bad | Instead |
|--------------|---------|---------|
| Changing multiple parameters at once | Cannot attribute improvement | One variable per experiment |
| Only checking overall F1 | Hides category-level regressions | Check all element types |
| No baseline comparison | "It works" is not evidence | Always compare to stored baseline |
| Informal spike without metrics | Learnings are lost | Even quick tests should produce metrics JSON |
| Optimizing for the test set | Overfitting to annotated pages | Hold out some GT pages for validation |

### Test Set Management

Split ground truth into:
- **Development set** (70%): Used during experimentation
- **Validation set** (30%): Only used for final evaluation before merge

This prevents overfitting to the annotated corpus. When new GT pages are annotated, randomly assign them to dev or validation.

**Confidence:** HIGH for tracking patterns and anti-patterns (well-established). MEDIUM for the specific ADR format (reasonable extension of existing ADR practice).

---

## Summary and Recommendations

### Do NOT Adopt
- MLflow, W&B, or other heavyweight ML experiment trackers
- Complex database-backed experiment stores

### DO Adopt
1. **Extend the existing ground truth framework** with CI integration, stratified metrics, and historical tracking
2. **Standardize experiment specs** as YAML files with hypothesis, parameters, and success criteria
3. **Build Claude Code agent protocols** for hypothesis/execute/evaluate/decide workflow
4. **Use JSONL experiment log** for tracking all runs
5. **Split GT corpus** into dev/validation sets
6. **Require evidence in ADRs** -- no architectural decisions without metrics

### Implementation Priority
1. CI regression gate (lowest effort, highest immediate value)
2. Experiment spec YAML template and logging
3. Stratified metrics in evaluation output
4. Agent protocol markdown files
5. Comparison and trend scripts
6. Dev/validation corpus split
