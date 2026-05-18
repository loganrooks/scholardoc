# Codebase Quality Audit — 2026-05-01

## Top-line Verdict

`scholargt/` is genuinely well-built: clean module decomposition (`base / spatial / page / document / semantic / labels / formatting / config / validation`), no internal coupling cycles, no scholardoc imports, 293 schema/config/validation tests all passing, and an explicitly version-pinned schema (`v2.0.0`). The package satisfies its "independent of any extractor" promise at the import level — `grep` for `scholardoc` in `scholargt/` returns zero hits. The recent Phase 1.1 taxonomy work landed solid IR design. `scholardoc/` is a different story: 32 unit tests fail because the test corpus PDFs were gitignored (Quick-3) but the test fixtures point at gitignored paths; two parallel OCR pipelines (`normalizers/` legacy + `ocr/` new) coexist with the legacy still wired up by default; `models.py` is a 1524-line god module mixing 27 dataclasses; and `tests/integration/test_ground_truth_regression.py:103` imports a `convert_pdf` symbol that does not exist (it would fail on first non-skipped invocation). ScholarGT is on track. ScholarDoc has bit-rotted in exactly the way one would expect of a "deferred" subsystem.

## Test Count Truth

`uv run pytest --collect-only -q` collects **694 tests** (not 312/320/349). Breakdown when run: scholargt 293 pass / 0 fail; integration 26 pass / 5 skip; unit 284 pass / 32 fail / 10 skip / 29 errors. The 32 unit failures and 29 collection errors are all the same root cause: missing `spikes/sample_pdfs/kant_critique_pages_64_65.pdf` (gitignored corpus). Effective passing: ~603. The "312" in `STATE.md:15` is the ScholarGT-only number from Phase 1.1 verification.

## Findings

### F1. ScholarDoc test suite is broken — 32 failures + 29 errors from missing fixtures (BLOCKING)

`tests/conftest.py` has no `SAMPLE_PDFS` fixture pointing at a real source, while `tests/unit/test_pdf_reader.py:30`, `tests/unit/test_extractors.py:38`, and `tests/unit/test_ocr_pipeline.py:360` all reference `spikes/sample_pdfs/kant_critique_pages_64_65.pdf` directly. That file is in a gitignored directory (per Quick-3 "organize uncommitted files"). The hardcoded paths bypass any fixture resolution. **Evidence:** `FileNotFoundError: PDF not found: /home/rookslog/.../spikes/sample_pdfs/kant_critique_pages_64_65.pdf` from running tests. **Intervention:** Phase 1.2 should land a small (1-2 page) Kant fixture PDF *committed* under `tests/fixtures/`, and rewrite the three offending test files to use a `kant_pdf` fixture from `conftest.py` instead of hardcoded paths. Until fixed, CI cannot trust the test signal at all.

### F2. `convert_pdf` import in regression test points at a non-existent symbol (IMPORTANT)

`tests/integration/test_ground_truth_regression.py:103` does `from scholardoc.convert import convert_pdf`. The `scholardoc/convert.py` exports `convert`, `convert_batch`, `detect_format`, `supported_formats` — there is no `convert_pdf`. The test currently passes only because the surrounding fixture skips when the YAML/PDF path doesn't exist. The moment a regression PDF lands, this fails. **Intervention:** rename to `convert` and pass via fixture, or add a `convert_pdf = convert` alias if the rename is undesired.

### F3. Two parallel OCR pipelines, legacy is still the default (IMPORTANT)

`scholardoc/normalizers/ocr_pipeline.py` (708 lines, "Legacy") and `scholardoc/ocr/pipeline.py` (317 lines, "new") both exist. `scholardoc/convert.py:38-39` imports both, and `convert.py:104` defaults to `LegacyOCRPipeline()` whenever `config.ocr.enabled=False` (which is the default per `config.py`). Per the Dec 2025 plan the new pipeline was supposed to be integrated, but the integration kept the legacy as the default fallback rather than retiring it. Effect: 2,472 lines of duplicate-purpose OCR code with two different APIs (`apply_line_breaks`/`detect_errors` vs `process_text` returning `PipelineResult`). **Intervention:** when ScholarDoc work resumes (Milestone 2+), delete `normalizers/ocr_pipeline.py` and the dead branch in `convert.py:103-105,207-235`. For now: leave a deprecation warning; the `Active (Deferred)` list in PROJECT.md should track this explicitly.

