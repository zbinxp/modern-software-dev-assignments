from backend.app.services.extract import extract_action_items, extract_hashtags, extract_checkbox_tasks, extract_all


def test_extract_action_items():
    text = """
    This is a note
    - TODO: write tests
    - Ship it!
    Not actionable
    """.strip()
    items = extract_action_items(text)
    assert "TODO: write tests" in items
    assert "Ship it!" in items


def test_extract_hashtags_single():
    text = "This is a note with #tag1"
    tags = extract_hashtags(text)
    assert tags == ["tag1"]


def test_extract_hashtags_multiple():
    text = "Note with #tag1 and #tag2 and #tag3"
    tags = extract_hashtags(text)
    assert tags == ["tag1", "tag2", "tag3"]


def test_extract_hashtags_deduplicate():
    text = "Note with #tag1 and #tag1 again"
    tags = extract_hashtags(text)
    assert tags == ["tag1"]


def test_extract_hashtags_empty():
    text = "Note with no hashtags"
    tags = extract_hashtags(text)
    assert tags == []


def test_extract_hashtags_underscore():
    text = "Note with #tag_name"
    tags = extract_hashtags(text)
    assert tags == ["tag_name"]


def test_extract_checkbox_tasks_single():
    text = """Note content
    - [ ] Task 1"""
    tasks = extract_checkbox_tasks(text)
    assert tasks == ["Task 1"]


def test_extract_checkbox_tasks_multiple():
    text = """- [ ] Task 1
- [ ] Task 2
- [ ] Task 3"""
    tasks = extract_checkbox_tasks(text)
    assert tasks == ["Task 1", "Task 2", "Task 3"]


def test_extract_checkbox_tasks_empty():
    text = "Note with no checkboxes"
    tasks = extract_checkbox_tasks(text)
    assert tasks == []


def test_extract_checkbox_tasks_not_checked():
    text = """- [x] Already done
- [ ] Not done"""
    tasks = extract_checkbox_tasks(text)
    assert tasks == ["Not done"]


def test_extract_all():
    text = """Note with #tag1
- [ ] Task 1
- [ ] Task 2
TODO: Legacy item
- Ship it!"""
    result = extract_all(text)
    assert result["hashtags"] == ["tag1"]
    assert result["action_items"] == ["Task 1", "Task 2"]
    assert "TODO: Legacy item" in result["legacy_items"]
    assert "Ship it!" in result["legacy_items"]


def test_extract_all_empty():
    text = "Just plain text"
    result = extract_all(text)
    assert result["hashtags"] == []
    assert result["action_items"] == []
    assert result["legacy_items"] == []
