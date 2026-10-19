#!/usr/bin/env python3
"""Prepare source-only page facts before coding; never declare visual acceptance."""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import time

from PIL import Image
from fontTools.ttLib import TTFont
from fidelity_contract import inventory, read_json, sha256
from init_visual_contract import visual_hints
from preflight import style_gaps
from visual_fidelity_gate import _load_nodes, _validate_evidence


def rect(bounds):
    return [bounds[k] for k in ('x', 'y', 'width', 'height')]


def export_origin(nodes, canvas):
    # Only full-canvas anchors establish the export coordinate origin. Tiny
    # glyphs may have different glyph/advance frames and are not safe anchors.
    anchors = []
    for key, n in nodes.items():
        b, f = n.get('bounds', {}), n.get('raw_style', {}).get('ddsOriginFrame', {})
        if not all(k in b and k in f for k in ('x', 'y', 'width', 'height')):
            continue
        if any(abs(b[k]-v) > .001 for k, v in zip(('x','y','width','height'), [0,0,*canvas])):
            continue
        if any(abs(f[k]-b[k]) > .001 for k in ('width','height')):
            continue
        anchors.append((key, (f['x']-b['x'], f['y']-b['y'])))
    offsets = {p for _, p in anchors}
    return (list(next(iter(offsets))) if len(offsets) == 1 else None,
            [key for key, _ in anchors])


def font_audit(nodes, mapping, base):
    """Check every source text run, including mixed fonts. Never choose fallback."""
    issues, requirements, cmaps = [], {}, {}
    for key, n in inventory(nodes).items():
        if not n.get('text'):
            continue
        spec = n.get('text_spec') or {}
        runs = spec.get('text_runs') or [dict(spec.get('base_style') or {}, text=n['text'])]
        if ''.join(r.get('text', '') for r in runs) != n['text']:
            issues.append({'kind': 'text_run_coverage', 'node_id': key})
        for run in runs:
            family = run.get('font_family')
            weight = run.get('font_weight')
            label = f'{family}@{weight}'
            entry = requirements.setdefault(label, {'source_family': family, 'weight': weight,
                                                     'node_ids': [], 'characters': set()})
            if key not in entry['node_ids']:
                entry['node_ids'].append(key)
            chars = {ch for ch in run.get('text', '') if not ch.isspace()}
            entry['characters'].update(chars)
            font = mapping.get('fonts', {}).get(label)
            if not font:
                issues.append({'kind': 'font_mapping_missing', 'node_id': key, 'font': label})
                continue
            path = (base/font['path']).resolve()
            identity = (str(path), font.get('font_number', 0))
            try:
                if identity not in cmaps:
                    with TTFont(path, fontNumber=identity[1]) as tt:
                        cmaps[identity] = set((tt.getBestCmap() or {}).keys())
                missing = ''.join(sorted(ch for ch in chars if ord(ch) not in cmaps[identity]))
                entry.update(path=str(path), sha256=sha256(path), runtime_family=font.get('runtime_family'))
                if missing:
                    issues.append({'kind': 'missing_glyphs', 'node_id': key, 'font': label,
                                   'characters': missing, 'path': str(path)})
            except (OSError, ValueError) as exc:
                issues.append({'kind': 'font_unreadable', 'node_id': key, 'error': str(exc)})
    for entry in requirements.values():
        entry['characters'] = ''.join(sorted(entry['characters']))
    return list(requirements.values()), issues


