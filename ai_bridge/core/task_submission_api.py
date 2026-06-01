from __future__ import annotations

import json
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
        return [str(item) for item in raw if str(item).strip()]
    if isinstance(raw, str):
        chunks = [item.strip() for item in raw.replace("\r", "\n").split("\n")]
        return [item for item in chunks if item]
    return [str(raw)]




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
    return "No description provided"


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
                return parsed
        except json.JSONDecodeError:
            pass
        return _inject_frontend_standardization({"description": stripped})
    return {}


def create_standard_task(data: dict[str, Any]) -> Task:
    normalized = normalize_user_payload(data)
    try:
        task = Task(
            type=_normalize_task_type(normalized.get("type")),
            input=TaskInput(
                description=_extract_description(normalized),
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
        return task
    except Exception as e:
        raise ValueError(f"Invalid task data format: {e}") from e
