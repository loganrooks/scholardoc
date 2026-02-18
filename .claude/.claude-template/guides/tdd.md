# Test-Driven Development Guide

## Purpose

Write tests before implementation to ensure code meets requirements, catches regressions, and produces cleaner designs.

## Principles

1. **Red-Green-Refactor** - Write failing test, make it pass, improve code
2. **Test behavior, not implementation** - Tests verify WHAT, not HOW
3. **One assertion per concept** - Each test validates one logical outcome
4. **Tests are documentation** - Test names describe expected behavior
5. **Fast feedback** - Keep test suite fast to encourage running often

## TDD Cycle

### Phase 1: RED (Write Failing Test)

```
1. Understand the requirement (one specific behavior)
2. Write test that verifies that behavior
3. Run test - confirm it FAILS (for the right reason)
4. If test passes immediately, requirement already satisfied or test is wrong
```

### Phase 2: GREEN (Make It Pass)

```
1. Write MINIMUM code to make test pass
2. Don't optimize, don't clean up yet
3. Hard-coded values are acceptable temporarily
4. Run test - confirm it PASSES
```

### Phase 3: REFACTOR (Improve Code)

```
1. Clean up implementation (remove duplication, improve names)
2. Clean up test if needed
3. Run tests - confirm they still PASS
4. Commit when all tests green
```

## Test Structure

### Given-When-Then Format

```python
def test_<behavior>_<scenario>():
    # Given: preconditions
    user = create_user(name="Alice")

    # When: action under test
    result = user.greet()

    # Then: expected outcome
    assert result == "Hello, Alice"
```

### Test File Organization

```
tests/
├── unit/           # Isolated component tests (fast)
├── integration/    # Component interaction tests
└── e2e/           # Full system tests (slow)
```

### Naming Convention

```
test_<function/method>_<scenario>_<expected_outcome>

Examples:
- test_parse_valid_json_returns_dict
- test_parse_invalid_json_raises_error
- test_parse_empty_string_returns_none
```

## Test Categories

### Happy Path
Normal, expected operation:
```
Given valid input
When operation performed
Then expected result returned
```

### Edge Cases
Boundary conditions:
```
- Empty input ([], "", None)
- Single item
- Maximum values
- Unicode/special characters
```

### Error Conditions
Failure handling:
```
- Invalid input types
- Missing required data
- External service failures
- Permission errors
```

## Quality Criteria

A good test suite:
- [ ] Tests run fast (unit tests < 1s each)
- [ ] Tests are isolated (no test depends on another)
- [ ] Tests are deterministic (same result every run)
- [ ] Test names describe the behavior being verified
- [ ] Coverage includes happy path, edges, and errors
- [ ] No implementation details leaked into tests

## Anti-patterns

- **Test after**: Writing tests after implementation (misses design benefits)
- **Testing implementation**: Asserting on internal state, not behavior
- **Fragile tests**: Tests that break when implementation changes
- **Slow tests**: Tests that make feedback loop painful
- **Shared state**: Tests that depend on other tests running first
- **Over-mocking**: Mocking everything loses integration confidence
- **Test names like "test1"**: Non-descriptive test naming

## Adaptation Notes

When generating for a project:
- Use project's test framework (pytest, jest, vitest, etc.)
- Follow project's existing test organization
- Match assertion style (assert vs expect vs should)
- Reference project's mocking patterns
- Include project-specific fixtures/utilities
