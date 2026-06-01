from __future__ import annotations

from pathlib import Path
from typing import Any


class ComponentCodegenModule:
    def generate(self, root: str, schema: dict[str, Any]) -> dict[str, Any]:
        base = Path(root) / "src" / "components" / "ui"
        base.mkdir(parents=True, exist_ok=True)
        generated: list[str] = []
        for comp in schema.get("components", []):
            name = str(comp.get("name", "")).strip()
            if not name:
                continue
            body = (
                f"export interface {name}Props {{ title?: string }}\n"
                f"export function {name}({{ title }}: {name}Props) {{\n"
                f"  return <section aria-label=\"{name}\">{{title ?? '{name}'}}</section>;\n"
                "}\n"
            )
            target = base / f"{name}.tsx"
            target.write_text(body, encoding="utf-8")
            generated.append(str(target))
        return {"status": "generated", "count": len(generated), "files": generated}
