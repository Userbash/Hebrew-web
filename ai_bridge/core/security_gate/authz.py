from __future__ import annotations

import getpass
import os
from pathlib import Path

from .models import SecurityCheckReport, SecurityIssue


class PreDeployAuthorization:
    def __init__(self, repo_root: Path) -> None:
        self.repo_root = repo_root

    def run(self, env: dict[str, str] | None = None) -> SecurityCheckReport:
        env = env or dict(os.environ)
        issues: list[SecurityIssue] = []

        current_user = getpass.getuser()
        allowed_users_raw = env.get("AI_BRIDGE_DEPLOY_ALLOWED_USERS", current_user)
        allowed_users = {item.strip() for item in allowed_users_raw.split(",") if item.strip()}
        if current_user not in allowed_users:
            issues.append(SecurityIssue(
                category="authorization",
                severity="high",
                message=f"Current user '{current_user}' is not allowed to deploy",
                recommendation="Add user to AI_BRIDGE_DEPLOY_ALLOWED_USERS",
            ))

        provided_val = env.get("AI_BRIDGE_DEPLOY_AUTH_TOKEN", "").strip()
        required_val = env.get("AI_BRIDGE_DEPLOY_TOKEN", "").strip()

        auth_path = self.repo_root / ".deploy_auth_token"
        if not required_val and auth_path.exists():
            required_val = auth_path.read_text().strip()

        if required_val and provided_val != required_val:
            issues.append(SecurityIssue(
                category="authorization",
                severity="high",
                message="Deploy authorization token is missing or invalid",
                recommendation="Set AI_BRIDGE_DEPLOY_AUTH_TOKEN with correct value",
            ))

        return SecurityCheckReport(name="pre_deploy_authorization", allowed=not issues, issues=issues)
