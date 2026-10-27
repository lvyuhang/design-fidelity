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
from round_log import RoundLog
from fidelity_contract import sha256


def preflight(contract_path, skill, require_style_evidence=False):
    sys.path.insert(0, str(skill / 'scripts'))
    from preflight import check
    from graphic_source_audit import audit_contract
    result = check(contract_path, require_style_evidence)
    graphics = audit_contract(contract_path)
    if graphics['status'] != 'PASS':
        preview = '; '.join(f"{v.get('file', '')}:{v.get('line', '')} {v['reason']}"
                           for v in graphics['failures'][:8])
        raise ValueError('Unverified drawn icon or CustomPainter: ' + preview)
    result['graphic_source_audit'] = graphics
    from dart_fidelity_lint import lint_contract
    lint = lint_contract(contract_path)
    if lint['status'] == 'FAIL':
        preview = '; '.join(f"{v['file']}:{v['line']} {v['rule']} {v.get('symbol', '')}"
                            for v in lint['findings'][:8])
        raise ValueError(f"Dart fidelity lint failed ({len(lint['findings'])}): {preview}. "
                         'Use lanhu_fidelity primitives/tokens; see scripts/dart_fidelity_lint.py')
    result['dart_fidelity_lint'] = lint
    return result


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
    parser.add_argument('--task-log', type=Path, help='Persistent per-task JSON; defaults to output parent/task-run.json')
    parser.add_argument('--round-note', default='', help='Batch changes/retry reason; explain overruns beyond round 3')
    args = parser.parse_args()
    contract, app, out, skill = [p.resolve() for p in (args.contract, args.app, args.output, args.skill)]
    out.mkdir(parents=True, exist_ok=False)
    started = time.monotonic()
    report = {'status': 'RUNNING', 'scope': 'validation of supplied implementation; not end-to-end development time',
              'started_unix': time.time(), 'stages': [], 'gate_status': None}
    task_log = RoundLog(args.task_log or out.parent/'task-run.json')
    ticket = None
    current_stage = 'round_log'

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
        ticket = task_log.begin(contract, out, args.round_note, command={'app':str(app),'test':args.test})
        report['iteration'] = ticket
        current_stage = 'baseline'
        if ticket['baseline_differences']:
            raise ValueError('Frozen acceptance changed; this run cannot demonstrate same-quality improvement: '
                             + ', '.join(ticket['baseline_differences'][:8]))
        current_stage = 'preflight'
        begin = time.monotonic()
        report['preflight'] = preflight(contract, skill, args.require_style_evidence)
        report['stages'].append({'name': 'preflight', 'seconds': round(time.monotonic()-begin, 3), 'exit_code': 0})
        env = {**os.environ, args.output_env: str(out / 'render.png')}
        current_stage = 'render'
        stage('render', [sys.executable, str(skill / 'scripts/render_with_receipt.py'),
                        '--contract', str(contract), '--candidate', str(out / 'render.png'),
                        '--receipt', str(out / 'receipt.json'), '--cwd', str(app), '--',
                        'flutter', 'test', '--no-pub', args.test])
        report['render_sha256'] = sha256(out/'render.png')
        current_stage = 'gate'
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
        report['failures'] += [
            {'check': f"geometry.{item['node_id']}", 'label': item['label'], 'failures': item['failures']}
            for item in candidate.get('geometry', {}).get('failures', [])]
        if not candidate.get('responsive', {}).get('passed', True):
            report['failures'].append({'check': 'responsive', 'label': 'multi-size layout',
                                       'failures': [f"{f['kind']}: {f['message']}" for f in
                                                    candidate['responsive']['findings']
                                                    if f['kind'] in (*candidate['responsive'].get('blocking', []), 'missing')][:10]})
        report['metrics'] = {key: value['metrics'] for key,value in candidate.get('regions', {}).items()}
        if gate_code or not gate.get('passed'):
            raise ValueError(gate.get('reason') or f'Visual gate failed; see {out / "gate/visual-gate-report.json"}')
        if args.analyze:
            current_stage = 'analyze'
            stage('analyze', ['dart', 'analyze', *args.analyze])
        if args.build:
            current_stage = 'build'
            stage('build', ['flutter', 'build', 'web', '--release', '--no-pub'])
        report['status'] = gate['status']
    except (ValueError, OSError, KeyError, subprocess.TimeoutExpired) as exc:
        report['status'] = 'NOT_ACCEPTED'
        report['error'] = str(exc)
        report['failed_stage'] = current_stage
    finally:
        report['seconds'] = round(time.monotonic()-started, 3)
        (out / 'run.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n')
        if ticket:
            task_log.finish(ticket, report)
        print(json.dumps({'status': report['status'], 'seconds': report['seconds'],
                          'gate_status': report['gate_status'], 'error': report.get('error'),
                          'style_gap_count': len(report.get('preflight', {}).get('style_gaps', [])),
                          'source_obligations': report.get('preflight', {}).get('coverage'),
                          'failed_checks': report.get('failures', [])[:10],
                          'round': ticket['round_number'] if ticket else None,
                          'attempt': ticket['attempt_number'] if ticket else None,
                          'over_target': ticket['over_target'] if ticket else None,
                          'task_log': ticket['html'] if ticket else None,
                          'report': str(out / 'run.json')}, ensure_ascii=False))
    return 0 if report['status'] in ('PASS','PASS_WITH_EXCLUSIONS') else 1


if __name__ == '__main__':
    raise SystemExit(main())
