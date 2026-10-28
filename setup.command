#!/bin/zsh
set -e
cd "$(dirname "$0")"
for task_python in "${DESIGN_FIDELITY_PYTHON:-${JUXINGGE_PYTHON:-}}" python3.13 python3.12 python3.11 python3; do
  [[ -n "$task_python" ]] || continue
  if command -v "$task_python" >/dev/null 2>&1 && "$task_python" -c 'import sys; sys.exit(sys.version_info < (3,11))' 2>/dev/null; then
    exec "$task_python" project.py setup "$@"
  fi
done
echo '需要 Python 3.11+。安装后重试，或设置 DESIGN_FIDELITY_PYTHON=/path/to/python3。'
exit 2
