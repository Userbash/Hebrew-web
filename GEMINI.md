# Project AI Connection Protocol

You are Gemini CLI, and you are now **DIRECTLY CONNECTED** to the AI Orchestrator Core.

## Integration Rules

1.  **Automated Triggers:** You (Gemini CLI) must monitor all user input for the following keyword prefixes. If detected, you should **delegate immediately** to the Orchestrator:
    *   `CORE:`, `ЯДРО:`, `STATUS:`, `СТАТУС:`, `HEALTH:`, `ЗДОРОВЬЕ:` (System & Monitoring)
    *   `PLAN:`, `ПЛАН:`, `DESIGN:`, `ДИЗАЙН:`, `ARCH:`, `АРХИТЕКТУРА:` (Architecture & Planning)
    *   `BUILD:`, `КОД:`, `РЕАЛИЗУЙ:`, `WRITE:`, `НАПИШИ:`, `DEV:`, `РАЗРАБОТАЙ:` (Code Implementation)
    *   `FIX:`, `ИСПРАВЬ:`, `ПОЧИНИ:`, `BUG:`, `ОШИБКА:`, `DEBUG:`, `ОТЛАДКА:` (Bug Fixing)
    *   `REVIEW:`, `РЕВЬЮ:`, `ПРОВЕРЬ:`, `AUDIT:`, `АУДИТ:`, `SECURITY:`, `БЕЗОПАСНОСТЬ:`, `SCAN:`, `СКАНИРУЙ:` (Security & Quality)
    *   `TEST:`, `ТЕСТ:`, `ПРОТЕСТИРУЙ:`, `CHECK:`, `ПРОВЕРКА:` (Automated Testing)
    *   `RESEARCH:`, `ИССЛЕДУЙ:`, `FIND:`, `НАЙДИ:`, `ANALYZE:`, `АНАЛИЗИРУЙ:`, `LEARN:`, `ИЗУЧИ:` (Deep Analysis & Learning)
    *   `DOCS:`, `ДОКУМЕНТАЦИЯ:`, `DOC:`, `ОПИШИ:`, `README:` (Documentation)
    *   `CLEAN:`, `ОЧИСТИ:`, `REFACTOR:`, `РЕФАКТОР:`, `OPTIMIZE:`, `ОПТИМИЗИРУЙ:` (Maintenance)
    *   `DEPLOY:`, `ДЕПЛОЙ:`, `START:`, `ЗАПУСТИ:`, `RUN:` (Runtime Operations)

2.  **Flexible Prefixing:** You can also use conversational prefixes like "Core, please ANALYZE..." or "Ядро, пожалуйста ПОЧИНИ...".

3.  **Orchestrator Awareness:** You must always consider the background Orchestrator as your primary execution engine for complex technical tasks.

4.  **API Control:** You have direct access to the Orchestrator via `http://localhost:8000/chat`.

5.  **Task Delegation:** When a trigger is detected, formulate a JSON task payload and send it to the Orchestrator. Present the results clearly to the user.

## Connection Status
- **Modules:** `chat_bus`, `trigger_dispatcher` (Active)
- **Status:** Expanded semantic routing established.
