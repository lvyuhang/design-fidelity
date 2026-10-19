#!/usr/bin/env python3
"""One reusable preflight/render/gate runner; never edits acceptance criteria."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time


def preflight(contract_path, skill, require_style_evidence=False):
    sys.path.insert(0, str(skill / 'scripts'))
    from preflight import check
    return check(contract_path, require_style_evidence)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--contract', required=True, type=Path)
    parser.add_argument('--app', required=True, type=Path)
    parser.add_argument('--test', required=True)
    parser.add_argument('--output-env', required=True)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--skill', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--require-style-evidence', action='store_true')
    parser.add_argument('--analyze', nargs='*', default=[])
    parser.add_argument('--build', action='store_true')
    args = parser.parse_args()
    contract, app, out, skill = [p.resolve() for p in (args.contract, args.app, args.output, args.skill)]
    out.mkdir(parents=True, exist_ok=False)
    started = time.monotonic()
    report = {'status': 'RUNNING', 'scope': 'validation of supplied implementation; not end-to-end development time',
              'started_unix': time.time(), 'stages': [], 'gate_status': None}

    def stage(name, command, allow_failure=False):
        begin = time.monotonic()
        with (out / f'{name}.log').open('w') as log:
            result = subprocess.run(command, cwd=app, env=env, stdout=log,
                                    stderr=subprocess.STDOUT, timeout=300)
        report['stages'].append({'name': name, 'seconds': round(time.monotonic()-begin, 3),
                                 'exit_code': result.returncode})
        if result.returncode and not allow_failure:
            raise ValueError(f'{name} failed; read {out / (name + ".log")}')
        return result.returncode

    try:
        begin = time.monotonic()
        report['preflight'] = preflight(contract, skill, args.require_style_evidence)
        report['stages'].append({'name': 'preflight', 'seconds': round(time.monotonic()-begin, 3), 'exit_code': 0})
        env = {**os.environ, args.output_env: str(out / 'render.png')}
        stage('render', [sys.executable, str(skill / 'scripts/render_with_receipt.py'),
                        '--contract', str(contract), '--candidate', str(out / 'render.png'),
                        '--receipt', str(out / 'receipt.json'), '--cwd', str(app), '--',
                        'flutter', 'test', '--no-pub', args.test])
        gate_code = stage('gate', [sys.executable, str(skill / 'scripts/visual_fidelity_gate.py'),
                      '--contract', str(contract), '--candidate', f'flutter={out / "render.png"}',
                      '--receipt', f'flutter={out / "receipt.json"}', '--output-dir', str(out / 'gate')], allow_failure=True)
        gate = json.loads((out / 'gate/visual-gate-report.json').read_text())
        report['gate_status'] = gate['status']
        candidate = gate.get('candidates', {}).get('flutter', {})
        report['failures'] = [
            {'check': f'{group}.{key}', 'label': value.get('label'),
             'failures': value.get('failures'), 'error': value.get('error')}
            for group in ('regions', 'features', 'relations', 'colors')
            for key, value in candidate.get(group, {}).items() if not value.get('passed')]
        report['metrics'] = {key: value['metrics'] for key,value in candidate.get('regions', {}).items()}
        if gate_code or not gate.get('passed'):
            raise ValueError(gate.get('reason') or f'Visual gate failed; see {out / "gate/visual-gate-report.json"}')
        if args.analyze:
            stage('analyze', ['dart', 'analyze', *args.analyze])
        if args.build:
            stage('build', ['flutter', 'build', 'web', '--release', '--no-pub'])
        report['status'] = 'PASS'
    except (ValueError, OSError, KeyError, subprocess.TimeoutExpired) as exc:
        report['status'] = 'NOT_ACCEPTED'
        report['error'] = str(exc)
    finally:
        report['seconds'] = round(time.monotonic()-started, 3)
        (out / 'run.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n')
        print(json.dumps({'status': report['status'], 'seconds': report['seconds'],
                          'gate_status': report['gate_status'], 'error': report.get('error'),
                          'style_gap_count': len(report.get('preflight', {}).get('style_gaps', [])),
                          'failed_checks': report.get('failures', [])[:10],
                          'report': str(out / 'run.json')}, ensure_ascii=False))
    return 0 if report['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
