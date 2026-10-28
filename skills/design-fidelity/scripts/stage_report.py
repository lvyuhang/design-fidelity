#!/usr/bin/env python3
"""Summarise a page run from its artifacts, in the test plan's categories.

Hand-written summaries mixed blocking failures with observations (e.g. counted
non-blocking text overlaps as gate blockers) and dropped the node-level detail
needed to fix anything. This reads session.json, the latest validate/accept
run, its gate report, the contract and the codegen report, and prints the
numbers exactly as recorded. Unavailable values stay null.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

GROUPS = ('regions', 'features', 'relations', 'colors')


def _read(path):
    try:
        return json.loads(Path(path).read_text())
    except (OSError, ValueError, TypeError):
        return None


def build(config_path: Path) -> dict:
    config = json.loads(config_path.read_text())
    base = config_path.resolve().parent
    run_dir = (base / config['run_dir']).resolve()
    session = _read(run_dir / 'session.json') or {'events': []}
    events = session.get('events', [])
    runs = [e for e in events if e['action'] in ('validate', 'accept') and e.get('report')]
    latest = runs[-1] if runs else None
    run = _read(latest['report']) if latest else None
    gate = _read(Path(latest['report']).parent / 'gate' / 'visual-gate-report.json') if latest else None
    candidate = ((gate or {}).get('candidates') or {}).get('flutter') or {}
    contract = _read(base / config['contract']) if config.get('contract') else None
    generations = [e for e in events if e['action'] == 'generate' and e.get('status') == 'OK']
    codegen = _read(generations[-1]['report']) if generations else None

    blocking = Counter()
    pixel_failures = []
    for group in GROUPS:
        for name, item in candidate.get(group, {}).items():
            if not item.get('passed', True):
                blocking[group] += 1
                pixel_failures.append({'check': f'{group}.{name}', 'label': item.get('label'),
                                       'failures': item.get('failures') or item.get('reason')})
    geometry = candidate.get('geometry') or {}
    blocking['geometry'] = len(geometry.get('failures', []))
    responsive = candidate.get('responsive') or {}
    findings = responsive.get('findings', [])
    blocking_kinds = set(responsive.get('blocking', [])) | {'missing'}
    by_kind = Counter(f['kind'] for f in findings)
    for kind, count in by_kind.items():
        if kind in blocking_kinds:
            blocking[f'responsive.{kind}'] = count
    observations = {f'responsive.{k}': v for k, v in by_kind.items() if k not in blocking_kinds}
    lint = ((run or {}).get('preflight') or {}).get('dart_fidelity_lint') or {}
    summary = session.get('summary') or {}
    rounds = summary.get('rounds') or {}
    return {
        'page': config.get('name'),
        'session_status': session.get('status'),
        'latest_run': {'action': latest['action'], 'status': latest.get('status'),
                       'report': latest['report']} if latest else None,
        'gate_status': (run or {}).get('gate_status'),
        'failed_stage': (run or {}).get('failed_stage'),
        'blocking_total': sum(v for v in blocking.values()),
        'blocking': {k: v for k, v in blocking.items() if v},
        'observations': observations,
        'geometry_failures': geometry.get('failures', []),
        'pixel_failures': pixel_failures,
        'responsive_findings': findings,
        'lint': {'status': lint.get('status'), 'findings': len(lint.get('findings', [])),
                 'suppressed': lint.get('suppressed', [])},
        'exclusions': [{'reason': s.get('reason'), 'rect': s.get('rect')}
                       for s in (contract or {}).get('exclude_shapes', [])],
        'excluded_fraction': (gate or {}).get('excluded_fraction'),
        'generation': {k: (codegen or {}).get(k) for k in ('mode_counts',)} | {
            'unsupported': len((codegen or {}).get('unsupported', [])),
            'issues': len((codegen or {}).get('issues', [])),
            'scene_obligations': Counter(o['status'] for o in
                                         ((codegen or {}).get('scene_test') or {}).get('obligations', []))},
        'rounds': rounds.get('rounds'),
        'validation_attempts': rounds.get('validation_attempts'),
        'elapsed_seconds': summary.get('elapsed_seconds'),
        'phase_seconds': summary.get('phase_seconds'),
        'tokens': summary.get('tokens'),
        'note': 'Blocking = fails the gate. Observations (e.g. text_overlap at 1.3x) are recorded '
                'but do not block. A generator first draft without model rounds is a baseline, '
                'not a quality verdict.',
    }


def markdown(report: dict) -> str:
    lines = [f"# {report['page']} 运行报告", '',
             '| 项 | 值 |', '|---|---|',
             f"| 会话 / 最近一次运行 | {report['session_status']} / "
             f"{(report['latest_run'] or {}).get('action')} {(report['latest_run'] or {}).get('status')} |",
             f"| 门禁 | {report['gate_status']}（失败阶段 {report['failed_stage']}） |",
             f"| 阻断项合计 | {report['blocking_total']} |",
             f"| 阻断项分类 | {json.dumps(report['blocking'], ensure_ascii=False)} |",
             f"| 观察项（不阻断） | {json.dumps(report['observations'], ensure_ascii=False)} |",
             f"| lint | {report['lint']['status']}，违规 {report['lint']['findings']}，"
             f"例外 {len(report['lint']['suppressed'])} |",
             f"| 排除 | {len(report['exclusions'])} 项，面积占比 {report['excluded_fraction']} |",
             f"| 生成 | unsupported {report['generation']['unsupported']}，issues "
             f"{report['generation']['issues']}，scene {dict(report['generation']['scene_obligations'])} |",
             f"| 轮次 / 验证次数 | {report['rounds']} / {report['validation_attempts']} |",
             f"| 墙钟（start 起） | {report['elapsed_seconds']} 秒 |",
             f"| token | {report['tokens']} |", '']
    if report['geometry_failures']:
        lines += ['## 几何失败', '', '| 节点 | 偏差 |', '|---|---|']
        lines += [f"| {f['label']} | {'；'.join(f['failures'])} |" for f in report['geometry_failures']]
        lines.append('')
    if report['pixel_failures']:
        lines += ['## 像素 / 特征 / 关系 / 颜色失败', '', '| 检查 | 标签 | 原因 |', '|---|---|---|']
        lines += [f"| {f['check']} | {f['label']} | {f['failures']} |" for f in report['pixel_failures']]
        lines.append('')
    if report['responsive_findings']:
        lines += ['## 多尺寸', '', '| 变体 | 类型 | 说明 |', '|---|---|---|']
        lines += [f"| {f.get('variant')} | {f['kind']} | {f['message']} |"
                  for f in report['responsive_findings']]
        lines.append('')
    lines.append(report['note'])
    return '\n'.join(lines) + '\n'


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--output', type=Path, help='Write Markdown here (JSON goes to stdout)')
    args = parser.parse_args()
    report = build(args.config)
    if args.output:
        args.output.write_text(markdown(report), encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False, indent=2, default=dict))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
