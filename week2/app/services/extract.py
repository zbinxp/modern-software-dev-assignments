from __future__ import annotations

import os
import re
from typing import List
import json
from typing import Any
from ollama import chat
from dotenv import load_dotenv

load_dotenv()

BULLET_PREFIX_PATTERN = re.compile(r"^\s*([-*•]|\d+\.)\s+")
KEYWORD_PREFIXES = (
    "todo:",
    "action:",
    "next:",
)


def _is_action_line(line: str) -> bool:
    stripped = line.strip().lower()
    if not stripped:
        return False
    if BULLET_PREFIX_PATTERN.match(stripped):
        return True
    if any(stripped.startswith(prefix) for prefix in KEYWORD_PREFIXES):
        return True
    if "[ ]" in stripped or "[todo]" in stripped:
        return True
    return False


def extract_action_items(text: str) -> List[str]:
    lines = text.splitlines()
    extracted: List[str] = []
    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            continue
        if _is_action_line(line):
            cleaned = BULLET_PREFIX_PATTERN.sub("", line)
            cleaned = cleaned.strip()
            # Trim common checkbox markers
            cleaned = cleaned.removeprefix("[ ]").strip()
            cleaned = cleaned.removeprefix("[todo]").strip()
            extracted.append(cleaned)
    # Fallback: if nothing matched, heuristically split into sentences and pick imperative-like ones
    if not extracted:
        sentences = re.split(r"(?<=[.!?])\s+", text.strip())
        for sentence in sentences:
            s = sentence.strip()
            if not s:
                continue
            if _looks_imperative(s):
                extracted.append(s)
    # Deduplicate while preserving order
    seen: set[str] = set()
    unique: List[str] = []
    for item in extracted:
        lowered = item.lower()
        if lowered in seen:
            continue
        seen.add(lowered)
        unique.append(item)
    return unique


def _looks_imperative(sentence: str) -> bool:
    words = re.findall(r"[A-Za-z']+", sentence)
    if not words:
        return False
    first = words[0]
    # Crude heuristic: treat these as imperative starters
    imperative_starters = {
        "add",
        "create",
        "implement",
        "fix",
        "update",
        "write",
        "check",
        "verify",
        "refactor",
        "document",
        "design",
        "investigate",
    }
    return first.lower() in imperative_starters


LLM_SYSTEM_PROMPT = """You are an assistant that extracts action items from meeting notes or text.
An action item is a task, todo, or thing that needs to be done. It often starts with a verb and describes something that needs to be completed.

Output your response as a JSON array of strings, where each string is an action item.
If no action items are found, return an empty array: []

Example:
Input: "We need to fix the bug and also create a new feature."
Output: ["fix the bug", "create a new feature"]

Only output the JSON array, nothing else."""


def extract_action_items_llm(text: str) -> List[str]:
    """Extract action items from text using LLM (Ollama with llama3.1:8b)."""
    user_prompt = f"""Extract all action items from the following text. An action item is a task that needs to be done.

Text:
{text}

Output only a JSON array of action items."""

    response = chat(
        model="llama3.1:8b",
        messages=[
            {"role": "system", "content": LLM_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ],
        options={"temperature": 0.3},
    )

    content = response.message.content.strip()

    # Try to parse JSON from the response
    try:
        # Try direct JSON parsing first
        items = json.loads(content)
        if isinstance(items, list):
            return [str(item).strip() for item in items if str(item).strip()]
    except json.JSONDecodeError:
        pass

    # Fallback: try to extract JSON from markdown code block
    try:
        # Look for JSON in markdown code block
        match = re.search(r'\[.*\]', content, re.DOTALL)
        if match:
            items = json.loads(match.group(0))
            if isinstance(items, list):
                return [str(item).strip() for item in items if str(item).strip()]
    except (json.JSONDecodeError, AttributeError):
        pass

    # If all parsing fails, return empty list
    return []
