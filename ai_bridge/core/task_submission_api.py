from __future__ import annotations

import json
import re
from typing import Any

from .models import Priority, Task, TaskContext, TaskInput, TaskType


_TASK_TYPE_ALIASES: dict[str, str] = {
    "bug": "fix",
    "fix": "fix",
    "issue": "fix",
    "research": "research",
    "doc": "docs",
    "docs": "docs",
    "review": "review",
    "test": "test",
    "tests": "test",
    "plan": "plan",
    "code": "code",
}

_PRIORITY_ALIASES: dict[str, str] = {
    "urgent": "critical",
    "blocker": "critical",
    "crit": "critical",
    "normal": "normal",
    "medium": "normal",
    "default": "normal",
}

_GARBAGE_PATTERNS = (
    r"^[\W_]+$",
    r"^(n/?a|none|null|undefined|test|asdf|qwerty|lol)$",
)


def _normalize_task_type(raw: Any) -> TaskType:
    value = str(raw or "code").strip().lower()
    mapped = _TASK_TYPE_ALIASES.get(value, value)
    try:
        return TaskType(mapped)
    except ValueError:
        return TaskType.CODE


def _normalize_priority(raw: Any) -> Priority:
    value = str(raw or "normal").strip().lower()
    mapped = _PRIORITY_ALIASES.get(value, value)
    try:
        return Priority(mapped)
    except ValueError:
        return Priority.NORMAL


def _as_list(raw: Any) -> list[str]:
    if raw is None:
        return []
    if isinstance(raw, list):
        return [str(item).strip() for item in raw if str(item).strip()]
    if isinstance(raw, str):
        chunks = [item.strip() for item in raw.replace("\r", "\n").split("\n")]
        return [item for item in chunks if item]
    value = str(raw).strip()
    return [value] if value else []


def _is_meaningful_text(text: str) -> bool:
    cleaned = " ".join(text.split()).strip()
    if len(cleaned) < 4:
        return False
    if not re.search(r"[A-Za-zА-Яа-я0-9]", cleaned):
        return False
    lowered = cleaned.lower()
    for pattern in _GARBAGE_PATTERNS:
        if re.match(pattern, lowered):
            return False
    return True


def _is_frontend_oneshot_request(data: dict[str, Any]) -> bool:
    text = " ".join(str(data.get(k, "")) for k in ("description", "message", "prompt", "objective")).lower()
    return any(k in text for k in ["frontend", "ui", "ux", "landing", "catalog", "page", "website", "site", "веб", "страниц", "дизайн"])


def _inject_frontend_standardization(data: dict[str, Any]) -> dict[str, Any]:
    if not _is_frontend_oneshot_request(data):
        return data
    out = dict(data)
    out.setdefault("type", "code")
    out.setdefault("framework", "react")
    out.setdefault("frontend_output_root", "frontend-react")
    out.setdefault("frontend_app_name", "frontend-app")
    out.setdefault("acceptance_criteria", [
        "responsive ui",
        "design tokens applied",
        "semantic sections generated",
        "content seeded",
    ])
    out.setdefault("frontend_schema", {
        "components": [
            {"name": "SiteHeader"},
            {"name": "HeroSection"},
            {"name": "CatalogGrid"},
            {"name": "CourseCard"},
            {"name": "CartSummary"},
            {"name": "AccountPanel"},
            {"name": "SiteFooter"},
        ],
        "pages": ["/", "/catalog", "/course/:id", "/cart", "/checkout", "/account", "/account/lessons"],
    })
    return out


def _extract_description(data: dict[str, Any]) -> str:
    for key in ("description", "message", "text", "prompt", "objective"):
        value = data.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def normalize_user_payload(payload: Any) -> dict[str, Any]:
    if isinstance(payload, dict):
        return _inject_frontend_standardization(payload)
    if isinstance(payload, str):
        stripped = payload.strip()
        if not stripped:
            return {}
        try:
            parsed = json.loads(stripped)
            if isinstance(parsed, dict):
                return _inject_frontend_standardization(parsed)
        except json.JSONDecodeError:
            pass
        return _inject_frontend_standardization({"description": stripped})
    return {}


def validate_normalized_payload(normalized: dict[str, Any]) -> tuple[bool, list[str]]:
    issues: list[str] = []
    if not isinstance(normalized, dict) or not normalized:
        return False, ["empty_payload"]

    description = _extract_description(normalized)
    if not _is_meaningful_text(description):
        issues.append("empty_or_garbage_description")

    task_type = str(normalized.get("type") or "").strip().lower()
    if task_type and task_type not in {t.value for t in TaskType} and task_type not in _TASK_TYPE_ALIASES:
        issues.append("unknown_task_type")

    files = normalized.get("files")
    if files is not None and not isinstance(files, (list, tuple, str)):
        issues.append("invalid_files_field")

    acceptance = normalized.get("acceptance_criteria")
    if acceptance is not None and not isinstance(acceptance, (list, tuple, str)):
        issues.append("invalid_acceptance_criteria")

    if normalized.get("session_id") is not None and not str(normalized.get("session_id")).strip():
        issues.append("empty_session_id")

    return len(issues) == 0, issues


def create_standard_task(data: dict[str, Any]) -> Task:
    normalized = normalize_user_payload(data)
    ok, issues = validate_normalized_payload(normalized)
    if not ok:
        raise ValueError(f"Invalid task payload: {', '.join(issues)}")

    try:
        description = _extract_description(normalized)
        if not description:
            raise ValueError("missing description")

        task = Task(
            type=_normalize_task_type(normalized.get("type")),
            input=TaskInput(
                description=description,
                files=_as_list(normalized.get("files")),
                constraints=_as_list(normalized.get("constraints")),
                acceptance_criteria=_as_list(normalized.get("acceptance_criteria")) or ["tests pass"],
            ),
            context=TaskContext(
                project=str(normalized.get("project", "default")),
                repo_path=str(normalized.get("repo_path", ".")),
                branch=str(normalized.get("branch", "main")),
            ),
            priority=_normalize_priority(normalized.get("priority")),
            session_id=normalized.get("session_id"),
        )
        ext_task_id = normalized.get("task_id")
        if isinstance(ext_task_id, str) and ext_task_id.strip():
            task.task_id = ext_task_id.strip()
        if not task.routing_hints:
            task.routing_hints = {}
        task.routing_hints.setdefault("input_validation", {"status": "ok", "issues": []})
        return task
    except Exception as e:
        raise ValueError(f"Invalid task data format: {e}") from e
