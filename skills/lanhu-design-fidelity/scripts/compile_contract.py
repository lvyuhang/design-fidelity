#!/usr/bin/env python3
"""Compile reviewed checks into a frozen v2 contract without per-page Python."""
from __future__ import annotations
import argparse
import copy
import json
from pathlib import Path

from fidelity_contract import inventory, read_json, sha256, validate_contract, verify_files, verify_fonts
from visual_fidelity_gate import (_load_nodes, _validate_evidence, _union_bounds,
    _padded_roi, _measure_feature)
from source_requirements import add_sample_drafts


def expand_groups(c):
    """Expand reviewed templates, preserving an independent check per node."""
    for group_name, target, wrapped in (
        ('decision_groups', 'node_decisions', True),
        ('feature_groups', 'features', False),
    ):
        destination = c.setdefault(target, {})
        for name, group in c.pop(group_name, {}).items():
            ids = group.get('node_ids', [])
            if not ids or len(ids) != len(set(ids)):
                raise ValueError(f'{group_name}.{name}: unique explicit node_ids required')
            template = group['decision'] if wrapped else {k:v for k,v in group.items() if k != 'node_ids'}
            for node_id in ids:
                key = node_id if wrapped else f'{name}__{node_id}'
                if key in destination:
                    raise ValueError(f'{group_name}.{name}: duplicate binding {key}')
                destination[key] = copy.deepcopy(template)
                if not wrapped:
                    destination[key]['node_ids'] = [node_id]


def check_reference_detectors(c, nodes, base):
    """Source-only check before freezing: no candidate pixels or threshold tuning."""
    import numpy as np
    from PIL import Image
    with Image.open(base/c['reference']) as im:
        expected = tuple(round(v*c['render_scale']) for v in c['canvas'])
        if im.size != expected:
            raise ValueError('Reference dimensions differ from canvas/render_scale')
        reference = np.asarray(im.convert('RGB'))
    empty = []
    for key, feature in c['features'].items():
        roi = _padded_roi(_union_bounds(feature['node_ids'], nodes),
                          feature.get('padding', [0, 0, 0, 0]))
        if _measure_feature(reference, roi, c['render_scale'], feature['detector']) is None:
            empty.append(key)
    if empty:
        raise ValueError('Reference detectors found no ink; review occlusion/target layer before render: '
                         + ', '.join(empty))


def check_raster_scope(c, nodes):
    """Reject text-bearing UI crops; a decorative glyph needs explicit review."""
    text_owners = set()
    for key, node in nodes.items():
        if not node.get('text'):
            continue
        seen = set()
        while key in nodes and key not in seen:
            seen.add(key)
            text_owners.add(key)
            key = nodes[key].get('parent_id')
    for key, decision in c.get('node_decisions', {}).items():
        if decision.get('mode') != 'render_fallback':
            continue
        if key in text_owners and not decision.get('static_artwork_reason', '').strip():
            raise ValueError(f'{key}: render_fallback contains text/UI; use native widgets and '
                             'individual missing-asset placeholders. Static decorative artwork '
                             'requires an explicit static_artwork_reason, never business labels.')


def compile_spec(spec, base):
    c = copy.deepcopy(spec)
    expand_groups(c)
    if any(k in c for k in ('coverage','pinned_files','status')):
        raise ValueError('Spec must omit generated coverage, pinned_files and status')
    exclusions = c.pop('excluded_nodes', {})
    paths = [base/p for p in c['source_documents']]
    _validate_evidence(paths, c)
    nodes = _load_nodes(paths)
    check_raster_scope(c, nodes)
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
    check_reference_detectors(c, nodes, base)
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
