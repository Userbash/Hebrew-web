#!/usr/bin/env bash
set -euo pipefail

TASK_ID="${1:?task id required}"
TARGET_FILE="${2:?target file required}"
TASK_TEXT="${3:?task text required}"

mkdir -p .agent/tasks

cat > ".agent/tasks/${TASK_ID}-gemini.txt" <<EOF
Ты внешний сабагент Gemini CLI.

Задача:
${TASK_TEXT}

Файл:
${TARGET_FILE}

Правила:
- не изменяй код напрямую;
- верни только отчет;
- не пиши общие фразы;
- укажи конкретные строки;
- укажи риск;
- предложи исправление;
- форматируй ответ строго по шаблону.

Шаблон ответа:

task_id: ${TASK_ID}
agent: gemini
file: ${TARGET_FILE}
status:

FOUND:
FIXED_SUGGESTION:
CHANGED_FILES:
COMMANDS_TO_VERIFY:
RISKS:
NEXT:
EOF

echo ".agent/tasks/${TASK_ID}-gemini.txt"
