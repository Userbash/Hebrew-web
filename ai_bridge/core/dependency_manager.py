from __future__ import annotations

import importlib
import logging
import subprocess
import sys
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class DependencySpec:
    module_name: str
    package_name: str
    required: bool = False


class DependencyManager:
    """Dependency checker for orchestrator runtime and optional AI providers."""

    CORE_DEPENDENCIES: tuple[DependencySpec, ...] = (
        DependencySpec("pydantic", "pydantic", required=True),
        DependencySpec("redis", "redis", required=False),
        DependencySpec("pika", "pika", required=False),
    )

    AI_DEPENDENCIES: tuple[DependencySpec, ...] = (
        DependencySpec("openai", "openai", required=False),
        DependencySpec("google.generativeai", "google-generativeai", required=False),
        DependencySpec("mistralai", "mistralai", required=False),
        DependencySpec("langchain", "langchain", required=False),
        DependencySpec("langgraph", "langgraph", required=False),
        DependencySpec("litellm", "litellm", required=False),
        DependencySpec("tiktoken", "tiktoken", required=False),
        DependencySpec("orjson", "orjson", required=False),
        DependencySpec("tenacity", "tenacity", required=False),
    )

    @classmethod
    def find_missing(cls) -> dict[str, list[str]]:
        missing_required: list[str] = []
        missing_optional: list[str] = []

        for spec in (*cls.CORE_DEPENDENCIES, *cls.AI_DEPENDENCIES):
            base_module = spec.module_name.split(".")[0]
            try:
                importlib.import_module(base_module)
            except ImportError:
                if spec.required:
                    missing_required.append(spec.package_name)
                else:
                    missing_optional.append(spec.package_name)

        return {
            "required": sorted(set(missing_required)),
            "optional": sorted(set(missing_optional)),
        }

    @classmethod
    def ensure_required(cls) -> None:
        missing = cls.find_missing()["required"]
        if missing:
            raise RuntimeError(
                "Missing required dependencies: "
                + ", ".join(missing)
                + ". Install them before running orchestrator."
            )

    @classmethod
    def install_optional(cls, packages: list[str]) -> None:
        if not packages:
            return
        cmd = [sys.executable, "-m", "pip", "install"] + packages
        logger.info("Installing optional dependencies: %s", ", ".join(packages))
        subprocess.run(cmd, check=True)
