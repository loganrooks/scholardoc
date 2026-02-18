# Refactoring Guide

## Purpose

Improve code structure without changing behavior. Make code easier to understand, modify, and extend.

## Principles

1. **Tests first** - Never refactor without test coverage
2. **Small steps** - Each change should be easily reversible
3. **One thing at a time** - Don't mix refactoring with features
4. **Behavior preservation** - Tests pass before AND after
5. **Clear motivation** - Know WHY before changing

## Refactoring Process

### Phase 1: PREPARE

```
1. Ensure adequate test coverage
2. Run tests - confirm all pass
3. Commit current state
4. Identify specific improvement goal
```

### Phase 2: EXECUTE

```
1. Make one small change
2. Run tests
3. If pass: commit
4. If fail: revert immediately
5. Repeat until goal achieved
```

### Phase 3: VERIFY

```
1. Full test suite passes
2. Code review the diff
3. Verify behavior unchanged
4. Document any API changes
```

## Common Refactorings

### Extract Function
When: Code block does one coherent thing
```python
# Before
def process():
    # ... 20 lines calculating total ...
    # ... 20 lines formatting output ...

# After
def process():
    total = calculate_total(items)
    return format_output(total)
```

### Rename
When: Name doesn't reflect purpose
```python
# Before
def proc(d): ...

# After
def process_transaction(data): ...
```

### Extract Variable
When: Complex expression needs explanation
```python
# Before
if user.age >= 18 and user.verified and not user.banned:

# After
is_eligible = user.age >= 18 and user.verified and not user.banned
if is_eligible:
```

### Inline
When: Indirection adds no value
```python
# Before
def get_name(user):
    return user.name
name = get_name(user)

# After
name = user.name
```

### Move
When: Code belongs elsewhere
```
- Function in wrong module
- Method on wrong class
- Constant in wrong file
```

### Replace Conditional with Polymorphism
When: Type-checking switch statements
```python
# Before
if type == "A": do_a()
elif type == "B": do_b()

# After
handler = handlers[type]
handler.process()
```

## Code Smells to Address

| Smell | Refactoring |
|-------|-------------|
| Long function | Extract Function |
| Long parameter list | Introduce Parameter Object |
| Duplicated code | Extract Function/Class |
| Feature envy | Move Method |
| Data clumps | Extract Class |
| Primitive obsession | Replace Primitive with Object |
| Switch statements | Replace with Polymorphism |
| Parallel inheritance | Collapse Hierarchy |

## Quality Criteria

A good refactoring:
- [ ] Tests pass before and after
- [ ] Each step is atomic and committed
- [ ] No behavior change (unless intentional)
- [ ] Code is measurably improved (simpler, clearer, shorter)
- [ ] Changes are small enough to review easily

## Anti-patterns

- **Big bang refactor**: Too many changes at once
- **No tests**: Refactoring without safety net
- **Mixed changes**: Refactoring + features together
- **Premature abstraction**: DRY before pattern emerges
- **Renaming everything**: Changes that don't improve clarity
- **Forgetting to commit**: Losing the ability to revert steps

## Adaptation Notes

When generating for a project:
- Reference project's test commands
- Note project's linting rules (may catch issues)
- Include project's code style conventions
- Mention automated refactoring tools if available (IDE support)
- Respect project's abstraction patterns
