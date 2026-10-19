#!/bin/bash
set -euo pipefail
task_root="$(cd "$(dirname "$0")/.." && pwd)"
cd "$task_root"
if [[ ! -x "$task_root/.venv/bin/lanhu-mcp" ]]; then
  echo '请先运行 ./setup.command --profile all --with-mcp' >&2
  exit 2
fi
exec "$task_root/.venv/bin/python" "$task_root/project.py" mcp-serve
