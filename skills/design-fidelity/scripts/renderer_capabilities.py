"""Fail closed on unhandled paint features. This is not a visual acceptance score."""
import argparse
import json
from pathlib import Path


def requirements(nodes):
    found = {}
    def add(feature, node):
        found.setdefault(feature, []).append(node['node_id'])
    for node in nodes:
        s = node.get('raw_style', {})
        if node.get('effective_source_visible') is False or s.get('isVisible') is False:
            continue
        if node.get('asset_ids'):
            add('asset.export_frame', node)
        if s.get('opacity', 100) != 100:
            add('layer.opacity', node)
        if any(isinstance(r, (int,float)) and r > 1e10 for r in s.get('radius', []) or []):
            add('geometry.extreme_radius', node)
        for field in ('fills', 'borders'):
            for paint in s.get(field, []):
                if paint.get('isEnabled') is False:
                    continue
                kind = 'gradient.' + str(paint['gradient'].get('type', 'unknown')) if paint.get('gradient') else ('color' if paint.get('color') else 'unknown')
                add(field + '.' + kind, node)
                if field == 'borders':
                    add('borders.position.' + str(paint.get('position', 'unknown')), node)
                if paint.get('gradient'):
                    add(field + '.gradient.coordinates', node)
                    if any(stop.get('color', {}).get('a', 1) != 1 for stop in paint['gradient'].get('colorStops', [])):
                        add(field + '.gradient.background_dependency', node)
                if paint.get('opacity', 1) != 1:
                    add(field + '.opacity', node)
                if paint.get('blendMode', 0) != 0:
                    add(field + '.blend.' + str(paint['blendMode']), node)
        if s.get('blur', {}).get('isEnabled'):
            add('blur.' + str(s['blur'].get('blurType', 'unknown')), node)
            add('blur.radius_mapping', node)
            if s['blur'].get('saturation', 1) != 1:
                add('blur.saturation', node)
        for shadow in s.get('shadow', []):
            if shadow.get('isEnabled') is not False:
                add('shadow.' + str(shadow.get('type', 'unknown')), node)
                add('shadow.kernel_and_extent', node)
        if s.get('rotation', 0) or s.get('isFlippedHorizontal') or s.get('isFlippedVertical'):
            add('transform.' + ('ancestor' if node.get('node_type') in ('layer-group', 'symbol') else 'self'), node)
    return {key: sorted(set(ids)) for key, ids in sorted(found.items())}


def audit(nodes, capabilities):
    needed = requirements(nodes)
    supported = capabilities.get('supported', {})
    missing = {key: ids for key, ids in needed.items()
               if not isinstance(supported.get(key), dict)
               or not supported[key].get('implementation')
               or not supported[key].get('test')}
    return {'status': 'UNHANDLED_FEATURES' if missing else 'DECLARED_COVERAGE',
            'requirements': needed, 'unhandled': missing,
            'scope': 'Declared implementation/test coverage only. Execute tests and visual checks separately; never visual PASS.'}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--evidence', type=Path, action='append', required=True)
    p.add_argument('--capabilities', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    nodes = [n for path in a.evidence for n in json.loads(path.read_text())['nodes']]
    result = audit(nodes, json.loads(a.capabilities.read_text()))
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(result, ensure_ascii=False, indent=2))
    print(json.dumps({'status': result['status'], 'unhandled_features': list(result['unhandled']), 'report': str(a.output)}, ensure_ascii=False))
    return 2 if result['unhandled'] else 0


if __name__ == '__main__':
    raise SystemExit(main())