### F4. `scholardoc/models.py` is a 1524-line god module with 27 classes (IMPORTANT)

A single file holds 6 enums, the `Span` hierarchy (5 classes), reference annotations (4), content models (4), quality machinery (5), document metadata, RAG chunk, and `ScholarDocument` itself (the 200+ line aggregate root). Coupling is high: `ScholarDocument.to_markdown()` is implemented inside the dataclass. Compare to `scholargt/schema/` which decomposes the equivalent surface across 8 files of 84-384 lines each. **Evidence:** `wc -l scholardoc/models.py` = 1524; `grep -c "^class " scholardoc/models.py` = 27. **Intervention:** when ScholarDoc work resumes, split into `models/spans.py`, `models/annotations.py`, `models/quality.py`, `models/document.py`. Not urgent because the module is in maintenance mode, but flag in PROJECT.md.

### F5. `extra="allow"` is applied to 4 of 5 top-level Pydantic models (IMPORTANT)

`GTElement` (base), `PageGT`, `DocumentGT`, and `GTProfile` all set `model_config = ConfigDict(extra="allow")`. Region inherits it from `GTElement`. The justification ("forward compatibility" / "incremental annotation") is reasonable, but the cumulative effect is that *no* schema typo is ever caught at validation time — `Regoin(id=..., bbox=...)` works without complaint, `PageGT(page_indes=0, ...)` silently accepts the typo. The tests catch nothing of this kind. **Evidence:** `scholargt/schema/base.py:93`, `page.py:132`, `document.py:127`, `config/models.py:49`. **Intervention:** consider `extra="ignore"` for `GTProfile` (project configs rarely need forward-compat), and add a strict-mode validator path for CI that rebuilds the same models with `extra="forbid"` to surface unknown fields. The current design is too permissive even for an evolving schema.

### F6. Schema tests heavily favour instantiation over behaviour (NICE-TO-HAVE)

`tests/test_scholargt/test_semantic_models.py` has 61 tests, but the dominant pattern is "construct with field X, assert field X equals Y" (e.g., `test_create_note_endnote_style` at L176, `test_note_with_all_fields` at L188). The validation-behaviour tests live in `test_validation.py` (46 tests) and `test_page_models.py` reading_order check, but the cross-element validators (note→note_schema_id reference, citation→bib_entry_id reference at `validator.py:269-296`) are tested only at the document level, never with a malformed element directly. The discriminated-union deserialization (`semantic.py:365-384`) is asserted by passing element_type="note" rather than by feeding mixed-type JSON and checking the right Python class comes out. **Intervention:** add ~10 tests that exercise polymorphic JSON round-trips (`DocumentGT.model_validate(json_with_mixed_elements)` → assert types) and one test per cross-reference validator that fails when malformed.

### F7. Profile YAMLs duplicate the enum values as strings (NICE-TO-HAVE)

`scholargt/config/profiles/base.yaml` lists `text_block`, `note_area`, `page_header`, etc. as raw strings; the same values are defined in `scholargt/schema/labels.py:27-47` as `SpatialLabel` enum members. There is no validation that a profile YAML cannot contain an unknown spatial label — `GTProfile.spatial_labels: set[str]` with `extra="allow"` accepts anything. So `base.yaml` could ship with `text_blok` (typo) and CI would pass; only annotators using the profile would later see warnings. **Intervention:** add a `Field(validator=lambda x: x in {e.value for e in SpatialLabel} | {custom_set})` or a model_validator that checks against the enum unions, with a documented escape hatch for custom project labels.

### F8. `scholardoc/writers/__init__.py` is still a 1-line stub (IMPORTANT, deferred)

