"""Tests for action item extraction functionality."""

import pytest
from backend.app.services.extract import (
    extract_action_items,
    extract_action_items_simple,
    ActionItem,
)


class TestBasicPatterns:
    """Test existing patterns still work."""

    def test_todo_prefix(self):
        text = "TODO: write tests"
        items = extract_action_items(text)
        assert len(items) == 1
        assert items[0].text == "write tests"
        assert items[0].pattern_type == "todo"
        assert items[0].confidence == 1.0

    def test_action_prefix(self):
        text = "ACTION: review PR"
        items = extract_action_items(text)
        assert len(items) == 1
        assert items[0].text == "review PR"
        assert items[0].pattern_type == "action"

    def test_exclamation_ending(self):
        text = "Ship it!"
        items = extract_action_items(text)
        assert len(items) == 1
        assert items[0].text == "Ship it!"
        assert items[0].pattern_type == "exclamation"
        assert items[0].confidence == 0.7

    def test_task_prefix(self):
        text = "TASK: complete documentation"
        items = extract_action_items(text)
        assert len(items) == 1
        assert items[0].text == "complete documentation"
        assert items[0].pattern_type == "task"

    def test_case_insensitive(self):
        text = "todo: write tests\nAction: review PR"
        items = extract_action_items(text)
        assert len(items) == 2
        assert items[0].pattern_type == "todo"
        assert items[1].pattern_type == "action"


class TestNewPatterns:
    """Test new pattern recognition."""

    def test_checkbox_pattern(self):
        text = "- [ ] Fix the bug"
        items = extract_action_items(text)
        assert len(items) == 1
        assert items[0].text == "Fix the bug"
        assert items[0].pattern_type == "checkbox"
        assert items[0].confidence == 0.9

    def test_asterisk_checkbox(self):
        text = "* [ ] Another task"
        items = extract_action_items(text)
        assert len(items) == 1
        assert items[0].pattern_type == "checkbox"

    def test_priority_parentheses(self):
        text = "(A) High priority task"
        items = extract_action_items(text)
        assert len(items) == 1
        assert items[0].text == "High priority task"
        assert items[0].pattern_type == "priority"
        assert items[0].priority == "a"
        assert items[0].confidence == 1.0

    def test_priority_number(self):
        text = "(1) Critical task"
        items = extract_action_items(text)
        assert len(items) == 1
        assert items[0].priority == "1"

    def test_priority_text(self):
        text = "High priority: Send report"
        items = extract_action_items(text)
        assert len(items) == 1
        assert items[0].pattern_type == "priority"
        assert items[0].priority == "high"

    def test_mention_pattern(self):
        text = "@john fix the server"
        items = extract_action_items(text)
        assert len(items) == 1
        assert items[0].text == "fix the server"
        assert items[0].pattern_type == "mention"
        assert items[0].assignee == "john"
        assert items[0].confidence == 0.85

    def test_verb_pattern_call(self):
        text = "Call client about the project"
        items = extract_action_items(text)
        assert len(items) == 1
        assert items[0].text == "client about the project"
        assert items[0].pattern_type == "verb"
        assert items[0].confidence == 0.6

    def test_verb_pattern_email(self):
        text = "Email team updates"
        items = extract_action_items(text)
        assert len(items) == 1
        assert items[0].pattern_type == "verb"

    def test_verb_pattern_fix(self):
        text = "Fix authentication bug"
        items = extract_action_items(text)
        assert len(items) == 1
        assert items[0].pattern_type == "verb"

    def test_multiple_verbs(self):
        text = "Send email\nReview PR\nCreate report"
        items = extract_action_items(text)
        assert len(items) == 3
        assert all(item.pattern_type == "verb" for item in items)


