#!/usr/bin/env python3
"""Generate a deterministic first implementation from canonical design evidence.

  --target flutter   Dart on the lanhu_fidelity primitives (Flutter)
  --target react     TSX on @design-fidelity/react (Web)
  --target compose   Kotlin on the fidelity Compose primitives (Android)
  --target swiftui   Swift on the fidelity SwiftUI primitives (iOS)

Every visual parameter comes from the saved source nodes (Lanhu or Figma) and
the prepare plan; nothing is inferred from screenshots or chosen by a model.
The scene model (`scene_model.py`) makes all platform-independent decisions;
emitters only translate. The report lists, per visible node, how it was
rendered (draft `node_decisions`), unsupported features, system chrome and
font or asset gaps. It never grants visual acceptance.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import re
import shutil
from pathlib import Path

from fidelity_contract import read_json
from scene_model import SceneModel
from visual_fidelity_gate import _load_nodes, _validate_evidence

TARGETS = {
    'flutter': ('emit_flutter', ('ios', 'android')),
    'react': ('emit_react', ('web',)),
    'compose': ('emit_compose', ('android',)),
    'swiftui': ('emit_swiftui', ('ios',)),
}


def generate(evidence: list[Path], plan_path: Path | None, font_map_path: Path | None,
             class_name: str, output: Path, report_path: Path | None = None,
             app_root: Path | None = None, asset_dir: str | None = None,
             scene_test: Path | None = None, render_test: Path | None = None,
             output_env: str | None = None, target: str = 'flutter', options: dict | None = None) -> dict:
    if target not in TARGETS:
        raise ValueError(f'unknown target {target}; choose from {", ".join(TARGETS)}')
    if not re.fullmatch(r'[A-Z][A-Za-z0-9]*', class_name):
        raise ValueError('class name must be UpperCamelCase')
    documents = [read_json(p) for p in evidence]
    first = documents[0]
    canvas = [first['canvas']['width'], first['canvas']['height']]
    _validate_evidence(evidence, {'canvas': canvas})
    nodes = _load_nodes(evidence)
    plan = read_json(plan_path) if plan_path else None
    if plan:
        for field in ('snapshot_id', 'resolved_version'):
            if plan.get(field) != first.get(field):
                raise ValueError(f'Plan {field} differs from evidence; re-run prepare')
    font_map = read_json(font_map_path) if font_map_path else {}
    implementation = output.name
    if app_root is not None:
        try:
            implementation = str(output.resolve().relative_to(app_root.resolve()))
        except ValueError:
            implementation = str(output)
    module_name, platforms = TARGETS[target]
    module = importlib.import_module(module_name)
    model = SceneModel(nodes, documents, plan, font_map, class_name, asset_dir,
                       implementation, font_platforms=platforms)
    result = module.emit(model, {'output': output, 'app_root': app_root, 'scene_test': scene_test,
                                 'render_test': render_test, 'output_env': output_env,
                                 'font_map': font_map_path, 'options': options or {}})
    code, report, asset_field = result['code'], result['report'], result['asset_field']
    if app_root is not None and asset_dir:
        for entry in report['assets']:
            target_path = (app_root / entry[asset_field]).resolve()
            if app_root.resolve() not in target_path.parents:
                raise ValueError('Asset target escapes app root')
            target_path.parent.mkdir(parents=True, exist_ok=True)
            source = Path(entry['source'])
            digest = hashlib.sha256(source.read_bytes()).hexdigest()
            if entry.get('sha256') and digest != entry['sha256']:
                raise ValueError(f'Asset hash changed since prepare: {source}')
            if not target_path.exists() or hashlib.sha256(target_path.read_bytes()).hexdigest() != digest:
                shutil.copyfile(source, target_path)
            entry['installed'] = str(target_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(code, encoding='utf-8')
    report['output'] = str(output)
    report['output_sha256'] = hashlib.sha256(code.encode('utf-8')).hexdigest()
    if target != 'flutter':
        report['target'] = target
    report_path = report_path or module.default_report_path(output)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    report['report'] = str(report_path)
    return report


def main(default_target: str | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--target', choices=sorted(TARGETS), default=default_target or 'flutter')
    parser.add_argument('--evidence', type=Path, action='append', required=True)
    parser.add_argument('--plan', type=Path, help='page-plan.json from prepare (assets, fonts)')
    parser.add_argument('--font-map', type=Path)
    parser.add_argument('--class-name', required=True, help='UpperCamelCase page name, e.g. Withdraw2')
    parser.add_argument('--output', type=Path, required=True, help='Generated source file')
    parser.add_argument('--report', type=Path)
    parser.add_argument('--app-root', type=Path, help='App root; enables asset install')
    parser.add_argument('--asset-dir', help='Asset directory relative to app root')
    parser.add_argument('--scene-test', type=Path, help='Scene obligation test (Flutter)')
    parser.add_argument('--render-test', type=Path, help='Create this render test if missing (project-owned)')
    parser.add_argument('--output-env', help='Environment variable the render test writes the PNG to')
    parser.add_argument('--option', action='append', default=[], help='Target option KEY=VALUE')
    args = parser.parse_args()
    options = dict(item.split('=', 1) for item in args.option)
    report = generate(args.evidence, args.plan, args.font_map, args.class_name, args.output,
                      args.report, args.app_root, args.asset_dir, args.scene_test,
                      args.render_test, args.output_env, args.target, options)
    summary = {k: report[k] for k in ('status', 'mode_counts', 'output', 'report')}
    summary['unsupported'] = len(report['unsupported'])
    summary['issues'] = len(report['issues'])
    summary['system_chrome'] = [c['kind'] for c in report['system_chrome']]
    if report.get('scene_test'):
        obligations = report['scene_test']['obligations']
        summary['scene_obligations'] = {'bound': sum(o['status'] == 'bound' for o in obligations),
                                        'unsupported': [o['id'] for o in obligations if o['status'] != 'bound']}
    if report['assets'] and not args.asset_dir:
        summary['next_action'] = 'pass --app-root/--asset-dir to install assets into the app'
    print(json.dumps(summary, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
