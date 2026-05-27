from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from .kernel_protocol import KernelAPI, KernelModule
from .models import TaskType, Priority

logger = logging.getLogger("trigger_dispatcher")

@dataclass
class TriggerDispatcherModule:
    """
    Automates Orchestrator activation by detecting keywords and semantic patterns
    in the chat stream.
    """
    name: str = "trigger_dispatcher"
    _api: KernelAPI | None = None
    
    # Mapping triggers to TaskTypes with expanded patterns
    TRIGGERS: Dict[str, TaskType] = field(default_factory=lambda: {
        # 1. System & Status
        r"^(CORE|ЯДРО|STATUS|СТАТУС|HEALTH|ЗДОРОВЬЕ):": TaskType.RESEARCH,
        
        # 2. Planning & Architecture
        r"^(PLAN|ПЛАН|DESIGN|ДИЗАЙН|ARCH|АРХИТЕКТУРА):": TaskType.PLAN,
        
        # 3. Implementation & Development
        r"^(BUILD|КОД|РЕАЛИЗУЙ|WRITE|НАПИШИ|DEV|РАЗРАБОТАЙ):": TaskType.CODE,
        
        # 4. Debugging & Maintenance
        r"^(FIX|ИСПРАВЬ|ПОЧИНИ|BUG|ОШИБКА|DEBUG|ОТЛАДКА):": TaskType.FIX,
        r"^(CLEAN|ОЧИСТИ|REFACTOR|РЕФАКТОР|OPTIMIZE|ОПТИМИЗИРУЙ):": TaskType.FIX,
        
        # 5. Quality, Security & Audit
        r"^(REVIEW|РЕВЬЮ|ПРОВЕРЬ|AUDIT|АУДИТ|SECURITY|БЕЗОПАСНОСТЬ|SCAN|СКАНИРУЙ):": TaskType.REVIEW,
        
        # 6. Testing
        r"^(TEST|ТЕСТ|ПРОТЕСТИРУЙ|CHECK|ПРОВЕРКА):": TaskType.TEST,
        
        # 7. Knowledge & Analysis
        r"^(RESEARCH|ИССЛЕДУЙ|FIND|НАЙДИ|ANALYZE|АНАЛИЗИРУЙ|LEARN|ИЗУЧИ):": TaskType.RESEARCH,
        
        # 8. Documentation
        r"^(DOCS|ДОКУМЕНТАЦИЯ|DOC|ОПИШИ|README):": TaskType.DOCS,
        
        # 9. Deployment & Runtime
        r"^(DEPLOY|ДЕПЛОЙ|START|ЗАПУСТИ|RUN):": TaskType.CODE,
    })

    def on_load(self, api: KernelAPI) -> None:
        self._api = api
        self._api.log("info", f"[TRIGGER] {self.name} system active. Monitoring chat for {len(self.TRIGGERS)} categories.")

    def process_chat_input(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Analyzes text for triggers and returns a formatted Task payload if found.
        Supports prefixes like 'Core, please ANALYZE...' or 'Ядро, ИССЛЕДУЙ...'
        """
        # Clean up common prefixes to find the actual command
        clean_text = re.sub(r"^(CORE|ЯДРО|AI|ИИ)[,\s]+(PLEASE|ПОЖАЛУЙСТА)?[,\s]*", "", text, flags=re.IGNORECASE).strip()
        
        for pattern, task_type in self.TRIGGERS.items():
            if re.search(pattern, clean_text, re.IGNORECASE):
                # Extract description by removing the trigger word and the colon
                description = re.sub(pattern, "", clean_text, flags=re.IGNORECASE).strip()
                
                self._api.log("info", f"[TRIGGER] Detected {task_type.value} trigger in message.")
                
                return {
                    "type": task_type.value,
                    "description": description or "Auto-triggered task",
                    "priority": "high" if "!!!" in text else "normal",
                    "source": "auto_trigger"
                }
        return None

    def on_unload(self) -> None:
        pass

    def before_task(self, task: Any, context: dict[str, Any]) -> None:
        pass

    def after_task(self, task: Any, result: Any, context: dict[str, Any]) -> None:
        pass

    def finalize(self) -> dict[str, Any]:
        return {"status": "active", "registered_patterns": len(self.TRIGGERS)}