class TestEntityExtraction:
    """Test entity extraction (assignee, due date)."""

    def test_due_date_by_friday(self):
        text = "TODO: complete report by Friday"
        items = extract_action_items(text)
        assert len(items) == 1
        assert items[0].due_date is not None
        assert "friday" in items[0].due_date.lower()

    def test_due_date_eod(self):
        text = "ACTION: send email due EOD"
        items = extract_action_items(text)
        assert len(items) == 1
        assert items[0].due_date is not None

    def test_due_date_tomorrow(self):
        text = "Task: finish by tomorrow"
        items = extract_action_items(text)
        assert len(items) == 1
        assert items[0].due_date is not None

    def test_due_date_mmddyyyy(self):
        text = "TODO: submit form due 12/15/2024"
        items = extract_action_items(text)
        assert len(items) == 1
        assert "12/15" in items[0].due_date

    def test_combined_assignee_and_due_date(self):
        text = "@sarah complete review by Monday"
        items = extract_action_items(text)
        assert len(items) == 1
        assert items[0].assignee == "sarah"
        assert items[0].due_date is not None


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_none_input(self):
        items = extract_action_items(None)
        assert items == []

    def test_empty_string(self):
        items = extract_action_items("")
        assert items == []

    def test_whitespace_only(self):
        items = extract_action_items("   \n  \n   ")
        assert items == []

    def test_non_string_input(self):
        with pytest.raises(ValueError, match="Expected string"):
            extract_action_items(123)  # type: ignore

    def test_non_string_list(self):
        with pytest.raises(ValueError):
            extract_action_items(["item1", "item2"])  # type: ignore

    def test_empty_lines_in_text(self):
        text = "TODO: first\n\n\nTODO: second\n"
        items = extract_action_items(text)
        assert len(items) == 2

    def test_lines_with_dashes(self):
        text = "- TODO: bullet item"
        items = extract_action_items(text)
        assert len(items) == 1

    def test_unicode_characters(self):
        text = "TODO: review café menu 🎉"
        items = extract_action_items(text)
        assert len(items) == 1
        assert "café" in items[0].text
        assert "🎉" in items[0].text

    def test_very_long_line(self):
        long_text = "TODO: " + "x" * 10000
        items = extract_action_items(long_text)
        assert len(items) == 1
        assert len(items[0].text) == 10000


class TestConfidenceScoring:
    """Test confidence scoring."""

    def test_highest_confidence_patterns(self):
        """Priority and prefix patterns should have highest confidence."""
        text = "TODO: task\n(A) task\nACTION: task"
        items = extract_action_items(text)
        assert all(item.confidence >= 0.9 for item in items)

    def test_lower_confidence_verb(self):
        """Verb patterns should have lower confidence."""
        text = "Call someone"
        items = extract_action_items(text)
        assert items[0].confidence == 0.6


class TestBackwardCompatibility:
    """Test backward compatibility with simple function."""

    def test_simple_function_returns_strings(self):
        text = "TODO: write tests\nACTION: review PR\nShip it!"
        items = extract_action_items_simple(text)
        assert isinstance(items, list)
        assert all(isinstance(item, str) for item in items)
        assert "write tests" in items
        assert "review PR" in items
        assert "Ship it!" in items

    def test_simple_function_with_none(self):
        items = extract_action_items_simple(None)
        assert items == []


class TestMultipleItems:
    """Test extracting multiple action items."""

    def test_multiple_items_in_text(self):
        text = """
        This is a note
        - TODO: write tests
        - ACTION: review PR
        - Ship it!
        Not actionable
        @john fix this
        (A) Important
        """.strip()
        items = extract_action_items(text)
        # 5 items: TODO, ACTION, exclamation, mention, priority (Not actionable is skipped)
        assert len(items) == 5

    def test_no_action_items(self):
        text = "This is just a regular note without any tasks."
        items = extract_action_items(text)
        assert items == []

    def test_mixed_content(self):
        text = """
        Meeting notes from today.
        TODO: Follow up with client
        We discussed the project timeline.
        ACTION: Update documentation
        @mary schedule meeting by Friday
        """.strip()
        items = extract_action_items(text)
        assert len(items) == 3
        pattern_types = {item.pattern_type for item in items}
        assert "todo" in pattern_types
        assert "action" in pattern_types
        assert "mention" in pattern_types