`scholardoc/writers/__init__.py` reads exactly: `"""writers module - see SPEC.md for design."""`. This was flagged Dec 2025 ("Empty Writers module"); it is still empty in May 2026. Currently `ScholarDocument.to_markdown()` lives inside `models.py` (god-module problem F4). The `SPEC.md` design and `PROJECT.md:43` ("Writers module (JSON canonical, Markdown presentation)") explicitly assume this gets factored out. **Intervention:** correctly tracked in PROJECT.md "Active (Deferred)". No code action this milestone.

### F9. `pyproject.toml` package config is correct, but `name="scholardoc"` is misleading (NICE-TO-HAVE)

`[tool.hatch.build.targets.wheel] packages = ["scholardoc", "scholargt"]` (line 100) correctly ships both top-level packages from a single project. However the project `name = "scholardoc"` (line 2) means importing both still says "I'm depending on scholardoc-the-distribution to get scholargt." If ScholarGT really is independent and serves multiple consumers (PROJECT.md:7), it should be its own distribution — either now (separate `pyproject.toml` files in each subdirectory) or via the `[tool.uv.workspace]` adoption that STATE.md decisions hint at. There is **no** `[tool.uv.workspace]` section currently. **Intervention:** Phase 1.2 ("Repo Governing Reset") should explicitly decide: dual-package single-distribution (current) vs. uv-workspace dual-distribution. Document the decision in an ADR; either is defensible, but leaving it implicit will hurt downstream consumers.

### F10. Stale top-level `ground_truth/` mixes legacy artifacts with active code (NICE-TO-HAVE)

`ground_truth/` (1.4MB+) holds (a) prior-art docs (SCHEMA.md, ANNOTATION_UI_DESIGN.md, etc. — useful), (b) gitignored corpora (per memory), and (c) `ground_truth/lib/` (1207 lines: matching, metrics, normalize, reports — actively imported by `tests/unit/ground_truth/test_*.py`). Tests pass against this code, so it isn't dead, but it is *not* under either `scholardoc/` or `scholargt/`. It looks like Era 1 evaluation infrastructure that should either move into `scholargt/evaluation/` or `scholardoc/evaluation/` once the seam is decided, or be gitignored as completely-historical-reference. Currently it lives in a third namespace. **Intervention:** Phase 1.2 should decide whether `ground_truth/lib/` belongs under scholargt (likely — it's exactly what scholargt's measurement story will need) or stays a separate evaluation toolkit.

## What's Actually Good

- **Clean module boundaries in `scholargt/`.** `base.py` → `spatial.py` / `labels.py` → `semantic.py` / `formatting.py` / `page.py` → `document.py` is a strict DAG. No circular imports, no upward references. The discriminated union in `semantic.py:365-384` is the right Pydantic pattern for polymorphic JSON.
- **Decomposition of citation modeling** into `CitationFormat` (appearance) + `ReferenceSystem` (coordinates) at `labels.py:108-143` is genuinely good design — it eliminates the v1 conflation that motivated Phase 1.1.
- **Per-element verification** via `GTElement.verifications: list[VerificationRecord]` (`base.py:96`) with `is_verified(threshold)` and `agreement_score()` is exactly the right primitive for the measurement story; it's at the base class so every annotatable element gets it for free.
- **Independence is real.** `grep -rn "scholardoc" scholargt/` and `grep -rn "scholargt" scholardoc/` both return zero hits. The two packages do not depend on each other at the import level. The seam where the future extractor protocol must connect (Phase 2) is wide open and unconstrained — no premature coupling.
- **Schema generation is one-shot, deterministic, and committed** (`scholargt/generated/schema.json`, 2695 lines via `models_json_schema`). IDE autocomplete and CI validation work today.
- **ScholarGT tests pass cleanly** (293/293, 6.3s). Hypothesis-style edge cases (empty regions, missing fields, duplicate IDs) are covered. Validation distinguishes errors from warnings consistently across `validator.py:38-52`.
- **TODO/FIXME hygiene is excellent**: only 2 TODOs in entire `scholardoc/` codebase (`convert.py:333`, `convert.py:441`), zero in `scholargt/`. No `XXX`/`HACK`/`FIXME` markers.
