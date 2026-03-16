# Task 2 Plan: Enhance Action Item Extraction

## Context

The current action item extraction in `backend/app/services/extract.py` uses only three basic patterns:
- Lines starting with `TODO:`
- Lines starting with `ACTION:`
- Lines ending with `!`

This is too limited for real-world use. The task is to enhance this with more sophisticated pattern recognition, add proper unit tests, and ensure error handling.

## Current State

- **Extract function**: `backend/app/services/extract.py` - simple function with basic patterns
- **Existing tests**: `backend/tests/test_extract.py` - only 1 basic test
- **No error handling**: Function doesn't handle edge cases (empty text, None input, etc.)

## Implementation Plan

### 1. Enhance Pattern Recognition

Add more sophisticated patterns to detect action items:

**Existing patterns to keep:**
- `TODO:` / `todo:` prefixes
- `ACTION:` / `action:` prefixes
- Lines ending with `!`

**New patterns to add:**
- `TASK:` / `task:` prefix variations
- `@name` mentions (e.g., "@john fix this")
- `[ ]` checkbox style (Markdown tasks)
- Priority indicators like `(A)`, `(High)`, `(1)` at start
- Verbs at start: "Call...", "Email...", "Send...", "Review...", "Fix...", "Update..."
- Due date patterns: "by Friday", "due 12/15", "by EOD"

**Data structure enhancement:**
- Return structured data instead of just strings
- Include: original text, detected pattern type, confidence score, extracted entities (assignee, due date)

```python
# Proposed new return type
class ActionItem:
    text: str
    pattern_type: str  # "todo", "action", "checkbox", "mention", "verb", etc.
    confidence: float   # 0.0 to 1.0
    assignee: str | None  # extracted from @mention
    due_date: str | None  # extracted from date patterns
```

### 2. Add Unit Tests

Create comprehensive tests in `backend/tests/test_extract.py`:

- Test all existing patterns still work
- Test new patterns with various inputs
- Test edge cases:
  - Empty text
  - None input
  - Whitespace-only input
  - Very long lines
  - Unicode characters
  - Mixed case variations
- Test confidence scoring
- Test entity extraction (assignee, due date)

### 3. Error Handling

- Add input validation (type checking)
- Handle None/empty gracefully with appropriate exceptions or defaults
- Add docstrings with type hints
- Consider adding a custom exception class for extraction errors

## Files to Modify

| File | Changes |
|------|---------|
| `backend/app/services/extract.py` | Enhance extraction logic, add structured output, add error handling |
| `backend/tests/test_extract.py` | Add comprehensive unit tests |

## Verification

1. Run existing tests to ensure backward compatibility: `pytest backend/tests/test_extract.py -v`
2. Add new tests and verify they pass
3. Test with various input samples to verify pattern recognition works
4. Verify error handling with invalid inputs

## Notes

- Keep backward compatibility - existing callers should still work
- Consider making the extraction configurable (allow enabling/disabling specific patterns)
- The function is currently not connected to any API endpoint - consider if it should be exposed via the API
