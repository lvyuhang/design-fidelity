#!/usr/bin/env python3
"""Merge prepare's draft checks with codegen decisions into a compilable spec.

The model should review exceptions, not hand-type hundreds of node IDs. This
tool combines: the source-derived checks from `init_visual_contract`, the
per-node implementation decisions from `generate_flutter`, the asset/font
pins from prepare, system-chrome exclusions, and a per-node region for any
visible node no other check covers. It then runs the real compiler and
reports what still needs a human decision. It never edits thresholds of an
existing spec and never writes the frozen contract.
"""
from __future__ import annotations

import argparse
import copy
import json
import os
from pathlib import Path

import numpy as np
from PIL import Image

from compile_contract import compile_spec
from fidelity_contract import inventory, read_json, sha256
from source_requirements import is_small_visual, requirements
from system_chrome import chrome_members
from visual_fidelity_gate import _load_nodes

DEFAULT_NODE_REGION = {'max_mae': 6.0, 'max_p95': 40.0}
GENERATED_FIELDS = ('coverage', 'status', 'pinned_files')


def rel(path: Path, base: Path, home_relative: bool = False) -> str:
    """Path relative to `base`; per-user files (e.g. design fonts under
    ~/.design-fidelity) are written as ~/... so the spec works on every machine."""
    resolved = Path(path).expanduser().resolve()
    if home_relative:
        home = Path.home().resolve()
        if home in resolved.parents:
            return '~/' + resolved.relative_to(home).as_posix()
    return os.path.relpath(resolved, base.resolve())


def strip_nodes(spec: dict, removed: set[str]) -> list[str]:
    """Remove node IDs from every check; drop checks that become empty."""
    dropped = []
    for group in ('features', 'regions', 'color_samples'):
        for name in list(spec.get(group, {})):
            check = spec[group][name]
            ids = check.get('node_ids')
            if not ids:
                continue
            kept = [i for i in ids if i not in removed]
            if not kept and 'rect' not in check:
                del spec[group][name]
                dropped.append(f'{group}.{name}')
            else:
                check['node_ids'] = kept
            effect = check.get('effect') or {}
            if effect.get('node_id') in removed and name in spec.get(group, {}):
                del spec[group][name]
                dropped.append(f'{group}.{name}')
    for name in list(spec.get('relations', {})):
        if any(f not in spec.get('features', {}) for f in spec['relations'][name]['features']):
            del spec['relations'][name]
            dropped.append(f'relations.{name}')
    return dropped


def _solid_color(node: dict):
    """Opaque source fill/border colour of a small shape, if unambiguous."""
    from scene_model import parse_color
    raw = node.get('raw_style') or {}
    for field in ('fills', 'borders'):
        for paint in raw.get(field) or []:
            if not isinstance(paint, dict) or paint.get('isEnabled', True) is False:
                continue
            if paint.get('type', 'color') != 'color':
                continue
            color = parse_color(paint.get('color'))
            if color and color[3] >= 0.99 and float(paint.get('opacity', 1) or 1) >= 0.99:
                return list(color[:3])
    return None


def _reference_detector(reference: np.ndarray, roi: list[float], scale: float):
    """Foreground colour inside a reference ROI, separated from its own border."""
    x1, y1 = max(0, round(roi[0] * scale)), max(0, round(roi[1] * scale))
    x2 = min(reference.shape[1], round((roi[0] + roi[2]) * scale))
    y2 = min(reference.shape[0], round((roi[1] + roi[3]) * scale))
    crop = reference[y1:y2, x1:x2].astype(float)
    if crop.size == 0:
        return None
    edge = np.concatenate([crop[0], crop[-1], crop[:, 0], crop[:, -1]])
    background = np.median(edge, axis=0)
    distance = np.linalg.norm(crop - background, axis=2)
    foreground = crop[distance > 40]
    if len(foreground) < 2:
        return None
    rgb = [int(v) for v in np.median(foreground, axis=0)]
    gap = float(np.linalg.norm(np.asarray(rgb) - background))
    return {'kind': 'color_distance', 'rgb': rgb,
            'max_distance': round(max(24.0, min(64.0, gap / 2)), 1), 'min_pixels': 1}


