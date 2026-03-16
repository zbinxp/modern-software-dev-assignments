"""Action item extraction service with sophisticated pattern recognition."""

from dataclasses import dataclass, field
from datetime import datetime
import re
from typing import Any


@dataclass
class ActionItem:
    """Represents an extracted action item with metadata."""
    text: str
    pattern_type: str
    confidence: float
    assignee: str | None = None
    due_date: str | None = None
    priority: str | None = None


# Regex patterns for sophisticated matching
PATTERNS: list[tuple[str, re.Pattern, float]] = [
    # Priority patterns (highest confidence) - with capturing group for priority
    ("priority", re.compile(r"^\s*\(([A-Z1-3])\)\s*(.+)", flags=re.IGNORECASE), 1.0),
    ("priority", re.compile(r"^\s*(high|medium|low)\s*(?:priority)?[:\-]?\s*(.+)", flags=re.IGNORECASE), 0.95),

    # Bullet point prefixes (strip leading - or *)
    ("todo", re.compile(r"^\s*[-*]\s*todo:\s*(.+)", flags=re.IGNORECASE), 1.0),
    ("action", re.compile(r"^\s*[-*]\s*action:\s*(.+)", flags=re.IGNORECASE), 1.0),
    ("task", re.compile(r"^\s*[-*]\s*task:\s*(.+)", flags=re.IGNORECASE), 1.0),
    ("checkbox", re.compile(r"^\s*[-*]\s*\[\s*\]\s*(.+)", flags=re.IGNORECASE), 0.9),
    ("exclamation", re.compile(r"^\s*[-*]\s*(.+[!])$"), 0.7),

    # Standard prefixes
    ("todo", re.compile(r"^\s*todo:\s*(.+)", flags=re.IGNORECASE), 1.0),
    ("action", re.compile(r"^\s*action:\s*(.+)", flags=re.IGNORECASE), 1.0),
    ("task", re.compile(r"^\s*task:\s*(.+)", flags=re.IGNORECASE), 1.0),

    # Checkbox style
    ("checkbox", re.compile(r"^\s*[-*]\s*\[\s*\]\s*(.+)", flags=re.IGNORECASE), 0.9),

    # Exclamation ending (moderate confidence)
    ("exclamation", re.compile(r"^(.+[!])$"), 0.7),

    # @mention pattern (with bullet prefix)
    ("mention", re.compile(r"^\s*[-*]\s*@(\w+)\s+(.+)", flags=re.IGNORECASE), 0.85),
    ("mention", re.compile(r"^\s*@(\w+)\s+(.+)", flags=re.IGNORECASE), 0.85),

    # Action verbs (with bullet prefix)
    ("verb", re.compile(r"^\s*[-*]\s*(call|email|send|review|fix|update|create|delete|write|schedule|finish|complete|submit|approve|check|test|deploy|setup|install|run|build)\b[\s:\-]*(.+)", flags=re.IGNORECASE), 0.6),
    # Action verbs (lower confidence, requires more context)
    ("verb", re.compile(r"^\s*(call|email|send|review|fix|update|create|delete|write|schedule|finish|complete|submit|approve|check|test|deploy|setup|install|run|build)\b[\s:\-]*(.+)", flags=re.IGNORECASE), 0.6),
]

# Due date patterns
DUE_DATE_PATTERN = re.compile(
    r"(?:by|due|before|until|on)\s+(?:this\s+)?(?:Friday|Monday|Tuesday|Wednesday|Thursday|Saturday|Sunday|jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?|\d{1,2}[/-]\d{1,2}(?:[/-]\d{2,4})?|\d{4}[/-]\d{1,2}[/-]\d{1,2}|(?:eod|end\s*of\s*day|end\s*of\s*week|eo[tw]|tomorrow|today))",
    flags=re.IGNORECASE
)


def extract_action_items(text: str | None) -> list[ActionItem]:
    """
    Extract action items from text using sophisticated pattern recognition.

    Args:
        text: The text to extract action items from.

    Returns:
        A list of ActionItem objects with metadata.

    Raises:
        ValueError: If text is not a string.
    """
    if text is None:
        return []
    if not isinstance(text, str):
        raise ValueError(f"Expected string, got {type(text).__name__}")

    if not text.strip():
        return []

    lines = [line.strip() for line in text.splitlines() if line.strip()]
    results: list[ActionItem] = []

    for line in lines:
        # Try each pattern category in order
        matched = _match_patterns(line)
        if matched:
            results.append(matched)

    return results


def _match_patterns(line: str) -> ActionItem | None:
    """Try to match a line against all patterns."""
    for pattern_type, pattern, confidence in PATTERNS:
        match = pattern.match(line)
        if match:
            # Extract the content (different groups for different patterns)
            if pattern_type == "priority":
                groups = match.groups()
                if len(groups) == 2:
                    priority, content = groups
                    text = content.strip()
                    assignee, due_date = _extract_entities(text)
                    return ActionItem(
                        text=text,
                        pattern_type=pattern_type,
                        confidence=confidence,
                        assignee=assignee,
                        due_date=due_date,
                        priority=priority.lower() if priority else None
                    )
                else:
                    text = match.group(1).strip()
                    assignee, due_date = _extract_entities(text)
                    return ActionItem(
                        text=text,
                        pattern_type=pattern_type,
                        confidence=confidence,
                        assignee=assignee,
                        due_date=due_date
                    )
            elif pattern_type in ("todo", "action", "task", "checkbox", "exclamation"):
                text = match.group(1).strip()
                assignee, due_date = _extract_entities(text)
                return ActionItem(
                    text=text,
                    pattern_type=pattern_type,
                    confidence=confidence,
                    assignee=assignee,
                    due_date=due_date
                )
            elif pattern_type == "mention":
                assignee, content = match.groups()
                text = content.strip()
                due_date = _extract_due_date(text)
                return ActionItem(
                    text=text,
                    pattern_type=pattern_type,
                    confidence=confidence,
                    assignee=assignee,
                    due_date=due_date
                )
            elif pattern_type == "verb":
                verb, content = match.groups()
                text = content.strip()
                assignee, due_date = _extract_entities(text)
                return ActionItem(
                    text=text,
                    pattern_type=pattern_type,
                    confidence=confidence,
                    assignee=assignee,
                    due_date=due_date
                )

    return None


def _extract_entities(text: str) -> tuple[str | None, str | None]:
    """Extract assignee and due date from text."""
    assignee = _extract_assignee(text)
    due_date = _extract_due_date(text)
    return assignee, due_date


def _extract_assignee(text: str) -> str | None:
    """Extract @mention assignee from text."""
    match = re.search(r"@(\w+)", text, re.IGNORECASE)
    return match.group(1) if match else None


def _extract_due_date(text: str) -> str | None:
    """Extract due date from text."""
    match = DUE_DATE_PATTERN.search(text)
    return match.group(0).strip() if match else None


# Backward compatibility: legacy function returns simple list of strings
def extract_action_items_simple(text: str | None) -> list[str]:
    """
    Legacy function for backward compatibility.
    Returns simple list of action item strings.
    """
    items = extract_action_items(text)
    return [item.text for item in items]
