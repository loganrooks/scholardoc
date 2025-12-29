# Implementation Plan: Document Profiles (Milestone 1.5)

**Created:** 2025-12-24
**Status:** Ready for implementation
**Scope:** Complete structure extraction milestone 1.4/1.5

---

## Summary

Add `DocumentProfile` configuration system to enable document-type-specific structure extraction settings. This completes the remaining items from milestones 1.4 (Structure Extraction) and 1.5 (Document Profiles).

**Key insight:** Leverage existing `estimate_document_type()` function (100% accuracy on books) instead of building new indicator system.

---

## Current State Analysis

### Already Implemented ✅
- `ToCParserSource` - Full ToC detection and parsing
- `NoOverlapValidator` - Sibling overlap detection
- `HierarchyValidator` - Level skip detection
- `CascadingExtractor` - Orchestrates cascade (outline → heading → ToC enrichment)
- `estimate_document_type()` - Returns "book", "article", "essay", "report", "generic"
- 35 passing extractor tests

### Missing ❌
- `DocumentProfile` dataclass
- Profile constants (BOOK_PROFILE, ARTICLE_PROFILE, etc.)
- `get_profile()` function
- Profile integration with CascadingExtractor
- Profile-based tests

---

## Design Decisions

### D1: Extend CascadingExtractor, Don't Replace
- Add optional `profile` parameter
- Keep existing API backward-compatible
- Add `for_profile()` and `for_document()` class methods

### D2: Simple Profile Configuration
```python
@dataclass
class DocumentProfile:
    name: str  # "book", "article", "essay", "report", "generic"
    description: str
    use_outline: bool = True
    use_heading_detection: bool = True
    use_toc_enrichment: bool = True
    min_confidence: float = 0.5
    title_similarity_threshold: float = 0.8
    validators: tuple[str, ...] = ("overlap", "hierarchy")
```

### D3: Leverage Existing Detection
Use `estimate_document_type()` for profile selection - already validated at 100% on books.

---

## Profile Configurations

| Profile | Outline | Heading | ToC | Confidence | Validators |
|---------|---------|---------|-----|------------|------------|
| **book** | ✅ | ✅ | ✅ | 0.5 | overlap, hierarchy, title |
| **article** | ✅ | ✅ | ❌ | 0.4 | overlap |
| **essay** | ✅ | ✅ | ❌ | 0.4 | overlap, min_content |
| **report** | ✅ | ✅ | ✅ | 0.5 | overlap, hierarchy |
| **generic** | ✅ | ✅ | ❌ | 0.5 | overlap |

---

## Implementation Tasks

### Phase 1: Core Profile System
1. Create `scholardoc/extractors/profiles.py`
   - DocumentProfile dataclass
   - 5 profile constants
   - get_profile() function
   - PROFILES dict

2. Add unit tests `tests/unit/test_profiles.py`
   - Profile creation
   - get_profile() for each document type
   - Profile attribute verification

### Phase 2: Extractor Integration
3. Modify `scholardoc/extractors/cascading.py`
   - Add `profile` parameter to __init__
   - Add `for_profile()` classmethod
   - Add `for_document()` classmethod
   - Modify extract() to use profile when set
   - Add `profile_used` to StructureResult

4. Add extractor profile tests
   - Test backward compatibility (no profile)
   - Test for_profile() creates correct config
   - Test for_document() auto-detects

### Phase 3: Finalization
5. Update exports in `__init__.py`
6. Add integration test with real PDFs
7. Update ROADMAP.md to mark complete

---

## Files Affected

| File | Action | Lines |
|------|--------|-------|
| `scholardoc/extractors/profiles.py` | CREATE | ~100 |
| `scholardoc/extractors/cascading.py` | MODIFY | ~50 |
| `scholardoc/extractors/__init__.py` | MODIFY | ~10 |
| `tests/unit/test_profiles.py` | CREATE | ~80 |
| `tests/unit/test_extractors.py` | MODIFY | ~30 |
| `ROADMAP.md` | MODIFY | ~10 |

**Total: ~280 lines**

---

## Success Criteria

1. All 257 existing tests pass (no regressions)
2. DocumentProfile dataclass with 5 standard profiles
3. get_profile() returns appropriate profile for document type
4. CascadingExtractor.for_document() auto-detects and configures
5. StructureResult.profile_used tracks which profile was applied
6. 10+ new unit tests for profiles
7. Integration test verifies profile-based extraction
8. ROADMAP.md milestone 1.5 marked complete

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Breaking existing API | All new params optional, existing tests unchanged |
| Profile detection accuracy | Reuse validated estimate_document_type() |
| Over-engineering | Keep profiles as configuration, not behavior |
| Naming confusion | Keep CascadingExtractor name (accurate) |

---

## Out of Scope

- FusionStrategy (invalidated by Phase 0.5 findings)
- Complex indicator classes (use existing estimate_document_type)
- Profile persistence/serialization
- User-defined profiles (future consideration)