def resolve_review_detectors(spec: dict, nodes: dict, spec_dir: Path) -> list[str]:
    """Replace `review_required` detectors from source colour or the reference."""
    resolved = []
    reference = None
    for name, check in spec.get('features', {}).items():
        detector = check.get('detector') or {}
        if detector.get('kind') != 'review_required':
            continue
        key = check['node_ids'][0]
        color = _solid_color(nodes[key])
        if color:
            check['detector'] = {'kind': 'color_distance', 'rgb': color, 'max_distance': 40,
                                 'min_pixels': detector.get('min_pixels', 1)}
            resolved.append(f'{name}: source colour')
            continue
        if reference is None:
            reference = np.asarray(Image.open(spec_dir / spec['reference']).convert('RGB'))
        b = nodes[key]['bounds']
        pad = check.get('padding', [1, 1, 1, 1])
        roi = [b['x'] - pad[0], b['y'] - pad[1], b['width'] + pad[0] + pad[2], b['height'] + pad[1] + pad[3]]
        derived = _reference_detector(reference, roi, float(spec['render_scale']))
        if derived:
            check['detector'] = derived
            check['review_reason'] = 'auto: foreground colour from the reference ROI; confirm segmentation'
            resolved.append(f'{name}: reference ROI')
    return resolved


def auto_relations(spec: dict, nodes: dict, limit: int = 40) -> list[str]:
    """Chain features that share a source baseline row or left column."""
    if spec.get('relations'):
        return []
    entries = []
    for name, check in spec.get('features', {}).items():
        if len(check.get('node_ids', [])) != 1 or not check.get('blocking', True):
            continue
        b = nodes[check['node_ids'][0]]['bounds']
        entries.append((name, b['x'], b['y'] + b['height'] / 2))
    added = []
    for metric, index in (('center_y', 2), ('left', 1)):
        buckets: dict[float, list] = {}
        for entry in entries:
            buckets.setdefault(round(entry[index] * 2) / 2, []).append(entry)
        for value, members in sorted(buckets.items()):
            members.sort(key=lambda e: e[1] if metric == 'center_y' else e[2])
            for first, second in zip(members, members[1:]):
                if len(added) >= limit:
                    break
                name = f'{metric}__{first[0]}__{second[0]}'
                spec.setdefault('relations', {})[name] = {
                    'label': f'{metric} aligned', 'features': [first[0], second[0]],
                    'metric': metric, 'max_delta': 1.0}
                added.append(name)
    if not added:
        spec.setdefault('not_applicable', {})['relations'] = 'no source row/column alignment between features'
    return added


def effect_regions(spec: dict, nodes: dict, skip: set[str]) -> list[str]:
    """Local region per source effect that has no automatic sample positions."""
    added = []
    for req in requirements(nodes, spec['canvas']):
        key, effect_key = req['node_id'], req['effect_key']
        if key in skip or req['samples']:
            continue
        if req['kind'] == 'backdrop' or effect_key == 'mask':
            continue  # Proven by the generated scene check.
        b = nodes[key]['bounds']
        raw = nodes[key].get('raw_style') or {}
        grow = 1.0
        if effect_key.startswith('borders'):
            grow += max([float(x.get('thickness') or 0) for x in raw.get('borders') or [] if isinstance(x, dict)] or [0])
        if effect_key.startswith(('shadow', 'shadows')):
            shadows = [x for x in raw.get('shadow') or [] if isinstance(x, dict)]
            grow += max([float(x.get('blurRadius') or 0) * 1.5 + abs(float(x.get('spread') or 0))
                         + max(abs(float(x.get('offsetX') or 0)), abs(float(x.get('offsetY') or 0)))
                         for x in shadows] or [0])
        rect = [max(0.0, b['x'] - grow), max(0.0, b['y'] - grow)]
        rect += [min(spec['canvas'][0], b['x'] + b['width'] + grow) - rect[0],
                 min(spec['canvas'][1], b['y'] + b['height'] + grow) - rect[1]]
        name = f"effect_region__{key}__{effect_key.replace(':', '_')}"
        region = {'label': f"{nodes[key].get('name') or key} {effect_key}", 'node_ids': [key],
                  'rect': [round(v, 3) for v in rect], 'effect': {'node_id': key, 'key': effect_key},
                  'review_reason': 'auto: local region around the source effect extent; '
                                   'confirm it still fails when the effect is removed',
                  **DEFAULT_NODE_REGION}
        if effect_key.startswith('borders') and ':gradient' not in effect_key:
            region['comparison_profile'] = 'vector_effect'
        spec.setdefault('regions', {})[name] = region
        added.append(name)
    return added


def covered(spec: dict) -> set[str]:
    ids = set()
    for group in ('regions', 'features', 'color_samples'):
        for check in spec.get(group, {}).values():
            if check.get('blocking', True):
                ids.update(check.get('node_ids', []))
    return ids