def prepare(evidence, reference, manifest_path, font_map=None):
    documents = [read_json(p) for p in evidence]
    first = documents[0]
    canvas = [first['canvas']['width'], first['canvas']['height']]
    _validate_evidence(evidence, {'canvas': canvas})
    nodes = _load_nodes(evidence)
    totals = {d.get('total_nodes', d.get('total')) for d in documents}
    if None in totals or len(totals) != 1 or next(iter(totals)) != len(nodes):
        raise ValueError('Incomplete/inconsistent page inventory; save all pagination results')
    manifest = read_json(manifest_path)
    for field in ('snapshot_id', 'resolved_version'):
        if manifest.get(field) != first.get(field):
            raise ValueError(f'Asset manifest {field} differs from source evidence')
    with Image.open(reference) as im:
        size = im.size
        im.verify()
    scale = size[0]/canvas[0]
    if abs(size[1]/canvas[1]-scale) > 1e-6:
        raise ValueError('Reference dimensions do not match source canvas')
    origin, anchors = export_origin(nodes, canvas)
    assets = {}
    for d in documents:
        for a in d.get('assets', []):
            key = a['asset_id']
            if key in assets and assets[key] != a:
                raise ValueError(f'Conflicting source asset: {key}')
            assets[key] = a
    exported = {a['asset_id']: a for a in manifest.get('assets', [])}
    issues = [{'kind': 'source_styles_missing', **g} for g in style_gaps(nodes)]
    for key, node in inventory(nodes).items():
        for asset_id in node.get('asset_ids', []):
            if asset_id not in assets:
                issues.append({'kind': 'asset_spec_missing', 'node_id': key, 'asset_id': asset_id})
    prepared_assets = []
    for key, a in assets.items():
        item = {'asset_id': key, 'node_id': a['node_id'],
                'layout_rect': rect(nodes[a['node_id']]['bounds'])}
        e = exported.get(key)
        if not e:
            issues.append({'kind': 'asset_not_exported', 'asset_id': key})
            prepared_assets.append(item)
            continue
        base = manifest_path.parent.resolve()
        path = (base/e['relative_path']).resolve()
        if base not in path.parents:
            raise ValueError('Asset path escapes manifest directory')
        if sha256(path) != e['sha256'] or path.stat().st_size != e['bytes']:
            raise ValueError(f'Asset bytes/hash mismatch: {key}')
        with Image.open(path) as im:
            pixels = im.size
            im.load()
            ink = im.convert('RGBA').getchannel('A').getbbox()
        if list(pixels) != [e['actual_pixel_size'][k] for k in ('width','height')]:
            raise ValueError(f'Asset dimensions mismatch: {key}')
        item.update(path=str(path), sha256=e['sha256'], pixel_size=list(pixels))
        source_size, point = a.get('source_size') or {}, a.get('source_point') or {}
        if origin is None or not {'width','height'} <= source_size.keys() or not {'x','y'} <= point.keys():
            issues.append({'kind': 'export_frame_unresolved', 'asset_id': key})
        else:
            frame = [point['x']-origin[0], point['y']-origin[1], source_size['width'], source_size['height']]
            if frame[2] <= 0 or frame[3] <= 0:
                raise ValueError(f'Invalid source export size: {key}')
            item['export_rect'] = frame
            item['layout_differs_from_export'] = any(abs(x-y) > .01 for x,y in zip(frame,item['layout_rect']))
            if ink:
                sx, sy = frame[2]/pixels[0], frame[3]/pixels[1]
                item['alpha_ink_rect'] = [frame[0]+ink[0]*sx, frame[1]+ink[1]*sy,
                                          (ink[2]-ink[0])*sx, (ink[3]-ink[1])*sy]
            if frame[0] < -1 or frame[1] < -1 or frame[0]+frame[2] > canvas[0]+1 or frame[1]+frame[3] > canvas[1]+1:
                issues.append({'kind': 'export_frame_outside_canvas', 'asset_id': key, 'rect': frame})
        prepared_assets.append(item)
    font_mapping = read_json(font_map) if font_map else {}
    fonts, font_issues = font_audit(nodes, font_mapping, font_map.parent if font_map else Path.cwd())
    issues.extend(font_issues)
    selected = inventory(nodes)
    asset_nodes = {a['node_id'] for a in prepared_assets if 'path' in a}
    node_plan, review = [], []
    for key, n in selected.items():
        owner, parent, visited = None, n.get('parent_id'), {key}
        while parent in nodes:
            if parent in visited:
                raise ValueError('Source parent cycle')
            visited.add(parent)
            if parent in asset_nodes:
                owner = parent
                break
            parent = nodes[parent].get('parent_id')
        mode = ('original_asset' if key in asset_nodes else 'ancestor_asset_candidate' if owner
                else 'text' if n.get('text') else 'missing_bitmap' if n.get('node_type') == 'bitmap'
                else 'review_source_geometry')
        entry = {'node_id': key, 'name': n.get('name'), 'layout_rect': rect(n['bounds']),
                 'proposal': mode, 'asset_owner_candidate': owner}
        if n.get('text'):
            entry['text'] = n['text']
            fields = ('text','font_family','font_size','font_weight','color','line_height','letter_spacing')
            entry['runs'] = [{k:r.get(k) for k in fields} for r in (n.get('text_spec') or {}).get('text_runs', [])]
        node_plan.append(entry)
        if mode in ('ancestor_asset_candidate','missing_bitmap','review_source_geometry'):
            review.append({'node_id': key, 'kind': mode, 'owner_candidate': owner})
    effects = [{'node_id': key, **visual_hints(n)} for key,n in nodes.items()
               if n.get('effective_source_visible',n.get('source_visible')) is not False and visual_hints(n)['effect_fields']]
    pins = {str(p.resolve()): sha256(p) for p in [*evidence, reference, manifest_path, *([font_map] if font_map else [])]}
    return {'status': 'NEEDS_INPUT_FIXES' if issues else 'PREPARED_FOR_REVIEW',
            'scope': 'source preparation only; proposals are not approved implementation or visual acceptance',
            'snapshot_id': first['snapshot_id'], 'resolved_version': first['resolved_version'],
            'canvas': canvas, 'render_scale': scale, 'source_nodes': len(nodes),
            'export_origin': origin, 'origin_anchor_nodes': anchors,
            'assets': prepared_assets, 'fonts': fonts, 'nodes': node_plan,
            'effect_candidates': effects, 'review_queue': review, 'issues': issues, 'pinned_inputs': pins}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--evidence', action='append', type=Path, required=True)
    p.add_argument('--reference', type=Path, required=True)
    p.add_argument('--manifest', type=Path, required=True)
    p.add_argument('--font-map', type=Path)
    p.add_argument('--output', type=Path, required=True, help='New directory; preserves prior runs')
    a = p.parse_args()
    a.output.mkdir(parents=True, exist_ok=False)
    start = time.monotonic()
    try:
        result = prepare(a.evidence, a.reference, a.manifest, a.font_map)
    except (ValueError, OSError, KeyError) as exc:
        result = {'status':'NOT_PREPARED', 'error':str(exc)}
    result['seconds'] = round(time.monotonic()-start, 4)
    (a.output/'page-plan.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n')
    summary = {k:result[k] for k in ('status','scope','canvas','source_nodes','seconds','error') if k in result}
    summary.update(asset_count=len(result.get('assets', [])),
                   issue_counts=dict(Counter(i['kind'] for i in result.get('issues', []))),
                   review_count=len(result.get('review_queue', [])), report=str(a.output/'page-plan.json'))
    (a.output/'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps(summary, ensure_ascii=False))
    return 0 if result['status'] == 'PREPARED_FOR_REVIEW' else 2


if __name__ == '__main__':
    raise SystemExit(main())
