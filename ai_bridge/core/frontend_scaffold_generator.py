from __future__ import annotations

from pathlib import Path


class FrontendScaffoldGenerator:
    def generate(self, root: str, app_name: str = "frontend-app") -> dict[str, object]:
        base = Path(root)
        src = base / "src"
        components = src / "components" / "ui"
        features = src / "features"
        for path in (src, components, features):
            path.mkdir(parents=True, exist_ok=True)

        (base / "package.json").write_text(
            '{\n  "name": "%s",\n  "private": true,\n  "scripts": {"dev":"vite","build":"vite build"}\n}\n' % app_name,
            encoding="utf-8",
        )
        (base / "vite.config.ts").write_text(
            "import { defineConfig } from 'vite';\nexport default defineConfig({});\n",
            encoding="utf-8",
        )
        (src / "main.tsx").write_text(
            "import React from 'react';\nimport ReactDOM from 'react-dom/client';\nimport { App } from './App';\nReactDOM.createRoot(document.getElementById('root')!).render(<App />);\n",
            encoding="utf-8",
        )
        (src / "App.tsx").write_text(
            "export function App(){ return <div>Language School UI</div>; }\n",
            encoding="utf-8",
        )
        return {"status": "generated", "root": str(base)}
