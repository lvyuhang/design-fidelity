"""Check immutable inputs before rendering; inventory source-style gaps separately."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import time
from fidelity_contract import read_json, validate_contract, verify_files, verify_fonts
from visual_fidelity_gate import _load_nodes, _validate_evidence


def style_gaps(nodes):
    """Conservative evidence check, not a claim that all design semantics are verified."""
    gaps = []
    for key, node in nodes.items():
        if not node.get('text') or node.get('effective_source_visible') is False:
            continue
        raw = (node.get('raw_style') or {}).get('font') or {}
        spec = (node.get('text_spec') or {}).get('base_style') or {}
        fields = {
            'font_family': spec.get('font_family') or raw.get('font'),
            'font_size': spec.get('font_size', raw.get('size')),
            'line_height': spec.get('line_height', raw.get('line')),
            'color': spec.get('color', raw.get('color')),
        }
        missing = [field for field, value in fields.items() if value is None or value == '']
        if missing:
            gaps.append({'node_id': key, 'text': node['text'], 'missing': missing})
    return gaps


def check(contract_path, require_style_evidence=False):
    from PIL import Image
    contract_path = Path(contract_path).resolve()
    base = contract_path.parent
    c = read_json(contract_path)
    paths = [base / p for p in c['source_documents']]
    _validate_evidence(paths, c)
    nodes = _load_nodes(paths)
    coverage = validate_contract(c, nodes)
    verify_files(c, base)
    fonts = verify_fonts(c, nodes, base)
    expected = tuple(round(n*c['render_scale']) for n in c['canvas'])
    with Image.open(base/c['reference']) as im:
        if im.size != expected:
            raise ValueError(f'Reference dimensions {im.size} differ from {expected}')
        im.verify()
    for path in c.get('assets', []):
        if Path(path).suffix.lower() == '.svg':
            # Source SVG integrity is hash-checked above; decode is renderer-specific.
            continue
        with Image.open(base/path) as im:
            im.verify()
    gaps = style_gaps(nodes)
    if require_style_evidence and gaps:
        raise ValueError(f'{len(gaps)} text nodes lack source styles; inspect and save source regions before coding')
    return {'status': 'READY_FOR_RENDER', 'coverage': coverage, 'fonts': fonts,
            'asset_count': len(c.get('assets', [])), 'style_gaps': gaps,
            'scope': 'input integrity and font coverage; source-style completeness is separate; not visual acceptance'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument('--contract', type=Path)
    source.add_argument('--evidence', type=Path, action='append')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--require-style-evidence', action='store_true')
    args = parser.parse_args()
    started = time.monotonic()
    try:
        if args.evidence:
            documents = [read_json(p) for p in args.evidence]
            identities = {(d.get('snapshot_id'), d.get('resolved_version')) for d in documents}
            if len(identities) != 1 or any(v is None for v in next(iter(identities))):
                raise ValueError('Source evidence identity is missing or inconsistent')
            nodes = _load_nodes(args.evidence)
            gaps = style_gaps(nodes)
            result = {'status': 'NEEDS_SOURCE_STYLES' if gaps else 'TEXT_STYLES_PRESENT',
                      'node_count': len(nodes), 'style_gaps': gaps,
                      'scope': 'text-style availability only; pagination, effects, vectors and fonts still require audit'}
            code = 2 if gaps else 0
        else:
            result = check(args.contract, args.require_style_evidence)
            code = 0
    except (ValueError, OSError, KeyError) as exc:
        result = {'status': 'NOT_EVALUATED', 'reason': str(exc)}
        code = 2
    result['seconds'] = round(time.monotonic()-started, 3)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('coverage','fonts','style_gaps')}
                     | {'style_gap_count': len(result.get('style_gaps', [])), 'report': str(args.output)}, ensure_ascii=False))
    return code


if __name__ == '__main__':
    raise SystemExit(main())
