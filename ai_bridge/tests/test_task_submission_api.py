from ai_bridge.core.models import Priority, TaskType
from ai_bridge.core.task_submission_api import create_standard_task, normalize_user_payload


def test_normalize_user_payload_plain_text():
    payload = normalize_user_payload("fix bug in login form")
    assert payload["description"] == "fix bug in login form"


def test_create_standard_task_with_aliases_and_string_lists():
    task = create_standard_task(
        {
            "type": "bug",
            "message": "Repair auth flow",
            "priority": "urgent",
            "files": "backend/auth.ts\nbackend/session.ts",
            "acceptance_criteria": "tests pass\nno regressions",
        }
    )

    assert task.type == TaskType.FIX
    assert task.priority == Priority.CRITICAL
    assert task.input.description == "Repair auth flow"
    assert task.input.files == ["backend/auth.ts", "backend/session.ts"]
    assert task.input.acceptance_criteria == ["tests pass", "no regressions"]
