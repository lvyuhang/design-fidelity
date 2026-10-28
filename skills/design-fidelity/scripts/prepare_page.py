#!/usr/bin/env python3
"""Prepare source-only page facts before coding; never declare visual acceptance."""
from __future__ import annotations

import argparse
import os
from collections import Counter
import json
from pathlib import Path
import time

from PIL import Image
from fontTools.ttLib import TTFont
from fidelity_contract import inventory, read_json, sha256
from init_visual_contract import visual_hints
from source_requirements import requirements, source_gaps, enabled
from visual_fidelity_gate import _load_nodes, _validate_evidence
from scene_requirements import scene_requirements
from source_disposition import source_disposition
from system_chrome import chrome_members, detect_system_chrome


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
            path = (base/Path(os.path.expandvars(font['path'])).expanduser()).resolve()
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


def compact_style(value):
    """Remove redundant serialization, not visual parameters."""
    if isinstance(value, list):
        return [compact_style(v) for v in value]
    if not isinstance(value, dict):
        return value
    result = {k: compact_style(v) for k, v in value.items()}
    if {'r','g','b','a'} <= value.keys():
        result.pop('value', None)  # Duplicate rgba(...) string.
    if value.get('type') in ('color','gradient') and value.get('noiseIntensity',0) == 0:
        for key in ('patternTileScale','patternFillType','noiseIntensity','noiseIndex'):
            result.pop(key, None)  # Not used for non-pattern, noise-free paints.
    return result


def implementation_brief(result, nodes):
    """Return the compact facts needed to start implementation.

    The complete page plan remains authoritative.  This view removes repeated
    style payloads while retaining every text/asset instance and its geometry.
    """
    text_groups = {}
    for entry in result['nodes']:
        if not entry.get('text'):
            continue
        styles = [{k: v for k, v in run.items() if k != 'text'}
                  for run in entry.get('runs', [])]
        signature = json.dumps(styles, ensure_ascii=False, sort_keys=True)
        group = text_groups.setdefault(signature, {'styles': styles, 'instances': []})
        group['instances'].append({'node_id': entry['node_id'], 'text': entry['text'],
                                   'parent_id': nodes[entry['node_id']].get('parent_id'),
                                   'source_order': nodes[entry['node_id']].get('source_order'),
                                   'rect': entry['layout_rect']})

    missing = []
    for entry in result['nodes']:
        if entry['proposal'] != 'missing_bitmap':
            continue
        node = nodes[entry['node_id']]
        style = node.get('raw_style') or {}
        w, h = entry['layout_rect'][2:]
        radius = style.get('borderRadius', style.get('border_radius', style.get('radius')))
        shape = 'circle_candidate' if abs(w-h) < .01 and radius in ('50%', '50') else (
            'rounded_rect_candidate' if radius not in (None, 0, '0') else 'shape_review_required')
        missing.append({'node_id': entry['node_id'], 'name': entry.get('name'),
                        'rect': entry['layout_rect'], 'shape_hint': shape,
                        'replace_scope': 'content_only; preserve scene dependencies'})

    # Deduplicate appearance, never discard a node because it is small. Text
    # appearance stays in text_style_groups; layer effects remain here too.
    visual_groups = {}
    chrome_ids = {e['node_id'] for e in result['nodes'] if e['proposal'] == 'system_chrome'}
    for key, node in inventory(nodes).items():
        if key in chrome_ids:
            continue  # Reserved OS chrome: listed separately, never implemented.
        raw = node.get('raw_style') or {}
        style = {}
        for field in ('fills', 'borders', 'shadow', 'shadows', 'innerShadows', 'blur', 'effects'):
            value = raw.get(field)
            if isinstance(value, list):
                value = [item for item in value if enabled(item)]
            if value:
                style[field] = value
        for field in ('opacity', 'radius', 'borderRadius', 'border_radius',
                      'hasClippingMask', 'clippingMaskMode', 'rotation', 'blendMode',
                      'isFlippedHorizontal', 'isFlippedVertical', 'booleanOperation',
                      'windingRule', 'isClosed', 'breaksMaskChain'):
            if field in raw:
                style[field] = raw[field]
        if node.get('text') and not effects_for_brief(style):
            continue
        # Paths are read only when needed. These references are explicit work,
        # not permission to replace an unexported vector with a familiar icon.
        geometry = 'export_frame' if node.get('asset_ids') else (
            'source_path' if raw.get('points') else node.get('node_type'))
        style = compact_style(style)
        style['geometry'] = geometry
        signature = json.dumps(style, ensure_ascii=False, sort_keys=True)
        group = visual_groups.setdefault(signature, {'style': style, 'instances': []})
        instance = {'node_id': key, 'parent_id': node.get('parent_id'),
                    'source_order': node.get('source_order'),
                    'rect': rect(node['bounds'])}
        if geometry == 'source_path':
            instance['geometry_ref'] = 'raw_style.points'
        if all(k in raw for k in ('influenceLeft','influenceTop','influenceWidth','influenceHeight')):
            origin = raw.get('ddsOriginFrame') or {}
            if 'x' in origin and 'y' in origin:
                paint_rect = [
                    raw['influenceLeft'] - origin['x'] + node['bounds']['x'],
                    raw['influenceTop'] - origin['y'] + node['bounds']['y'],
                    raw['influenceWidth'], raw['influenceHeight']]
                if any(abs(a-b) > .001 for a,b in zip(paint_rect, instance['rect'])):
                    instance['paint_rect'] = paint_rect
        group['instances'].append(instance)
    brief_ids = {i['node_id'] for g in visual_groups.values() for i in g['instances']}
    brief_ids.update(i['node_id'] for g in text_groups.values() for i in g['instances'])
    brief_ids.update(chrome_ids)
    if brief_ids != set(inventory(nodes)):
        raise ValueError('Implementation brief lost source inventory nodes')

    issue_counts = dict(Counter(i['kind'] for i in result['issues']))
    return {
        'schema_version': 2,
        'scope': 'implementation input only; page-plan.json remains authoritative',
        'source': {'snapshot_id': result['snapshot_id'],
                   'resolved_version': result['resolved_version'],
                   'canvas': result['canvas'], 'render_scale': result['render_scale']},
        'blocking_issue_counts': issue_counts,
        'assets': [{k:v for k,v in a.items() if k in
                    ('node_id','kind','path','export_rect','export_frame_source','alpha_ink_rect')}
                   for a in result['assets']],
        'asset_coverage_candidates': [
            {k:v for k,v in entry.items() if k in
             ('node_id','proposal','asset_owner_candidate')}
            for entry in result.get('nodes', []) if entry.get('asset_owner_candidate')],
        'missing_bitmaps': missing,
        'system_chrome': result.get('system_chrome', []),
        'text_style_groups': list(text_groups.values()),
        'visual_style_groups': list(visual_groups.values()),
        'inventory_count': len(brief_ids),
        'effect_requirements': compact_effect_requirements(result['effect_requirements']),
        'scene_requirements': compact_scene_requirements(scene_requirements(nodes)),
        'fonts': [{k:v for k,v in f.items() if k not in ('sha256','node_ids')}
                  for f in result['fonts']],
        'full_plan': 'page-plan.json',
    }


