#!/bin/bash
# Материализует .env из переменных окружения, заданных в настройках
# cloud-окружения (claude.ai/code -> иконка облака -> шестерёнка ->
# Environment variables). Сами значения НИКОГДА не попадают в git —
# в этом репозитории коммитится только .env.example со списком имён.
#
# Если запускается не в облачной сессии — ничего не делает.
set -euo pipefail

if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

cd "$CLAUDE_PROJECT_DIR"

if [ ! -f .env.example ]; then
  exit 0
fi

{
  echo "# Сгенерировано автоматически при старте сессии (session-start.sh)"
  echo "# из Environment variables cloud-окружения. Не редактировать вручную —"
  echo "# правки не переживут следующую сессию. Менять значения нужно в"
  echo "# настройках окружения на claude.ai/code."
  echo
  while IFS= read -r key; do
    [ -z "$key" ] && continue
    value="${!key:-}"
    echo "${key}=${value}"
  done < <(grep -oE '^[A-Z_][A-Z0-9_]*=' .env.example | sed 's/=$//')
} > .env

echo "session-start.sh: .env собран из переменных окружения ($(grep -cE '^[A-Z_][A-Z0-9_]*=' .env) переменных)"
