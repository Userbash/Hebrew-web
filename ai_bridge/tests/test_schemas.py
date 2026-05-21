import json
from pathlib import Path


def test_result_schema_has_required_contract():
    schema = json.loads(Path("ai_bridge/schemas/result.schema.json").read_text())

    assert "task_id" in schema["required"]
    assert "output" in schema["properties"]
    assert schema["properties"]["confidence"]["maximum"] == 1