def compact_scene_requirements(requirements):
    groups = {}
    for r in requirements:
        group = groups.setdefault(r['kind'], {'kind':r['kind'], 'verify':r['verify'], 'instances':[]})
        group['instances'].append({k:v for k,v in r.items() if k not in ('kind','verify')})
    return list(groups.values())


def effects_for_brief(style):
    return (style.get('opacity', 100) != 100 or style.get('hasClippingMask') or
            any(style.get(k) for k in ('borders','shadow','shadows','innerShadows','blur','effects')) or
            any(v.get('type') == 'gradient' for v in style.get('fills', [])))


def compact_effect_requirements(requirements):
    groups = {}
    for entry in requirements:
        common = {k:v for k,v in entry.items() if k not in ('node_id','samples')}
        signature = json.dumps(common, sort_keys=True)
        group = groups.setdefault(signature, {**common, 'node_ids': [], 'samples': {}})
        group['node_ids'].append(entry['node_id'])
        if entry['samples']:
            group['samples'][entry['node_id']] = entry['samples']
    return list(groups.values())


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
    issues = [{'kind': 'source_styles_missing', **g} for g in source_gaps(nodes, text_styles=True)]
    from evidence_schema import validate_set
    schema = validate_set(documents)
    schema_warnings = []
    for path, found in zip(evidence, schema['documents']):
        issues += [{'kind': 'evidence_schema', 'file': Path(path).name, **item}
                   for item in found if item['severity'] == 'error'][:20]
        schema_warnings += [{'file': Path(path).name, **item} for item in found if item['severity'] != 'error']
    issues += [{'kind': 'evidence_schema', **item} for item in schema['overall']]
    for key, node in inventory(nodes).items():
        for asset_id in node.get('asset_ids', []):
            if asset_id not in assets:
                issues.append({'kind': 'asset_spec_missing', 'node_id': key, 'asset_id': asset_id})
    prepared_assets = []
    for key, a in assets.items():
        item = {'asset_id': key, 'node_id': a['node_id'], 'kind':a.get('kind', 'unspecified'),
                'layout_rect': rect(nodes[a['node_id']]['bounds'])}
        e = exported.get(key)
        if not e and a.get('kind') == 'render_fallback':
            # Source metadata is retained, but unused fallback pixels are not a
            # prerequisite for native implementation or missing-source review.
            item.update(download_state='deferred', usable_for_implementation=False)
            prepared_assets.append(item)
            continue
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
        # Newer evidence supplies normalized render bounds. Use them only when
        # the source-canvas mapping and export dimensions corroborate the frame.
        owners = [d for d in documents if any(v.get('asset_id') == key for v in d.get('assets', []))]
        bounds = a.get('render_bounds') or {}
        verified_bounds = (all(d.get('coordinate_space') == 'source_canvas' and
                              d.get('coordinate_mapping', {}).get('verified') is True for d in owners)
                           and all(k in bounds for k in ('x','y','width','height'))
                           and all(k in source_size and abs(source_size[k]-bounds[k]) < .001
                                   for k in ('width','height')))
        frame = rect(bounds) if verified_bounds else (
            [point['x']-origin[0],point['y']-origin[1],source_size['width'],source_size['height']]
            if origin is not None and {'width','height'} <= source_size.keys() and {'x','y'} <= point.keys()
            else None)
        frame_source = 'verified_render_bounds' if verified_bounds else 'source_point_minus_origin'
        # Some exports include transparent padding around a small node and do
        # not have a trustworthy document origin. The node's source frame is
        # still sufficient when every owning document explicitly verifies the
        # source-canvas coordinate mapping.
        if frame is None and owners and all(
                d.get('coordinate_space') == 'source_canvas' and
                d.get('coordinate_mapping', {}).get('verified') is True for d in owners):
            raw = nodes[a['node_id']].get('raw_style') or {}
            local = raw.get('ddsOriginFrame') or {}
            if (all(k in source_size for k in ('width','height')) and
                    all(k in point for k in ('x','y')) and
                    all(k in local for k in ('x','y'))):
                layout = item['layout_rect']
                frame = [layout[0]+point['x']-local['x'],
                         layout[1]+point['y']-local['y'],
                         source_size['width'], source_size['height']]
                frame_source = 'source_point_relative_to_node_origin'
        # Corroborated node-local influence mapping is stronger than an unverified
        # document-origin offset (source_point may be in a different artboard space).
        if not verified_bounds:
            raw = nodes[a['node_id']].get('raw_style') or {}
            local = raw.get('ddsOriginFrame') or {}
            influence_keys = ('influenceLeft','influenceTop','influenceWidth','influenceHeight')
            if (all(k in raw for k in influence_keys) and all(k in local for k in ('x','y'))
                    and all(k in source_size for k in ('width','height'))
                    and abs(source_size['width']-raw['influenceWidth']) < .001
                    and abs(source_size['height']-raw['influenceHeight']) < .001):
                layout = item['layout_rect']
                frame = [raw['influenceLeft']-local['x']+layout[0],
                         raw['influenceTop']-local['y']+layout[1],
                         raw['influenceWidth'], raw['influenceHeight']]
                frame_source = 'source_size_verified_influence'
        if frame is not None and frame[2] > 0 and frame[3] > 0:
            dx, dy = pixels[0]/frame[2], pixels[1]/frame[3]
            if abs(dx-dy) > max(max(dx,dy)*.001, 1/min(frame[2:])):
                issues.append({'kind':'export_density_mismatch','asset_id':key})
                frame = None
            else:
                item['export_density'] = dx
        if frame is None:
            issues.append({'kind': 'export_frame_unresolved', 'asset_id': key})
        else:
            item['export_frame_source'] = frame_source
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
    asset_nodes = {a['node_id'] for a in prepared_assets if 'path' in a and a['kind'] != 'render_fallback'}
    node_plan, review = [], []
    chrome = chrome_members(nodes, canvas)
    for key, n in selected.items():
        if key in chrome:
            node_plan.append({'node_id': key, 'name': n.get('name'), 'node_type': n.get('node_type'),
                              'layout_rect': rect(n['bounds']), 'proposal': 'system_chrome',
                              'asset_owner_candidate': None,
                              'source_disposition': {'state': 'system_chrome',
                                                     'action': 'reserve_space_do_not_paint'},
                              'system_chrome': chrome[key]['kind'], 'chrome_owner': chrome[key]['node_id']})
            continue
        owner, parent, visited = None, n.get('parent_id'), {key}
        while parent in nodes:
            if parent in visited:
                raise ValueError('Source parent cycle')
            visited.add(parent)
            if parent in asset_nodes:
                owner = parent
                break
            parent = nodes[parent].get('parent_id')
        disposition = source_disposition(key, nodes)
        owner = owner or (disposition.get('source_node')
                          if disposition['state'] == 'ancestor_asset_candidate' else None)
        mode = ('original_asset' if key in asset_nodes else 'ancestor_asset_candidate' if owner
                else 'text' if n.get('text') else 'missing_bitmap'
                if disposition['state'] == 'missing_bitmap_candidate'
                else 'review_asset_export' if disposition['state'] == 'asset_candidate'
                else 'review_source_geometry')
        entry = {'node_id': key, 'name': n.get('name'), 'node_type': n.get('node_type'),
                 'layout_rect': rect(n['bounds']),
                 'proposal': mode, 'asset_owner_candidate': owner,
                 'source_disposition': disposition}
        if n.get('text'):
            entry['text'] = n['text']
            fields = ('text','font_family','font_size','font_weight','color','line_height','letter_spacing')
            entry['runs'] = [{k:r.get(k) for k in fields} for r in (n.get('text_spec') or {}).get('text_runs', [])]
        node_plan.append(entry)
        if mode not in ('original_asset', 'text'):
            review.append({'node_id': key, 'kind': mode, 'owner_candidate': owner})
    review_groups = {}
    for entry in node_plan:
        # Group only review work; every instance retains its own geometry and
        # obligation checks. Different text widths still need per-node review.
        styles = [{k:v for k,v in run.items() if k != 'text'} for run in entry.get('runs', [])]
        signature = json.dumps([entry['proposal'], entry['asset_owner_candidate'], styles], sort_keys=True)
        group = review_groups.setdefault(signature, {'proposal':entry['proposal'],
            'owner_candidate':entry['asset_owner_candidate'], 'styles':styles, 'node_ids':[]})
        group['node_ids'].append(entry['node_id'])
    effects = [{'node_id': key, **visual_hints(n)} for key,n in nodes.items()
               if n.get('effective_source_visible',n.get('source_visible')) is not False and visual_hints(n)['effect_fields']]
    pins = {str(p.resolve()): sha256(p) for p in [*evidence, reference, manifest_path, *([font_map] if font_map else [])]}
    return {'status': 'NEEDS_INPUT_FIXES' if issues else 'PREPARED_FOR_REVIEW',
            'scope': 'source preparation only; proposals are not approved implementation or visual acceptance',
            'snapshot_id': first['snapshot_id'], 'resolved_version': first['resolved_version'],
            'canvas': canvas, 'render_scale': scale, 'source_nodes': len(nodes),
            'export_origin': origin, 'origin_anchor_nodes': anchors,
            'evidence_schema_warnings': {'count': len(schema_warnings), 'sample': schema_warnings[:10]},
            'assets': prepared_assets, 'fonts': fonts, 'nodes': node_plan,
            'effect_requirements': requirements(nodes, canvas), 'effect_candidates': effects,
            'review_queue': review, 'review_groups':list(review_groups.values()),
            'system_chrome': [{k: v for k, v in e.items() if k != 'members'}
                              for e in detect_system_chrome(nodes, canvas)],
            'issues': issues, 'pinned_inputs': pins}


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
    if result.get('status') in ('PREPARED_FOR_REVIEW', 'NEEDS_INPUT_FIXES'):
        nodes = _load_nodes(a.evidence)
        brief = implementation_brief(result, nodes)
        (a.output/'implementation-brief.json').write_text(
            json.dumps(brief, ensure_ascii=False, separators=(',', ':'))+'\n')
    else:
        brief = {}
    summary = {k:result[k] for k in ('status','scope','canvas','source_nodes','seconds','error') if k in result}
    summary.update(asset_count=len(result.get('assets', [])),
                   issue_counts=dict(Counter(i['kind'] for i in result.get('issues', []))),
                   review_count=len(result.get('review_queue', [])), report=str(a.output/'page-plan.json'))
    summary['review_group_count'] = len(result.get('review_groups', []))
    summary.update(brief=str(a.output/'implementation-brief.json') if brief else None,
                   missing_bitmap_count=len(brief.get('missing_bitmaps', [])),
                   text_style_group_count=len(brief.get('text_style_groups', [])),
                   visual_style_group_count=len(brief.get('visual_style_groups', [])),
                   brief_inventory_count=brief.get('inventory_count'))
    (a.output/'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps(summary, ensure_ascii=False))
    return 0 if result['status'] == 'PREPARED_FOR_REVIEW' else 2


if __name__ == '__main__':
    raise SystemExit(main())
