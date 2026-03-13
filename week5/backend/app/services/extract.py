import re


def extract_hashtags(text: str) -> list[str]:
    """Extract hashtags from text.

    Args:
        text: The text to parse for hashtags.

    Returns:
        List of tag names (without # prefix), deduplicated.
    """
    # Match #word where word is alphanumeric, but require whitespace or start of line before #
    hashtags = re.findall(r'(?:^|\s)#(\w+)', text)
    # Deduplicate while preserving order
    seen = set()
    result = []
    for tag in hashtags:
        if tag not in seen:
            seen.add(tag)
            result.append(tag)
    return result


def extract_checkbox_tasks(text: str) -> list[str]:
    """Extract checkbox tasks from text.

    Args:
        text: The text to parse for checkbox tasks.

    Returns:
        List of task descriptions.
    """
    tasks = re.findall(r'^\s*-\s*\[ \]\s*(.+)$', text, re.MULTILINE)
    return tasks


def extract_action_items(text: str) -> list[str]:
    lines = [line.strip("- ") for line in text.splitlines() if line.strip()]
    return [line for line in lines if line.endswith("!") or line.lower().startswith("todo:")]


def extract_all(text: str) -> dict:
    """Extract all patterns from text.

    Args:
        text: The text to parse.

    Returns:
        Dictionary with:
        - hashtags: list of tag names (from #hashtags)
        - action_items: list of checkbox task descriptions (from - [ ] tasks)
        - legacy_items: list of existing TODO:/! items
    """
    return {
        "hashtags": extract_hashtags(text),
        "action_items": extract_checkbox_tasks(text),
        "legacy_items": extract_action_items(text),
    }
