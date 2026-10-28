#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CASE = ROOT / 'design_evidence/message-backup-34/optimized-v1'
APP = ROOT / 'flutter_ui_components'
SKILL = Path('/Users/tan/.codex/skills/design-fidelity')
PYTHON = ROOT / '.venv-fidelity/bin/python'
RUN_ID = datetime.now().strftime('%Y%m%d-%H%M%S')
RUN = CASE / 'runs' / RUN_ID
CONTRACT = CASE / 'visual-contract.json'
CANDIDATE = RUN / 'render.png'
RECEIPT = RUN / 'render-receipt.json'
GATE = RUN / 'gate'


def execute(name: str, command: list[str], *, cwd: Path = ROOT, env: dict[str, str] | None = None) -> dict:
    started = time.perf_counter()
    completed = subprocess.run(command, cwd=cwd, env=env, text=True, capture_output=True)
    elapsed = time.perf_counter() - started
    record = {
        'stage': name,
        'seconds': round(elapsed, 3),
        'exit_code': completed.returncode,
        'command': command,
        'stdout_tail': completed.stdout[-2000:],
        'stderr_tail': completed.stderr[-2000:],
    }
    print(f"[{name}] {elapsed:.2f}s exit={completed.returncode}")
    if completed.returncode:
        if completed.stdout:
            print(completed.stdout[-2000:])
        if completed.stderr:
            print(completed.stderr[-2000:], file=sys.stderr)
    return record


def main() -> int:
    RUN.mkdir(parents=True, exist_ok=False)
    started_at = datetime.now().astimezone()
    start = time.perf_counter()
    stages = []
    stages.append(execute('cached_evidence_preflight', [str(PYTHON), str(ROOT / 'tools/prepare_message_backup_34_optimized.py'), '--verify-only']))
    if stages[-1]['exit_code']:
        return finish(started_at, start, stages, 'FAIL')
    env = dict(os.environ)
    env['MESSAGE_BACKUP_34_RENDER_OUTPUT'] = str(CANDIDATE)
    env['MESSAGE_BACKUP_34_RENDER_SCALE'] = '2'
    stages.append(execute('flutter_render_and_interaction_tests', [
        str(PYTHON), str(SKILL / 'scripts/render_with_receipt.py'),
        '--contract', str(CONTRACT), '--candidate', str(CANDIDATE),
        '--receipt', str(RECEIPT), '--cwd', str(APP), '--',
        'flutter', 'test', '--no-pub', 'test/message_backup_34_render_test.dart',
    ], env=env))
    if stages[-1]['exit_code']:
        return finish(started_at, start, stages, 'FAIL')
    stages.append(execute('visual_gate', [
        str(PYTHON), str(SKILL / 'scripts/visual_fidelity_gate.py'),
        '--contract', str(CONTRACT), '--candidate', f'optimized={CANDIDATE}',
        '--receipt', f'optimized={RECEIPT}', '--output-dir', str(GATE),
    ]))
    if stages[-1]['exit_code']:
        return finish(started_at, start, stages, 'FAIL')
    stages.append(execute('flutter_static_analysis', [
        'flutter', 'analyze', '--no-pub',
        'lib/experiments/message_backup_34_page.dart',
        'test/message_backup_34_render_test.dart',
    ], cwd=APP))
    if stages[-1]['exit_code'] == 255:
        stages.append(execute('dart_static_analysis_fallback', [
            'dart', 'analyze',
            'lib/experiments/message_backup_34_page.dart',
            'test/message_backup_34_render_test.dart',
        ], cwd=APP))
    if stages[-1]['exit_code']:
        return finish(started_at, start, stages, 'FAIL')
    stages.append(execute('flutter_web_release_build', ['flutter', 'build', 'web', '--release', '--no-pub'], cwd=APP))
    status = 'PASS' if not stages[-1]['exit_code'] else 'FAIL'
    return finish(started_at, start, stages, status)


def finish(started_at: datetime, start: float, stages: list[dict], status: str) -> int:
    ended_at = datetime.now().astimezone()
    gate_report = GATE / 'visual-gate-report.json'
    gate = json.loads(gate_report.read_text()) if gate_report.exists() else None
    result = {
        'run_id': RUN_ID,
        'status': status,
        'started_at': started_at.isoformat(),
        'ended_at': ended_at.isoformat(),
        'elapsed_seconds': round(time.perf_counter() - start, 3),
        'workflow': 'optimized same-page replay v1',
        'model_work_excluded': True,
        'mcp_calls': 0,
        'source': 'frozen local snapshot b3437778812e65917e3972d7062be2c3',
        'contract': str(CONTRACT),
        'contract_sha256': __import__('hashlib').sha256(CONTRACT.read_bytes()).hexdigest() if CONTRACT.exists() else None,
        'stages': stages,
        'gate_status': gate.get('status') if gate else None,
        'gate_report': str(gate_report) if gate else None,
    }
    (RUN / 'run-log.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    latest = CASE / 'latest-run.json'
    latest.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'status': status, 'elapsed_seconds': result['elapsed_seconds'], 'run_log': str(RUN / 'run-log.json'), 'gate_status': result['gate_status']}, ensure_ascii=False))
    return 0 if status == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
