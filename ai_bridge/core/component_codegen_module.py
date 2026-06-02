from __future__ import annotations

from pathlib import Path
from typing import Any


class ComponentCodegenModule:
    def generate(self, root: str, schema: dict[str, Any]) -> dict[str, Any]:
        base = Path(root) / "src" / "components" / "ui"
        base.mkdir(parents=True, exist_ok=True)
        generated: list[str] = []
        
        # Mapping components to Tailwind designs
        component_designs = {
            "HeroSection": "bg-[#2A5C82] text-white py-20 px-6 text-center",
            "FeatureCards": "grid grid-cols-1 md:grid-cols-3 gap-6 p-6",
            "UserTable": "w-full border-collapse border border-gray-200 mt-4"
        }

        for comp in schema.get("components", []):
            name = str(comp.get("name", "")).strip()
            if not name:
                continue
            
            style = component_designs.get(name, "p-4 border rounded")
            
            body = (
                f"export interface {name}Props {{ title?: string; children?: React.ReactNode }}\n"
                f"export function {name}({{ title, children }}: {name}Props) {{\n"
                f"  return <section className=\"{style}\">"
                f"<h2 className=\"text-2xl font-bold mb-4\">{{title ?? '{name}'}}</h2>"
                f"{{children}}"
                "</section>;\n"
                "}\n"
            )
            target = base / f"{name}.tsx"
            target.write_text(body, encoding="utf-8")
            generated.append(str(target))
        return {"status": "generated", "count": len(generated), "files": generated}