def build(draft: dict, draft_dir: Path, codegen: dict, plan: dict | None, spec_dir: Path,
          app: Path, extra_inputs: list[Path], environment: dict) -> tuple[dict, dict]:
    spec = {k: copy.deepcopy(v) for k, v in draft.items() if k not in GENERATED_FIELDS}
    # Re-base draft-relative paths onto the spec directory.
    spec['reference'] = rel(draft_dir / draft['reference'], spec_dir)
    spec['source_documents'] = [rel(draft_dir / p, spec_dir) for p in draft['source_documents']]
    nodes = _load_nodes([spec_dir / p for p in spec['source_documents']])
    visible = inventory(nodes)
    chrome = chrome_members(nodes, spec['canvas'])
    review: dict[str, list] = {'auto_regions': [], 'dropped_checks': [], 'undecided_nodes': []}
    review['dropped_checks'] = strip_nodes(spec, set(chrome))

    generated = Path(codegen['output']).resolve()
    implementation = rel(generated, spec_dir)
    decisions = {}
    asset_paths = {}
    for entry in codegen.get('assets', []):
        app_asset = entry.get('app_asset') or entry['flutter_asset']
        asset_paths[app_asset] = rel(app / app_asset, spec_dir)
    for key, decision in codegen.get('draft_node_decisions', {}).items():
        decision = copy.deepcopy(decision)
        if decision.get('implementation'):
            decision['implementation'] = implementation
        if decision.get('asset'):
            decision['asset'] = asset_paths.get(decision['asset'], decision['asset'])
        decisions[key] = decision
    review['undecided_nodes'] = sorted(set(visible) - set(decisions))
    spec['node_decisions'] = decisions

    inputs = [implementation, *(rel(p, spec_dir) for p in extra_inputs)]
    scene = codegen.get('scene_test') or {}
    bound = [o['id'] for o in scene.get('obligations', []) if o['status'] == 'bound']
    review['unbound_obligations'] = [o['id'] for o in scene.get('obligations', []) if o['status'] != 'bound']
    if bound:
        test_file = Path(scene['test_file']).resolve()
        inputs.append(rel(test_file, spec_dir))
        command = ['flutter', 'test', '--no-pub', rel(test_file, app)]
        if codegen.get('target') == 'react':
            render = Path(codegen['render_test']['path']).resolve()
            command = ['node', rel(render.parent / 'support' / 'fidelity_render_harness.cjs', app),
                       rel(render, app), '--scene', rel(test_file, app)]
        spec['scene_checks'] = {'generated_scene': {
            'obligations': sorted(bound),
            'test_file': rel(test_file, spec_dir),
            'cwd': rel(app, spec_dir),
            'command': command,
            'timeout_seconds': 180,
            'assertions': 'Production scene binds each obligation to the verified design_fidelity primitive '
                          'with source parameters; stroke bands are rendered with/without the border to '
                          'prove position and no leakage; fill stacks are sampled against the source composite.'}}
    target = codegen.get('target', 'flutter')
    if target != 'flutter':
        spec['target'] = target
    manifests = {'flutter': ('pubspec.yaml', 'pubspec.lock'),
                 'react': ('package.json', 'package-lock.json', 'pnpm-lock.yaml', 'yarn.lock')}
    for name in manifests.get(target, ()):
        if (app / name).is_file():
            inputs.append(rel(app / name, spec_dir))
    spec['implementation_inputs'] = sorted(dict.fromkeys(inputs))
    spec['assets'] = sorted({d['asset'] for d in decisions.values() if d.get('asset')})

    fonts = {}
    for entry in (plan or {}).get('fonts', []):
        if not entry.get('path'):
            continue
        ids = [i for i in entry.get('node_ids', []) if i not in chrome]
        if ids:
            item = fonts.setdefault(entry['path'], {'path': rel(Path(entry['path']), spec_dir, True),
                                                    'node_ids': []})
            item['node_ids'] = sorted(set(item['node_ids']) | set(ids))
    spec['fonts'] = list(fonts.values())
    spec['environment'] = {**spec.get('environment', {}), **environment}

    review['resolved_detectors'] = resolve_review_detectors(spec, nodes, spec_dir)
    review['auto_relations'] = auto_relations(spec, nodes)
    placeholders = {k for k, d in decisions.items() if d.get('mode') in ('missing_asset_placeholder', 'excluded_with_reason')}
    review['effect_regions'] = effect_regions(spec, nodes, set(chrome) | placeholders)
    # Bind the page root to the whole-page region; give every other uncovered
    # visible node its own blocking region so nothing is diluted or skipped.
    whole = spec.get('regions', {}).get('whole')
    roots = [k for k, n in visible.items() if n.get('parent_id') not in nodes]
    if whole is not None:
        whole['node_ids'] = sorted(set(whole.get('node_ids', [])) | set(roots))
    already = covered(spec)
    reference = np.asarray(Image.open(spec_dir / spec['reference']).convert('RGB'))
    for key in sorted(visible):
        if key in chrome or key in already:
            continue
        if decisions.get(key, {}).get('mode') == 'missing_asset_placeholder':
            continue
        node = nodes[key]
        if node.get('text') or node.get('asset_ids') or is_small_visual(node):
            # Text and assets need a visible-ink feature, not an area average.
            b = node['bounds']
            roi = [b['x'] - 1, b['y'] - 1, b['width'] + 2, b['height'] + 2]
            detector = _reference_detector(reference, roi, float(spec['render_scale']))
            if detector is None:
                review.setdefault('needs_detector', []).append(key)
                continue
            name = f'auto__{key}'
            feature = {'label': str(node.get('name') or key), 'node_ids': [key],
                       'padding': [1, 1, 1, 1], 'detector': detector,
                       'review_reason': 'auto: foreground colour from the reference ROI; confirm segmentation',
                       'limits': {'max_center_delta': 1.0, 'max_size_delta': 1.5}}
            if is_small_visual(node):
                feature['profile'] = 'small_visual'
                feature['limits'] = {'max_center_delta': 0.75, 'max_size_delta': 0.75,
                                     'max_edge_delta': 0.75, 'max_ink_ratio_delta': 0.25,
                                     'max_mask_iou_loss': 0.2}
            spec.setdefault('features', {})[name] = feature
            review['auto_regions'].append(name)
            continue
        name = f'node__{key}'
        spec.setdefault('regions', {})[name] = {
            'label': str(nodes[key].get('name') or key), 'node_ids': [key], **DEFAULT_NODE_REGION}
        review['auto_regions'].append(name)
    if any(d.get('mode') == 'missing_asset_placeholder' for d in decisions.values()):
        spec.setdefault('excluded_nodes', {})
        for key, d in decisions.items():
            if d.get('mode') == 'missing_asset_placeholder':
                spec['excluded_nodes'][key] = 'design asset not exported; shape-preserving placeholder'
                bounds = nodes[key]['bounds']
                spec.setdefault('exclude_shapes', []).append({
                    'shape': 'rect', 'rect': [bounds['x'], bounds['y'], bounds['width'], bounds['height']],
                    'reason': f'missing asset placeholder {key}'})
    spec.pop('exclude_rects', None) if not spec.get('exclude_rects') else None
    return spec, review


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--draft', type=Path, required=True, help='prepare run draft.json')
    parser.add_argument('--codegen', type=Path, required=True, help='<page>.codegen.json')
    parser.add_argument('--plan', type=Path, help='prepare page-plan.json (font pins)')
    parser.add_argument('--app', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True, help='reviewed-spec.json to create')
    parser.add_argument('--input', type=Path, action='append', default=[],
                        help='Additional implementation inputs: page file, render test, harness')
    parser.add_argument('--renderer-version', default='')
    parser.add_argument('--platform', default='')
    parser.add_argument('--locale', default='zh_CN')
    args = parser.parse_args()
    marker = args.output.with_name(args.output.name + '.draft-sha256')
    if args.output.exists():
        untouched = marker.exists() and marker.read_text().strip() == sha256(args.output)
        if not untouched:
            parser.error('Refusing to overwrite a reviewed/edited spec; edit it directly or choose a new file')
    spec_dir = args.output.resolve().parent
    draft = read_json(args.draft)
    target = read_json(args.codegen).get('target', 'flutter')
    environment = {'renderer': {'flutter': 'flutter_test', 'react': 'chromium_playwright'}.get(target, target),
                   'renderer_version': args.renderer_version,
                   'platform': args.platform, 'locale': args.locale, 'state': 'default', 'text_scale': 1}
    spec, review = build(draft, args.draft.resolve().parent, read_json(args.codegen),
                         read_json(args.plan) if args.plan else None, spec_dir,
                         args.app.resolve(), args.input, environment)
    args.output.write_text(json.dumps(spec, ensure_ascii=False, indent=2) + '\n')
    marker.write_text(sha256(args.output) + '\n')
    try:
        compile_spec(spec, spec_dir)
        compiled, error = True, None
    except (ValueError, KeyError, OSError) as exc:
        compiled, error = False, str(exc)
    summary = {'status': 'SPEC_COMPILES' if compiled else 'SPEC_NEEDS_REVIEW', 'spec': str(args.output),
               'compile_error': error,
               'auto_regions': len(review['auto_regions']),
               'auto_detectors': review.get('resolved_detectors', []),
               'auto_relations': len(review.get('auto_relations', [])),
               'effect_regions': len(review.get('effect_regions', [])),
               'dropped_chrome_checks': len(review['dropped_checks']),
               'undecided_nodes': review['undecided_nodes'],
               'needs_detector': review.get('needs_detector', []),
               'unbound_obligations': review.get('unbound_obligations', []),
               'review': 'Auto regions use first-reference thresholds; confirm them before the first '
                         'render. Compiling is not visual acceptance.'}
    print(json.dumps(summary, ensure_ascii=False))
    return 0 if compiled else 2


if __name__ == '__main__':
    raise SystemExit(main())
