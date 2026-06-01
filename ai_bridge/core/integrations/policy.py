from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class LibraryDecision:
    library: str
    placement: str
    reason: str
    risk: str
    priority: str


CORE_SAFE = {
    "pydantic", "pydantic-settings", "fastapi", "uvicorn", "sqlalchemy", "alembic",
    "asyncpg", "redis", "apscheduler", "temporalio", "dbus-next", "langgraph",
    "litellm", "instructor"
}

PLUGIN_ONLY = {
    "crewai", "openai-agents", "autogen", "llamaindex", "pydantic-ai",
    "selenium", "firecrawl", "brightdata", "playwright"
}

DENY_DEFAULT = {"n8n", "cursor", "aider", "astro"}


def decide_library(library: str) -> LibraryDecision:
    lib = library.strip().lower()
    if lib in CORE_SAFE:
        return LibraryDecision(lib, "core", "infrastructure-level dependency", "medium", "high")
    if lib in PLUGIN_ONLY:
        return LibraryDecision(lib, "plugin", "agent/tool framework should be isolated", "high", "medium")
    if lib in DENY_DEFAULT:
        return LibraryDecision(lib, "deny", "not suitable as embedded runtime dependency", "high", "low")
    return LibraryDecision(lib, "plugin", "unknown dependency defaults to isolated plugin", "high", "low")
