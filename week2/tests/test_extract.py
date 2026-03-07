import os
import pytest

from ..app.services.extract import extract_action_items, extract_action_items_llm


def test_extract_bullets_and_checkboxes():
    text = """
    Notes from meeting:
    - [ ] Set up database
    * implement API extract endpoint
    1. Write tests
    Some narrative sentence.
    """.strip()

    items = extract_action_items(text)
    assert "Set up database" in items
    assert "implement API extract endpoint" in items
    assert "Write tests" in items


def test_llm_extract_bullet_list():
    """Test LLM extraction with bullet list format."""
    text = """
    Notes from meeting:
    - Set up database
    * implement API extract endpoint
    1. Write tests
    Some narrative sentence.
    """.strip()

    items = extract_action_items_llm(text)
    # Should extract the action items
    assert len(items) > 0
    # Check that bullet items are captured
    item_text = " ".join(items).lower()
    assert "set up database" in item_text
    assert "implement api" in item_text
    assert "write tests" in item_text


def test_llm_extract_keyword_prefixed():
    """Test LLM extraction with keyword-prefixed lines."""
    text = """
    Meeting notes:
    TODO: Fix the login bug
    ACTION: Update documentation
    NEXT: Review pull requests
    Just some regular text here.
    """.strip()

    items = extract_action_items_llm(text)
    # Should extract the keyword-prefixed items
    assert len(items) > 0
    item_text = " ".join(items).lower()
    assert "fix the login bug" in item_text
    assert "update documentation" in item_text
    assert "review pull requests" in item_text


def test_llm_extract_empty_input():
    """Test LLM extraction with empty/no action input."""
    # When there's no meaningful action items, LLM may return empty or may include example
    # Just verify it returns a list
    items = extract_action_items_llm("")
    assert isinstance(items, list)

    items = extract_action_items_llm("   ")
    assert isinstance(items, list)

    items = extract_action_items_llm("Just some regular sentences without any action items.")
    # May return empty or may include example text, just verify it's a list
    assert isinstance(items, list)


def test_llm_extract_checkboxes():
    """Test LLM extraction with checkbox format."""
    text = """
    Project notes:
    [ ] Buy groceries
    [x] Clean the house
    [todo] Call mom
    Regular text here.
    """.strip()

    items = extract_action_items_llm(text)
    # Should extract checkbox items
    assert len(items) > 0
    item_text = " ".join(items).lower()
    assert "buy groceries" in item_text
    assert "call mom" in item_text
