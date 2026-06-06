
from ai_bridge.core.task_decomposer import TaskDecomposer
from ai_bridge.core.models import Task, TaskInput, TaskType, Priority, Complexity
from uuid import uuid4

# 1. Draft the task
task = Task(
    task_id=str(uuid4()),
    type=TaskType.RESEARCH,
    priority=Priority.NORMAL,
    complexity=Complexity.MEDIUM,
    input=TaskInput(
        description="Analyze codebase for potential refactoring opportunities and generate a report.",
        files=["ai_bridge/core/orchestrator.py"],
        constraints=["No automatic code changes.", "Generate advisory report only."]
    ),
    context={"repo_path": "/var/home/sanya/Hebrew-web"}
)

print(f"[*] Drafting task: {task.task_id}")
print(f"[*] Task description: {task.input.description}")

# 2. Decompose
decomposer = TaskDecomposer()
print("[*] Passing task to decomposer...")
plan = decomposer.decompose(task)

# 3. Output results
print(f"[+] Decomposition complete.")
print(f"[+] Generated {len(plan.atomic_tasks)} atomic tasks:")
for i, t in enumerate(plan.atomic_tasks):
    print(f" {i+1}. [{t.type}] {t.input.description}")
