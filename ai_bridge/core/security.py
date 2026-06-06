from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from .orchestration_config import OrchestrationConfig

SECRET_PATTERNS = [
    re.compile(r'(?i)(api[_-]?key|token|secret|password)\s*[:=]\s*["\']?[^"\'\s]+'),
    re.compile(r"sk-[A-Za-z0-9_-]{16,}"),
]


@dataclass(slots=True)
class SecurityPolicy:
    allow_shell: bool = True
    shell_allowlist: list[str] = field(default_factory=lambda: ["pytest", "python -m pytest", "npm test", "agy -p", "antigravity -p"])
    block_commands: list[str] = field(default_factory=lambda: ["rm -rf /", "curl | sh", "sudo", "chmod 777"])


class SecurityManager:
    def __init__(self, policy: SecurityPolicy | None = None, orchestration: OrchestrationConfig | None = None) -> None:
        self.policy = policy or SecurityPolicy()
        self.orchestration = orchestration or OrchestrationConfig.from_env()

    def validate_shell_command(self, command: str) -> bool:
        if not self.policy.allow_shell:
            return False
        normalized = " ".join(command.strip().split())
        if any(blocked in normalized for blocked in self.policy.block_commands):
            return False
        return any(normalized == allowed or normalized.startswith(f"{allowed} ") for allowed in self.policy.shell_allowlist)

    def require_dry_run(self, command: str) -> bool:
        dangerous_tokens = ("rm ", "mv ", "chmod ", "chown ", "docker ", "podman ", "systemctl ")
        return any(token in f" {command} " for token in dangerous_tokens)

    def should_ask_confirmation(self, task: Any) -> bool:
        return self.orchestration.should_ask_confirmation(task)

    def redact_secrets(self, text: str) -> str:
        redacted = text
        for pattern in SECRET_PATTERNS:
            redacted = pattern.sub("[REDACTED]", redacted)
        return redacted

    def safe_context_for_external_ai(self, context: dict) -> dict:
        safe = {}
        for key, value in context.items():
            if any(word in key.lower() for word in ("key", "token", "secret", "password")):
                continue
            safe[key] = self.redact_secrets(str(value)) if isinstance(value, str) else value
        return safe
