"""Utility helpers for validation, parsing, and CLI formatting."""

from __future__ import annotations

import json
from typing import Any, Iterable

ALLOWED_PRIORITIES = {"low", "medium", "high"}
ALLOWED_STATUSES = {"not started", "in progress", "done"}


class ValidationError(Exception):
    """Raised when generated JSON does not match required structure."""


def normalize_priority(priority: str) -> str:
    """Normalize priority values to Notion-compatible labels."""
    value = priority.strip().lower()
    if value not in ALLOWED_PRIORITIES:
        raise ValidationError(f"Invalid priority: {priority}")
    return value.title()


def normalize_status(status: str) -> str:
    """Normalize status values to Notion-compatible labels."""
    value = status.strip().lower()
    if value not in ALLOWED_STATUSES:
        raise ValidationError(f"Invalid status: {status}")
    if value == "not started":
        return "Not Started"
    if value == "in progress":
        return "In Progress"
    return "Done"


def parse_json_strict(payload: str) -> dict[str, Any]:
    """Parse AI output as strict JSON object.

    This method intentionally rejects non-object roots and malformed JSON.
    """
    try:
        data = json.loads(payload)
    except json.JSONDecodeError as exc:
        raise ValidationError(f"Failed to parse JSON: {exc}") from exc

    if not isinstance(data, dict):
        raise ValidationError("AI output must be a JSON object")
    return data


def _require_str(data: dict[str, Any], key: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValidationError(f"Field '{key}' must be a non-empty string")
    return value.strip()


def _require_list(data: dict[str, Any], key: str) -> list[Any]:
    value = data.get(key)
    if not isinstance(value, list):
        raise ValidationError(f"Field '{key}' must be a list")
    return value


def validate_initial_plan(data: dict[str, Any]) -> dict[str, Any]:
    """Validate initial startup JSON contract from AI."""
    startup_name = _require_str(data, "startup_name")
    vision = _require_str(data, "vision")

    key_features = _require_list(data, "key_features")
    roadmap = _require_list(data, "roadmap")
    tasks = _require_list(data, "tasks")

    if not all(isinstance(item, str) and item.strip() for item in key_features):
        raise ValidationError("All key_features must be non-empty strings")

    if not all(isinstance(item, str) and item.strip() for item in roadmap):
        raise ValidationError("All roadmap phases must be non-empty strings")

    validated_tasks = validate_tasks(tasks)

    return {
        "startup_name": startup_name,
        "vision": vision,
        "key_features": [item.strip() for item in key_features],
        "roadmap": [item.strip() for item in roadmap],
        "tasks": validated_tasks,
    }


def validate_iteration_plan(data: dict[str, Any]) -> dict[str, Any]:
    """Validate update-loop JSON contract from AI."""
    suggestions = _require_list(data, "suggestions")
    tasks = _require_list(data, "next_tasks")

    if not all(isinstance(item, str) and item.strip() for item in suggestions):
        raise ValidationError("All suggestions must be non-empty strings")

    validated_tasks = validate_tasks(tasks)

    return {
        "suggestions": [item.strip() for item in suggestions],
        "next_tasks": validated_tasks,
    }


def validate_tasks(tasks: Iterable[Any]) -> list[dict[str, str]]:
    """Validate and normalize task items from AI output."""
    validated: list[dict[str, str]] = []
    for index, item in enumerate(tasks):
        if not isinstance(item, dict):
            raise ValidationError(f"Task at index {index} must be an object")

        title = item.get("title")
        priority = item.get("priority")
        status = item.get("status")

        if not isinstance(title, str) or not title.strip():
            raise ValidationError(f"Task title at index {index} must be non-empty")
        if not isinstance(priority, str):
            raise ValidationError(f"Task priority at index {index} must be a string")
        if not isinstance(status, str):
            raise ValidationError(f"Task status at index {index} must be a string")

        validated.append(
            {
                "title": title.strip(),
                "priority": normalize_priority(priority),
                "status": normalize_status(status),
            }
        )

    return validated


def comma_split(input_text: str) -> list[str]:
    """Split comma-separated user input into cleaned unique task titles."""
    items: list[str] = []
    for part in input_text.split(","):
        cleaned = part.strip()
        if cleaned and cleaned.lower() not in {"none", "n/a"}:
            items.append(cleaned)

    # Preserve order while removing duplicates.
    seen = set()
    unique_items = []
    for item in items:
        key = item.lower()
        if key in seen:
            continue
        seen.add(key)
        unique_items.append(item)
    return unique_items
