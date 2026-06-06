from __future__ import annotations

from collections import defaultdict
import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field

from .kernel_protocol import KernelAPI, KernelModule
from .models import ExecutionPlan, Priority, Task, TaskContext, TaskInput, TaskType


class DevChatMessage(BaseModel):
    message_id: str = Field(default_factory=lambda: str(uuid4()))
    session_id: str
    role: str
    content: str
    created_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    meta: dict[str, Any] = Field(default_factory=dict)


class DevChatSession(BaseModel):
    session_id: str = Field(default_factory=lambda: str(uuid4()))
    title: str = "Dev Toolkit Session"
    mode: str = "plan"
    repo_context: bool = False
    created_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    message_count: int = 0
    last_summary: str = ""


class DevToolkitRequest(BaseModel):
    session_id: str
    message: str
    mode: str = "plan"
    repo_context: bool = False
    allow_code_changes: bool = False
    allow_execution: bool = False
    dry_run: bool = False
    user_id: str | None = None


class DevClipboardItem(BaseModel):
    clipboard_id: str = Field(default_factory=lambda: str(uuid4()))
    session_id: str
    item_type: str
    content: str
    label: str | None = None
    created_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())


class DevToolkitAuditLog(BaseModel):
    user_id: str | None = None
    session_id: str
    task: str
    mode: str
    agents: list[str] = Field(default_factory=list)
    files_changed: list[str] = Field(default_factory=list)
    diff: str | None = None
    status: str
    created_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())


class DevToolkitResponse(BaseModel):
    session_id: str
    summary: str
    plan: dict[str, Any]
    tasks: list[dict[str, Any]]
    agents: list[dict[str, Any]]
    diff: str | None
    clipboard_payload: str | None
    fulltrace: dict[str, Any]
    status: str


class DevToolkitExecutionContext(BaseModel):
    session: DevChatSession
    request: DevToolkitRequest
    messages: list[DevChatMessage] = Field(default_factory=list)
    permissions: list[str] = Field(default_factory=list)
    source: str = "dev_toolkit"


