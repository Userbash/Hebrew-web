#!/bin/bash
TASK_DESC="$1"
echo "{\"type\": \"code\", \"description\": \"$TASK_DESC\"}" > /tmp/ai_bridge_queue.json
echo "Задача передана оркестратору: $TASK_DESC"
