#!/usr/bin/env python3
"""Compile reviewed checks into a frozen v2 contract without per-page Python."""
from __future__ import annotations
import argparse
import copy
import json
from pathlib import Path

from fidelity_contract import inventory, read_json, sha256, validate_contract, verify_files, verify_fonts
from visual_fidelity_gate import _load_nodes, _validate_evidence
from source_requirements import add_sample_drafts


def compile_spec(spec, base):
    c = copy.deepcopy(spec)
    if any(k in c for k in ('coverage','pinned_files','status')):
        raise ValueError('Spec must omit generated coverage, pinned_files and status')
    exclusions = c.pop('excluded_nodes', {})
    paths = [base/p for p in c['source_documents']]
    _validate_evidence(paths, c)
    nodes = _load_nodes(paths)
    c["workflow_version"] = 1
    auto = c.pop("auto_effect_samples", None)
    if auto is not None:
        add_sample_drafts(c, nodes, auto["max_channel_delta"])
    selected = inventory(nodes)
    if set(exclusions)-set(selected):
        raise ValueError('Exclusion references unknown/non-inventory node')
    coverage = {}
    for key in selected:
        checks = [f'{group}.{name}' for group in ('regions','features','relations','color_samples')
                  for name,check in c.get(group,{}).items()
                  if check.get('blocking',True) and key in check.get('node_ids',[])]
        if key in exclusions:
            if checks:
                raise ValueError(f'Node both checked and excluded: {key}')
            if not isinstance(exclusions[key], str) or not exclusions[key].strip():
                raise ValueError(f'Exclusion needs reason: {key}')
            coverage[key] = {'status':'excluded','checks':[], 'reason':exclusions[key]}
        else:
            coverage[key] = {'status':'covered' if checks else 'pending', 'checks':checks, 'reason':''}
    c['coverage'] = coverage
    c['status'] = 'ready'
    validate_contract(c, nodes)  # No blanket whole-page coverage, defaults or silent exclusions.
    required = {c['reference'],*c['source_documents'],*c.get('assets',[]),
                *(f['path'] for f in c.get('fonts',[]))}
    c['pinned_files'] = {p:sha256(base/p) for p in sorted(required)}
    verify_files(c, base)
    verify_fonts(c, nodes, base)
    return c


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--spec', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    if a.output.exists():
        p.error('Output exists; never overwrite a frozen baseline')
    if a.output.resolve().parent != a.spec.resolve().parent:
        p.error('Spec and contract must share a directory so relative paths remain unchanged')
    try:
        c = compile_spec(read_json(a.spec), a.spec.resolve().parent)
        a.output.write_text(json.dumps(c,ensure_ascii=False,indent=2)+'\n')
        print(json.dumps({'status':'CONTRACT_COMPILED','visual_acceptance':False,
                          'nodes':len(c['coverage']),'contract':str(a.output)},ensure_ascii=False))
        return 0
    except (ValueError,OSError,KeyError) as exc:
        print(json.dumps({'status':'NEEDS_REVIEW','error':str(exc)},ensure_ascii=False))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
