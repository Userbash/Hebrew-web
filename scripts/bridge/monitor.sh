#!/bin/bash
while true; do
  clear
  echo "=========================================="
  echo "   СИСТЕМА ОРКЕСТРАЦИИ ИИ (HEBREW-WEB)   "
  echo "   Время: $(date +'%H:%M:%S')"
  echo "=========================================="
  
  if flatpak-spawn --host podman exec hebrew_ai_backend [ -f /tmp/orchestrator_status.json ]; then
    STATUS_JSON=$(flatpak-spawn --host podman exec hebrew_ai_backend cat /tmp/orchestrator_status.json)
    STATUS=$(echo $STATUS_JSON | jq -r .status)
    TASKS=$(echo $STATUS_JSON | jq -r .active_tasks)
    MODULES=$(echo $STATUS_JSON | jq -r '.modules | join(", ")')
    
    echo -e "СТАТУС:       \e[32m[ ОНЛАЙН ]\e[0m"
    echo -e "АКТИВНОСТЬ:   \e[1;33m$TASKS\e[0m задач(и) в обработке"
    echo -e "МОДУЛИ ЯДРА:  $MODULES"
  else
    echo -e "СТАТУС:       \e[31m[ ОФЛАЙН / ИНИЦИАЛИЗАЦИЯ ]\e[0m"
  fi
  
  echo "=========================================="
  echo "Для выхода нажмите Ctrl+C"
  sleep 2
done
