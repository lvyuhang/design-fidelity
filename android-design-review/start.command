#!/bin/zsh
set -e
cd "$(dirname "$0")"
if [[ -f .env.local ]]; then source .env.local; fi
if [[ -n "${REVIEW_PYTHON:-}" ]]; then
  task_python="$REVIEW_PYTHON"
elif [[ -x .venv/bin/python ]]; then
  task_python=.venv/bin/python
elif [[ -x ../.venv-fidelity/bin/python ]]; then
  task_python=../.venv-fidelity/bin/python
else
  echo '请先运行：python3 -m venv .venv && .venv/bin/pip install -r requirements.txt'
  exit 1
fi
exec "$task_python" server.py "$@"
