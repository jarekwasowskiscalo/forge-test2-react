<!-- TEMPLATE: filled in by the requirements stage; the file counts as non-existent until this marker is gone -->
# Scenarios — <change title>

*Seeds. The implementation stage turns them into `.feature` files and binds the steps.*

## Coverage
| Requirement | Scenarios | Unhappy path? |
|---|---|---|
| R-1 | S-1, S-2 | <yes/no> |

## Scenarios

### S-1 — <a title in one sentence>
```gherkin
  @req:<cr_id>/R-1
  Scenario: <one sentence>
    Given <the starting state in business terms>
    When <what the user does>
    Then <what they see>
```

### S-2 — <a title in one sentence, the unhappy path>
```gherkin
  @req:<cr_id>/R-1
  Scenario: <what happens when the system refuses>
    Given <the starting state>
    When <an action that cannot succeed>
    Then <what the user sees and what the system did instead>
```

## Test data

`golden-set/` has two halves and they answer two different questions. **Fixtures** are what a
suite reads instead of inventing; **seed data** is what a freshly created environment opens
with. A value that belongs to both is two values (`golden-set/README.md`).

### For reuse
| Fixture | What it shows | Requirement |
|---|---|---|
| `golden-set/fixtures/<file>` | <what it demonstrates> | R-n |

### New fixtures
- **`<file-name>`** — the rule: <what it demonstrates>; the requirement: R-n; the shape:
  <how many rows, how many days>; boundary values: <which ones>; personal data: <how it is
  kept unambiguously synthetic>

### Seed data
*Does a new environment — a preview, a fresh clone — have to show anything it does not show
today? A change that adds a screen or a concept usually does: an empty one is a screen nobody
can judge. Answer `none — <reason>` when it does not; silence here reads as a decision
nobody took.*

- **`golden-set/seed/<file>`** — what it must show: <what a reviewer has to be able to see>;
  the screen: <which>; nothing near a bound, and nothing a test will assert about.

### Multi-day sequences
| Day | Content | What that day proves |
|---|---|---|
| 1 | <file/state> | <what> |
| 2 | <file/state> | <what> |

### Boundary values
| Rule | Just below | Exactly on the boundary | Just above |
|---|---|---|---|
| <rule> | <value> | <value> | <value> |

### Bounds the requirements did not give
- <the gap — reported, not filled in>
