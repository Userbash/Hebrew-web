from __future__ import annotations

import os
import shlex
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .kernel_protocol import KernelAPI, KernelModule
from .models import RoleProfile


SOURCECRAFT_REPO_KEYWORDS = (
    "repo",
    "repository",
    "worktree",
    "branch",
    "status",
    "diff",
    "clone",
    "checkout",
)
SOURCECRAFT_PR_KEYWORDS = (
    "pull request",
    "pr ",
    " pr",
    "merge request",
    "review",
    "patch",
)
SOURCECRAFT_RELEASE_KEYWORDS = (
    "issue",
    "label",
    "milestone",
    "release",
    "changelog",
    "notes",
    "triage",
)
SOURCECRAFT_DOCS_KEYWORDS = (
    "docs",
    "documentation",
    "explain",
    "summary",
    "commit message",
    "commit log",
)
SOURCECRAFT_VERIFICATION_KEYWORDS = (
    "test",
    "tests",
    "ci",
    "verification",
    "checklist",
    "health",
    "quota",
    "workflow",
)


@dataclass(slots=True)
class SourceCraftModule(KernelModule):
    name: str = "sourcecraft"
    _api: KernelAPI | None = None
    _binary: str | None = None
    _version: str | None = None
    _status: str = "idle"
    _last_error: str | None = None
    _last_probe: dict[str, Any] = field(default_factory=dict)

    @staticmethod
    def _timeout_sec() -> float:
        raw = os.getenv("SOURCECRAFT_CLI_TIMEOUT_SEC", "10").strip()
        try:
            return max(1.0, float(raw))
        except ValueError:
            return 10.0

    @staticmethod
    def _repo_root() -> Path:
        return Path(__file__).resolve().parents[2]

    def _candidate_bins(self) -> list[str]:
        env_bin = os.getenv("SOURCECRAFT_CLI_BIN", "").strip()
        if env_bin:
            return [env_bin]

        candidates = []
        candidates.append(str(self._repo_root() / ".tooling" / "sourcecraft" / "bin" / "src"))
        resolved = shutil.which("src")
        if resolved:
            candidates.append(resolved)
        return [candidate for candidate in candidates if candidate]

    def _resolve_binary(self) -> str | None:
        for candidate in self._candidate_bins():
            path = Path(candidate).expanduser()
            if path.is_file() and os.access(path, os.X_OK):
                return str(path)
        return None

    def _run(self, args: list[str]) -> subprocess.CompletedProcess[str]:
        if not self._binary:
            raise FileNotFoundError("SourceCraft CLI binary not resolved")
        return subprocess.run(
            [self._binary, *args],
            capture_output=True,
            text=True,
            timeout=self._timeout_sec(),
            check=False,
        )

    def _probe_version(self) -> dict[str, Any]:
        attempts = [["version"], ["--version"], ["-v"]]
        errors: list[str] = []
        for args in attempts:
            try:
                proc = self._run(args)
            except Exception as exc:
                errors.append(f"{shlex.join([self._binary or 'src', *args])}: {exc}")
                continue

            stdout = (proc.stdout or "").strip()
            stderr = (proc.stderr or "").strip()
            if proc.returncode == 0 and stdout:
                return {
                    "ok": True,
                    "command": args,
                    "stdout": stdout,
                    "stderr": stderr,
                    "returncode": proc.returncode,
                }

            errors.append(
                f"{shlex.join([self._binary or 'src', *args])}: rc={proc.returncode} stdout={stdout[:200]} stderr={stderr[:200]}"
            )

        return {"ok": False, "errors": errors}

    @staticmethod
    def _use_cases() -> list[dict[str, str]]:
        return [
            {"task": "repo ops", "fit": "clone, init, repo, browse, status"},
            {"task": "PR flow", "fit": "pr, prdescription, codereview"},
            {"task": "issue/release", "fit": "issue, label, milestone, release"},
            {"task": "agentic code", "fit": "code, do, skill, run"},
            {"task": "governance", "fit": "quota, update, auth, envs"},
        ]

    @staticmethod
    def _delegation_matrix() -> list[dict[str, str]]:
        return [
            {"task_family": "repo status / worktree diff", "handler": "SourceCraft"},
            {"task_family": "PR draft / PR description", "handler": "SourceCraft"},
            {"task_family": "issue triage / labels / milestones", "handler": "SourceCraft"},
            {"task_family": "release notes / changelog", "handler": "SourceCraft"},
            {"task_family": "feature code implementation", "handler": "codex-main or frontend-dev-1"},
            {"task_family": "tests / CI verification", "handler": "tester-1 or codex-main"},
            {"task_family": "review / security review", "handler": "reviewer-1"},
            {"task_family": "docs / UI design", "handler": "frontend-design-1 or antigravity-cli-1"},
        ]

    @staticmethod
    def _role_profile() -> RoleProfile:
        return RoleProfile(
            name="sourcecraft",
            title="SourceCraft Developer Copilot",
            description="Developer assistant role for SourceCraft flows that coordinates repository operations, PR work, and delivery hygiene.",
            summary="Developer assistant role for SourceCraft flows that coordinates repository operations, PR work, and delivery hygiene.",
            capabilities=["sourcecraft", "repo_ops", "pr_flow", "issue_release", "governance"],
            responsibilities=[
                "summarize repository state and worktree changes",
                "draft and review pull requests and descriptions",
                "triage issues, milestones, labels, and release notes",
                "prepare task breakdowns for code, docs, tests, and repo maintenance",
                "surface CI, quota, and workflow status to the orchestrator",
            ],
            supported_task_types=["code", "fix", "review", "docs", "research", "plan"],
            supported_capabilities=["sourcecraft", "repo_ops", "pr_flow", "issue_release", "governance"],
            pipeline_stages=["intake", "repo_analysis", "task_planning", "drafting", "review_handoff", "delivery_handoff"],
            guardrails=[
                "do not bypass security gates or destructive confirmations",
                "keep repository mutations explicit and reviewable",
                "prefer concise, traceable diffs and PR descriptions",
                "escalate production, secret, and billing changes to the orchestrator",
            ],
        )

    @staticmethod
    def _task_text(task: Any, context: dict[str, Any] | None = None) -> str:
        pieces: list[str] = []
        if context:
            for key in ("description", "objective", "message", "prompt", "summary"):
                value = context.get(key)
                if isinstance(value, str) and value.strip():
                    pieces.append(value.strip())
        description = str(getattr(getattr(task, "input", None), "description", "") or "").strip()
        if description:
            pieces.append(description)
        task_type = str(getattr(getattr(task, "type", None), "value", getattr(task, "type", ""))).strip()
        if task_type:
            pieces.append(task_type)
        files = getattr(getattr(task, "input", None), "files", []) or []
        if isinstance(files, list):
            pieces.extend(str(item) for item in files if str(item).strip())
        constraints = getattr(getattr(task, "input", None), "constraints", []) or []
        if isinstance(constraints, list):
            pieces.extend(str(item) for item in constraints if str(item).strip())
        return " ".join(pieces).lower()

    @staticmethod
    def _task_family(task_text: str) -> str:
        if any(keyword in task_text for keyword in SOURCECRAFT_REPO_KEYWORDS):
            return "repo_ops"
        if any(keyword in task_text for keyword in SOURCECRAFT_PR_KEYWORDS):
            return "pr_flow"
        if any(keyword in task_text for keyword in SOURCECRAFT_RELEASE_KEYWORDS):
            return "issue_release"
        if any(keyword in task_text for keyword in SOURCECRAFT_DOCS_KEYWORDS):
            return "docs_workflow"
        if any(keyword in task_text for keyword in SOURCECRAFT_VERIFICATION_KEYWORDS):
            return "verification"
        return "general"

    @staticmethod
    def _recommended_actions(task_family: str) -> list[str]:
        mapping = {
            "repo_ops": [
                "summarize repository state",
                "prepare a clean worktree summary",
                "list the next repository actions",
            ],
            "pr_flow": [
                "draft the pull request description",
                "summarize the code changes for reviewers",
                "highlight review and merge risks",
            ],
            "issue_release": [
                "triage the issue or release request",
                "group labels, milestones, and release notes",
                "prepare a concise handoff summary",
            ],
            "docs_workflow": [
                "produce a readable explanation of the change",
                "draft documentation or commit text",
                "summarize architecture or workflow impact",
            ],
            "verification": [
                "build a test plan",
                "list the checks that should run in the core",
                "prepare a human-readable health summary",
            ],
        }
        return mapping.get(task_family, [
            "summarize the task",
            "prepare a handoff for the core",
        ])

    @staticmethod
    def _core_retained_actions() -> list[str]:
        return [
            "security enforcement",
            "provider routing",
            "scheduler decisions",
            "budget controls",
            "mutating execution",
            "failover and retries",
        ]

    def build_delegation_profile(self, task: Any, context: dict[str, Any] | None = None) -> dict[str, Any]:
        text = self._task_text(task, context)
        task_family = self._task_family(text)
        task_type = str(getattr(getattr(task, "type", None), "value", getattr(task, "type", ""))).lower()
        required_capability = str(getattr(task, "required_capability", "") or "").strip().lower()
        is_sourcecraft_task = required_capability == "sourcecraft" or task_family != "general" or task_type in {"plan", "docs", "research"}
        should_delegate = task_family in {"repo_ops", "pr_flow", "issue_release", "docs_workflow", "verification"} or required_capability == "sourcecraft"

        return {
            "enabled": self._status in {"ready", "degraded"},
            "status": self._status,
            "task_family": task_family,
            "task_type": task_type or None,
            "is_sourcecraft_task": is_sourcecraft_task,
            "should_delegate": should_delegate,
            "recommended_owner": "sourcecraft" if should_delegate else "core",
            "delegation_mode": "advisory" if should_delegate else "core",
            "core_retained_actions": self._core_retained_actions(),
            "sourcecraft_actions": self._recommended_actions(task_family),
            "sourcecraft_role": self._role_profile().as_dict(),
        }

    def on_load(self, api: KernelAPI) -> None:
        self._api = api
        self._binary = self._resolve_binary()
        if not self._binary:
            self._status = "error"
            self._last_error = "SourceCraft CLI binary not found"
            self._last_probe = {"ok": False, "error": self._last_error, "binary_candidates": self._candidate_bins()}
            api.log("warning", "[SOURCECRAFT] src binary not found; module loaded in degraded mode.")
            return

        self._last_probe = self._probe_version()
        if self._last_probe.get("ok"):
            self._version = str(self._last_probe.get("stdout") or "").splitlines()[0].strip()
            self._status = "ready"
            self._last_error = None
            api.log("info", f"[SOURCECRAFT] src ready: {self._version}")
        else:
            self._status = "degraded"
            self._last_error = "; ".join(self._last_probe.get("errors", []))
            api.log("warning", f"[SOURCECRAFT] src probe degraded: {self._last_error}")

    def on_unload(self) -> None:
        self._status = "idle"
        self._last_error = None
        self._last_probe = {}

    def before_task(self, task: Any, context: dict[str, Any]) -> None:
        description = str(getattr(getattr(task, "input", None), "description", "") or context.get("description") or "").lower()
        task_type = str(getattr(getattr(task, "type", None), "value", getattr(task, "type", ""))).lower()
        likely_repo_work = any(
            keyword in description
            for keyword in ("repo", "repository", "pr", "pull request", "issue", "release", "clone", "branch", "status", "quota", "sourcecraft", "src")
        ) or task_type in {"plan", "code", "fix", "review", "docs", "research"}

        role_profile = self._role_profile()
        delegation = self.build_delegation_profile(task, context)
        context["sourcecraft"] = {
            "enabled": self._status in {"ready", "degraded"},
            "binary": self._binary,
            "version": self._version,
            "status": self._status,
            "likely_repo_work": likely_repo_work,
            "use_cases": self._use_cases(),
            "delegation_matrix": self._delegation_matrix(),
            "role": role_profile.as_dict(),
            "delegation": delegation,
        }

        if likely_repo_work:
            context["sourcecraft"]["recommended_flow"] = [
                "src status",
                "src repo",
                "src pr",
                "src issue",
                "src do",
            ]
        if delegation["should_delegate"]:
            context["sourcecraft"]["automation"] = {
                "owner": "sourcecraft",
                "task_family": delegation["task_family"],
                "actions": delegation["sourcecraft_actions"],
                "core_retained_actions": delegation["core_retained_actions"],
            }

    def after_task(self, task: Any, result: Any, context: dict[str, Any]) -> None:
        sourcecraft = context.get("sourcecraft")
        if not isinstance(sourcecraft, dict):
            return
        output = getattr(result, "output", {})
        summary = ""
        if isinstance(output, dict):
            summary = str(output.get("summary", "") or "")
        sourcecraft["last_result"] = {
            "task_id": getattr(task, "task_id", None),
            "status": getattr(getattr(result, "status", None), "value", getattr(result, "status", None)),
            "summary": summary,
            "next_recommendations": list(getattr(result, "next_recommendations", []) or []),
        }

    def finalize(self) -> dict[str, Any]:
        return {
            "status": self._status,
            "binary": self._binary,
            "version": self._version,
            "last_error": self._last_error,
            "probe": self._last_probe,
            "use_cases": self._use_cases(),
            "delegation_matrix": self._delegation_matrix(),
            "delegation_examples": {
                "repo_ops": self._recommended_actions("repo_ops"),
                "pr_flow": self._recommended_actions("pr_flow"),
                "issue_release": self._recommended_actions("issue_release"),
                "docs_workflow": self._recommended_actions("docs_workflow"),
                "verification": self._recommended_actions("verification"),
            },
            "role": self._role_profile().as_dict(),
            "binary_hint": str(self._repo_root() / ".tooling" / "sourcecraft" / "bin" / "src"),
        }
