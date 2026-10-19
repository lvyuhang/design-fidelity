#!/usr/bin/env python3
"""Reject Flutter-drawn icons that lack verifiable source provenance."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


CUSTOM_PAINT = re.compile(
    r'CustomPaint\s*\(\s*(?:key\s*:[^,]+,\s*)?painter\s*:\s*'
    r'(?:const\s+)?([A-Za-z_]\w*)\s*\(', re.S)
FRAMEWORK_ICON = re.compile(
    r'\bIcon\s*\(\s*((?:Icons|CupertinoIcons)\.[A-Za-z_]\w*)', re.S)


def _read(path: Path):
    return json.loads(path.read_text())


def _pointer(value, pointer):
    for token in pointer.strip('/').split('/') if pointer else []:
        token = token.replace('~1', '/').replace('~0', '~')
        value = value[int(token)] if isinstance(value, list) else value[token]
    return value


def _line(text, offset):
    return text.count('\n', 0, offset) + 1


def findings(paths, root):
    result = []
    for path in paths:
        text = path.read_text(errors='replace')
        try:
            rel = str(path.resolve().relative_to(root.resolve()))
        except ValueError:
            rel = str(path.resolve())
        for match in CUSTOM_PAINT.finditer(text):
            symbol = match.group(1)
            result.append({'id': f'{rel}::custom_paint::{symbol}', 'file': rel,
                           'line': _line(text, match.start()), 'kind': 'custom_paint',
                           'symbol': symbol})
        for match in FRAMEWORK_ICON.finditer(text):
            symbol = match.group(1)
            result.append({'id': f'{rel}::framework_icon::{symbol}', 'file': rel,
                           'line': _line(text, match.start()), 'kind': 'framework_icon',
                           'symbol': symbol})
    return result


def _node_index(documents):
    result = {}
    for document in documents:
        for node in _read(document).get('nodes', []):
            if node.get('node_id'):
                result[node['node_id']] = node
    return result


def audit(paths, root, provenance=None, evidence=()):
    found = findings(paths, root)
    bindings = (provenance or {}).get('bindings', {})
    nodes = _node_index(evidence)
    failures = []
    for item in found:
        binding = bindings.get(item['id'])
        if not binding:
            failures.append({**item, 'reason': 'missing provenance binding'})
            continue
        mode = binding.get('mode')
        if mode == 'system_chrome':
            if not binding.get('reason', '').strip():
                failures.append({**item, 'reason': 'system_chrome requires reason'})
        elif mode == 'source_vector':
            refs = binding.get('source_nodes') or []
            if not refs:
                failures.append({**item, 'reason': 'source_vector requires source_nodes'})
                continue
            for ref in refs:
                node = nodes.get(ref.get('node_id'))
                pointer = ref.get('pointer', '')
                try:
                    value = _pointer(node, pointer) if node is not None else None
                except (KeyError, IndexError, TypeError, ValueError):
                    value = None
                if not value:
                    failures.append({**item, 'reason':
                        f'unresolved geometry {ref.get("node_id")}#{pointer}'})
        else:
            failures.append({**item, 'reason':
                'mode must be source_vector or system_chrome; missing custom icons use placeholders'})
    stale = sorted(set(bindings) - {item['id'] for item in found})
    if stale:
        failures.append({'reason': 'stale provenance bindings', 'ids': stale})
    return {'status': 'PASS' if not failures else 'FAIL', 'findings': found,
            'failures': failures, 'checked_files': [str(p) for p in paths]}


def audit_contract(contract_path: Path):
    contract = _read(contract_path)
    base = contract_path.resolve().parent
    paths = [(base / p).resolve() for p in contract.get('implementation_inputs', [])
             if str(p).endswith('.dart')]
    provenance_path = contract.get('graphics_provenance')
    provenance = _read(base / provenance_path) if provenance_path else None
    evidence = [(base / p).resolve() for p in contract.get('source_documents', [])]
    return audit(paths, base, provenance, evidence)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--contract', type=Path)
    p.add_argument('--source', type=Path, action='append', default=[])
    p.add_argument('--root', type=Path, default=Path.cwd())
    p.add_argument('--provenance', type=Path)
    p.add_argument('--evidence', type=Path, action='append', default=[])
    p.add_argument('--output', type=Path)
    a = p.parse_args()
    if bool(a.contract) == bool(a.source):
        p.error('use exactly one of --contract or --source')
    result = (audit_contract(a.contract.resolve()) if a.contract else
              audit([x.resolve() for x in a.source], a.root.resolve(),
                    _read(a.provenance) if a.provenance else None,
                    [x.resolve() for x in a.evidence]))
    if a.output:
        a.output.parent.mkdir(parents=True, exist_ok=True)
        a.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result['status'] == 'PASS' else 2


if __name__ == '__main__':
    raise SystemExit(main())