@dataclass(slots=True)
class DevToolkitModule(KernelModule):
    name: str = "dev_toolkit"
    _api: KernelAPI | None = None
    _sessions: dict[str, DevChatSession] = field(default_factory=dict)
    _messages: dict[str, list[DevChatMessage]] = field(default_factory=lambda: defaultdict(list))
    _clipboard: dict[str, list[DevClipboardItem]] = field(default_factory=lambda: defaultdict(list))
    _audit_logs: list[DevToolkitAuditLog] = field(default_factory=list)
    _last_result: dict[str, Any] = field(default_factory=dict)

    def on_load(self, api: KernelAPI) -> None:
        self._api = api

    def on_unload(self) -> None:
        self._api = None

    def _touch_session(self, session: DevChatSession) -> DevChatSession:
        session.updated_at = datetime.now(UTC).isoformat()
        session.message_count = len(self._messages.get(session.session_id, []))
        return session

    def load_or_create_session(self, session_id: str | None = None, *, mode: str = "plan", repo_context: bool = False) -> DevChatSession:
        normalized = (session_id or "").strip()
        if normalized and normalized in self._sessions:
            session = self._sessions[normalized]
            session.mode = mode
            session.repo_context = repo_context
            return self._touch_session(session)

        if not normalized:
            normalized = str(uuid4())

        session = DevChatSession(session_id=normalized, title=f"Dev Toolkit {normalized[:8]}", mode=mode, repo_context=repo_context)
        self._sessions[normalized] = session
        self._messages.setdefault(normalized, [])
        self._clipboard.setdefault(normalized, [])
        return session

    def list_sessions(self) -> list[DevChatSession]:
        return [self._touch_session(session) for session in sorted(self._sessions.values(), key=lambda item: item.updated_at, reverse=True)]

    def get_messages(self, session_id: str) -> list[DevChatMessage]:
        return list(self._messages.get(session_id, []))

    def get_diff(self, session_id: str) -> dict[str, Any]:
        return {"session_id": session_id, "diff": None, "status": "planned"}

    def get_clipboard_items(self, session_id: str) -> list[DevClipboardItem]:
        return list(self._clipboard.get(session_id, []))

    def _append_message(self, session_id: str, role: str, content: str, **meta: Any) -> DevChatMessage:
        message = DevChatMessage(session_id=session_id, role=role, content=content, meta=dict(meta))
        self._messages[session_id].append(message)
        session = self._sessions.get(session_id)
        if session:
            session.message_count = len(self._messages[session_id])
            session.last_summary = content if role == "assistant" else session.last_summary
            session.updated_at = message.created_at
        return message

    @staticmethod
    def _normalize_mode(mode: str) -> str:
        normalized = (mode or "plan").strip().lower()
        return normalized if normalized in {"plan", "dry_run", "apply", "review", "repo"} else "plan"

    @staticmethod
    def _repo_hint(task: str) -> dict[str, Any]:
        text = task.lower()
        return {
            "mentions_repo": any(keyword in text for keyword in ("repo", "repository", "branch", "diff", "worktree", "pr", "pull request", "release", "changelog", "issue")),
            "mentions_execution": any(keyword in text for keyword in ("test", "verify", "run", "check", "build", "lint")),
            "mentions_code": any(keyword in text for keyword in ("file", "code", "patch", "refactor", "implement", "fix", "bug")),
        }

    def build_dev_context(self, *, session: DevChatSession, message: str, repo_context: bool, mode: str) -> DevToolkitExecutionContext:
        messages = list(self._messages.get(session.session_id, []))
        permissions = ["devtoolkit:read", "devtoolkit:plan"]
        if repo_context:
            permissions.append("devtoolkit:repo")

        return DevToolkitExecutionContext(
            session=session,
            request=DevToolkitRequest(
                session_id=session.session_id,
                message=message,
                mode=mode,
                repo_context=repo_context,
            ),
            messages=messages,
            permissions=permissions,
        )

    def _build_task(self, request: DevToolkitRequest, session: DevChatSession) -> Task:
        hints = self._repo_hint(request.message)
        task_context = TaskContext(
            project="dev-toolkit",
            repo_path=".",
            branch="main",
        )
        task = Task(
            type=TaskType.PLAN,
            input=TaskInput(
                description=request.message.strip(),
                files=[],
                constraints=[
                    "read-only planning",
                    f"mode={request.mode}",
                    f"repo_context={str(request.repo_context).lower()}",
                ],
                acceptance_criteria=[
                    "return plan only",
                    "do not modify files",
                    "do not run shell commands",
                ],
            ),
            context=task_context,
            priority=Priority.NORMAL,
        )
        task.session_id = session.session_id
        task.required_capability = "plan"
        task.routing_hints = {
            "source": "dev_toolkit",
            "mode": request.mode,
            "repo_context": request.repo_context,
            "allow_code_changes": request.allow_code_changes,
            "allow_execution": request.allow_execution,
            "dry_run": request.dry_run,
            **hints,
        }
        return task

    def _plan_to_dict(self, plan: ExecutionPlan) -> dict[str, Any]:
        return {
            "root_task_id": plan.root_task_id,
            "atomic_tasks": [
                {
                    "task_id": task.task_id,
                    "type": task.type.value,
                    "description": task.input.description,
                    "files": task.input.files,
                    "constraints": task.input.constraints,
                    "acceptance_criteria": task.input.acceptance_criteria,
                    "priority": task.priority.value,
                    "required_capability": task.required_capability,
                    "dependencies": task.dependencies,
                    "assigned_model": task.assigned_model,
                    "expected_output": task.expected_output,
                    "routing_hints": task.routing_hints,
                }
                for task in plan.atomic_tasks
            ],
            "draft_layers": plan.draft_layers,
        }

    def _select_agent_candidates(self, task: Task) -> list[dict[str, Any]]:
        if not self._api:
            return []

        registry = self._api.get_context("registry")
        load_balancer = self._api.get_context("load_balancer")
        candidates: list[dict[str, Any]] = []

        if not registry or not load_balancer:
            return [{
                'task_id': task.task_id,
                'agent_id': 'orchestrator',
                'capability': task.required_capability or 'plan',
                'provider': 'orchestrator',
                'model_name': 'orchestrator',
                'status': 'delegated',
                'reason': 'Agent registry or load balancer unavailable',
            }]

        capability = task.required_capability or "plan"
        agents = registry.by_capability(capability, include_disabled=False) if hasattr(registry, "by_capability") else []
        if not agents:
            candidates.append({
                "task_id": task.task_id,
                "agent_id": "orchestrator",
                "capability": capability,
                "provider": "orchestrator",
                "model_name": "orchestrator",
                "status": "delegated",
                "reason": "No direct agent available; orchestrator retains plan stage",
            })
            return candidates

        ranked = sorted(
            agents,
            key=lambda agent: load_balancer.score(agent, capability, task.priority) if hasattr(load_balancer, "score") else 0.0,
            reverse=True,
        )
        for agent in ranked[:4]:
            candidates.append({
                "task_id": task.task_id,
                "agent_id": agent.id,
                "capability": capability,
                "provider": agent.provider,
                "model_name": agent.model_name,
                "status": agent.status.value,
                "score": load_balancer.score(agent, capability, task.priority) if hasattr(load_balancer, "score") else None,
            })
        return candidates

    def _audit(self, request: DevToolkitRequest, *, session: DevChatSession, agents: list[dict[str, Any]], status: str, diff: str | None = None) -> DevToolkitAuditLog:
        audit = DevToolkitAuditLog(
            user_id=request.user_id,
            session_id=session.session_id,
            task=request.message,
            mode=request.mode,
            agents=[str(agent.get("agent_id", "")) for agent in agents if agent.get("agent_id")],
            files_changed=[],
            diff=diff,
            status=status,
        )
        self._audit_logs.append(audit)
        return audit

    def handle_devtoolkit_chat(self, request: DevToolkitRequest, *, user_id: str | None = None) -> DevToolkitResponse:
        if not self._api:
            return DevToolkitResponse(
                session_id=request.session_id or str(uuid4()),
                summary="Kernel API is unavailable",
                plan={},
                tasks=[],
                agents=[],
                diff=None,
                clipboard_payload=None,
                fulltrace={"status": "error", "message": "Kernel API unavailable"},
                status="error",
            )

        request.mode = self._normalize_mode(request.mode)
        session = self.load_or_create_session(request.session_id, mode=request.mode, repo_context=request.repo_context)
        user_message = self._append_message(session.session_id, "user", request.message, mode=request.mode, repo_context=request.repo_context)
        context = self.build_dev_context(session=session, message=request.message, repo_context=request.repo_context, mode=request.mode)

        task = self._build_task(request, session)
        create_plan = getattr(self._api, "create_execution_plan", None)
        if not callable(create_plan):
            return DevToolkitResponse(
                session_id=session.session_id,
                summary="Execution planner is unavailable",
                plan={},
                tasks=[],
                agents=[],
                diff=None,
                clipboard_payload=None,
                fulltrace={"status": "error", "message": "create_execution_plan not available"},
                status="error",
            )

        plan = create_plan(task)
        task_rows = self._plan_to_dict(plan)["atomic_tasks"]
        agents: list[dict[str, Any]] = []
        for atomic_task in plan.atomic_tasks:
            selected = self._select_agent_candidates(atomic_task)
            if selected:
                agents.append(selected[0])
        summary = f"Planned {len(task_rows)} tasks for session {session.session_id} in {request.mode} mode."

        assistant_message = self._append_message(
            session.session_id,
            "assistant",
            summary,
            plan={"task_count": len(task_rows), "agent_count": len(agents)},
        )
        session.last_summary = summary
        self._sessions[session.session_id] = self._touch_session(session)
        audit = self._audit(request, session=session, agents=agents, status="planned")

        plan_dict = self._plan_to_dict(plan)
        response = DevToolkitResponse(
            session_id=session.session_id,
            summary=summary,
            plan=plan_dict,
            tasks=task_rows,
            agents=agents,
            diff=None,
            clipboard_payload=json.dumps(plan_dict, indent=2, ensure_ascii=False),
            fulltrace={
                "session": session.model_dump(),
                "request": request.model_dump(),
                "context": context.model_dump(),
                "user_message": user_message.model_dump(),
                "assistant_message": assistant_message.model_dump(),
                "audit": audit.model_dump(),
                "plan": self._plan_to_dict(plan),
                "mode": request.mode,
                "source": "dev_toolkit",
            },
            status="planned",
        )
        self._last_result = response.model_dump()
        return response

    def handle_execute(self, request: DevToolkitRequest, *, user_id: str | None = None) -> dict[str, Any]:
        session = self.load_or_create_session(request.session_id, mode=request.mode, repo_context=request.repo_context)
        audit = self._audit(request, session=session, agents=[], status="blocked")
        return {
            "session_id": session.session_id,
            "status": "blocked",
            "message": "Execution is disabled in stage 1. Use plan mode only.",
            "audit": audit.model_dump(),
            "permissions": ["devtoolkit:execute", "devtoolkit:apply_changes"],
        }

    def handle_clipboard(self, payload: dict[str, Any]) -> dict[str, Any]:
        session_id = str(payload.get("session_id") or "").strip() or str(uuid4())
        item_type = str(payload.get("item_type") or "summary").strip().lower()
        content = str(payload.get("content") or "").strip()
        label = payload.get("label")
        item = DevClipboardItem(
            session_id=session_id,
            item_type=item_type,
            content=content,
            label=str(label).strip() if isinstance(label, str) and label.strip() else None,
        )
        self._clipboard[session_id].append(item)
        return {"status": "ok", "item": item.model_dump()}

    def finalize(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "sessions": [session.model_dump() for session in self.list_sessions()],
            "messages": {session_id: [message.model_dump() for message in messages] for session_id, messages in self._messages.items()},
            "clipboard": {session_id: [item.model_dump() for item in items] for session_id, items in self._clipboard.items()},
            "audit_logs": [audit.model_dump() for audit in self._audit_logs],
            "last_result": self._last_result,
        }
