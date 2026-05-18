# Deliberation: {TITLE}

<!--
Deliberation template grounded in:
- Dewey's inquiry cycle (situation → problematization → hypothesis → test → warranted assertion)
- Toulmin's argument structure (claim, grounds, warrant, rebuttal)
- Lakatos's progressive vs degenerating programme shifts
- Peirce's fallibilism (no conclusion is permanently settled)

Lifecycle: open → concluded → adopted → evaluated → superseded
-->

**Date:** {YYYY-MM-DD}
**Status:** Open
**Trigger:** {What prompted this — conversation observation, user question, signal IDs, phase outcomes, intuition, post-execution reflection}
**Affects:** {Phases, requirements, or milestones this deliberation may influence}
**Related:**
- {Links to signals, prior deliberations, philosophy files, requirements}

## Situation

{What is happening that warrants deliberation? This is Dewey's "indeterminate situation" made explicit. Ground in whatever evidence is available — this may be formal (signal IDs, KB data, codebase state) or informal (conversation observations, user intuitions, "something feels off"). Both are valid starting points. If the trigger was informal, include the investigation that verified or clarified the observation.}

### Evidence Base

<!--
Corroborated? column tracks whether claims survived falsification attempts (Step 2.5).
Per falsificationism: corroboration is provisional ("survived our best attempt to falsify"),
not verification (which implies certainty no finite number of checks can establish).
See philosophy: falsificationism/corroboration-not-confirmation.

Signal ID column tracks whether evidence has been formalized as a KB signal.
- Formal signal: use the sig-YYYY-MM-DD-slug ID
- Created during deliberation: signal with source: deliberation-trigger
- Not formalized: "informal" — the evidence exists only in this document
Formalizing evidence as signals makes it traceable, detectable for recurrence,
and referenceable by the remediation pipeline.
-->

| Source | What it shows | Corroborated? | Signal ID |
|--------|--------------|---------------|-----------|
| {KB query / codebase check / conversation observation} | {what it tells us} | {Yes (how) / Falsified / Untested} | {sig-ID or "informal"} |

## Framing

{What question are we actually asking? Restate the problem in terms that make the design space visible. Often the first framing is wrong — the real question is underneath.}

**Core question:** {One sentence}

**Adjacent questions:**
- {Related but distinct questions that may surface during deliberation}

## Analysis

{Explore the design space. For each serious option, use Toulmin structure.}

### Option A: {Name}

- **Claim:** {What we should do}
- **Grounds:** {Evidence supporting this}
- **Warrant:** {Why these facts support this conclusion — the inferential bridge}
- **Rebuttal:** {Conditions under which this option fails or is wrong}
- **Qualifier:** {Degree of confidence — certainly / probably / presumably}

### Option B: {Name}

- **Claim:** {What we should do}
- **Grounds:** {Evidence supporting this}
- **Warrant:** {Why these facts support this conclusion}
- **Rebuttal:** {Conditions under which this option fails or is wrong}
- **Qualifier:** {Degree of confidence}

## Tensions

{What contradictions or trade-offs does this deliberation surface? Which values are in conflict? Where does solving one problem create another?}

## Recommendation

{When status moves to `concluded`: the recommended option with rationale. Until then, this section captures the current leaning and open questions blocking conclusion.}

**Current leaning:** {Option X, because...}

**Open questions blocking conclusion:**
1. {Question that must be answered before concluding}

## Predictions

<!--
Predictions make the deliberation falsifiable (Lakatos). If adopted, what should we
observe? If we don't observe it, the deliberation's reasoning was flawed.
Record predictions BEFORE implementation so they can't be retrofitted.
-->

**If adopted, we predict:**

| ID | Prediction | Observable by | Falsified if |
|----|-----------|---------------|-------------|
| P1 | {What should happen} | {When/how we'd check} | {What would prove this wrong} |

## Decision Record

<!--
Filled when status moves to `concluded` or `adopted`.
Links the deliberation to the intervention that implements it.
-->

**Decision:** {What was decided}
**Decided:** {YYYY-MM-DD}
**Implemented via:** {Phase/plan IDs, quick task numbers, or "not yet implemented"}
**Signals addressed:** {Signal IDs this decision responds to, if any}

## Evaluation

<!--
Filled when status moves to `evaluated`.
Compare predictions against actual outcomes. Explain deviations.
This section is what makes deliberation a learning mechanism, not just a decision log.
-->

**Evaluated:** {YYYY-MM-DD}
**Evaluation method:** {How outcomes were assessed — signal recurrence check, verification, manual review}

| Prediction | Outcome | Match? | Explanation |
|-----------|---------|--------|-------------|
| P1: {prediction} | {what actually happened} | {yes/partial/no} | {why it matched or didn't} |

**Was this progressive or degenerating?** (Lakatos)
{Did the intervention predict novel outcomes that were confirmed? Or did it merely patch the immediate problem without advancing understanding?}

**Lessons for future deliberations:**
{What did this deliberation teach us about how to deliberate? Meta-learning.}

## Supersession

<!--
Filled when status moves to `superseded`.
A deliberation is superseded when better thinking replaces it.
-->

**Superseded by:** {Link to replacement deliberation}
**Reason:** {Why the new thinking is better — not just different}
