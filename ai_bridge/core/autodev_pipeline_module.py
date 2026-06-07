from __future__ import annotations

from pathlib import Path
from typing import Any, Literal
import subprocess
import shutil

from pydantic import BaseModel, Field

from .kernel_protocol import KernelAPI, KernelModule


class ProjectState(BaseModel):
    specs: str
    tasks: list[dict] = Field(default_factory=list)
    api_routes: list[dict] = Field(default_factory=list)
    api_contracts: list[dict] = Field(default_factory=list)
    backend_files: list[dict] = Field(default_factory=list)
    frontend_files: list[dict] = Field(default_factory=list)
    ui_tree: dict | None = None
    frontend_spec: list[dict] = Field(default_factory=list)
    figma_result: dict | None = None
    tests_result: dict | None = None
    lint_result: dict | None = None
    qa_result: dict | None = None
    errors: list[dict] = Field(default_factory=list)
    iteration: int = 0


class FilePayload(BaseModel):
    path: str
    content: str


class BackendAgentResponse(BaseModel):
    files: list[FilePayload] = Field(default_factory=list)
    api_contracts: list[dict] = Field(default_factory=list)


class FrontendAgentResponse(BaseModel):
    files: list[FilePayload] = Field(default_factory=list)


class QAAgentResponse(BaseModel):
    status: Literal["approve", "reject"]
    fixes_needed: list[dict] = Field(default_factory=list)


class AutodevPipelineModule(KernelModule):
    name = "autodev_pipeline"

    def __init__(self, max_iterations: int = 5) -> None:
        self._api: KernelAPI | None = None
        self.max_iterations = max_iterations
        self._last_result: dict[str, Any] = {}

    def on_load(self, api: KernelAPI) -> None:
        self._api = api

    def on_unload(self) -> None:
        self._api = None

    def _run_cmd(self, cmd: list[str], cwd: Path) -> dict[str, Any]:
        if shutil.which(cmd[0]) is None:
            return {"status": "skipped", "stdout": "", "stderr": f"Command not found: {cmd[0]}", "exit_code": 127}
        proc = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
        return {
            "status": "ok" if proc.returncode == 0 else "error",
            "stdout": proc.stdout,
            "stderr": proc.stderr,
            "exit_code": proc.returncode,
        }

    def _run_lint(self, root: Path) -> dict[str, Any]:
        return self._run_cmd(["ruff", "check", str(root)], root)

    def _run_tests(self, root: Path) -> dict[str, Any]:
        import sys
        return self._run_cmd([sys.executable, "-m", "pytest", "-q"], root)

    def _design(self, specs: str, figma_api_available: bool) -> dict[str, Any]:
        ui_tree = {
            "project": "Auto Web Project",
            "pages": [{"name": "Dashboard", "route": "/dashboard", "layout": "sidebar", "sections": [{"type": "header"}, {"type": "stats"}, {"type": "table"}, {"type": "footer"}]}],
        }
        handoff = [{"page": "dashboard", "layout": "sidebar", "components": ["Sidebar", "Header", "StatsCards", "UserTable"], "ui_library": "shadcn", "styling": "tailwind"}]
        figma = {"status": "created" if figma_api_available else "skipped"}
        return {"ui_tree": ui_tree, "frontend_spec": handoff, "figma": figma, "source_specs": specs}

    def run_pipeline(self, specs: str, project_root: str | Path, figma_api_available: bool = False) -> dict[str, Any]:
        root = Path(project_root).resolve()
        state = ProjectState(specs=specs)

        # 1. TDD Enforcement: Check if tests exist
        test_files = list(root.glob("**/test_*.py"))
        if not test_files:
            state.errors.append({"pipeline": "No failing test found. Strict TDD requires a test file."})
            return {"status": "failed", "state": state.model_dump()}

        # 2. TDD Enforcement: Verify test is RED (failing)
        state.tests_result = self._run_tests(root)
        if state.tests_result["status"] == "ok":
            state.errors.append({"pipeline": "Tests are already GREEN. Strict TDD requires a RED (failing) test first."})
            return {"status": "failed", "state": state.model_dump()}

        # UX -> UI -> JSON UI TREE -> FIGMA -> FRONTEND SPEC
        design = self._design(specs, figma_api_available)
        state.ui_tree = design["ui_tree"]
        state.frontend_spec = design["frontend_spec"]
        state.figma_result = design["figma"]

        # Backend/Frontend placeholders (actual agent runtime in kernel)
        backend = BackendAgentResponse.model_validate({"files": [], "api_contracts": [{"method": "GET", "path": "/health", "request_schema": {}, "response_schema": {"status": "ok"}}]})
        state.backend_files = [f.model_dump() for f in backend.files]
        state.api_contracts = backend.api_contracts
        state.api_routes = backend.api_contracts

        frontend = FrontendAgentResponse.model_validate({"files": []})
        state.frontend_files = [f.model_dump() for f in frontend.files]

        while state.iteration < self.max_iterations:
            state.lint_result = self._run_lint(root)
            state.tests_result = self._run_tests(root)

            qa_raw = {
                "status": "approve" if state.lint_result["status"] in {"ok", "skipped"} and state.tests_result["status"] in {"ok", "skipped"} else "reject",
                "fixes_needed": [],
            }
            state.qa_result = QAAgentResponse.model_validate(qa_raw).model_dump()

            if state.qa_result["status"] == "approve":
                self._last_result = {"status": "success", "iteration": state.iteration, "state": state.model_dump()}
                return self._last_result

            state.errors.append({"lint": state.lint_result, "tests": state.tests_result, "qa": state.qa_result})
            state.iteration += 1

        self._last_result = {"status": "failed", "reason": "MAX_ITERATIONS exceeded", "state": state.model_dump()}
        return self._last_result

    def finalize(self) -> dict[str, Any]:
        return {"last_result": self._last_result, "max_iterations": self.max_iterations}
