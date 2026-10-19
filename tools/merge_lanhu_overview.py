#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description='Merge one frozen Lanhu overview pagination set.')
    parser.add_argument('pages', nargs='+', type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    documents = [json.loads(path.read_text()) for path in args.pages]
    identities = {
        (doc.get('snapshot_id'), doc.get('resolved_version'), doc.get('design_id'))
        for doc in documents
    }
    if len(identities) != 1:
        raise SystemExit('pagination identity mismatch')
    nodes = [node for doc in documents for node in doc.get('nodes', [])]
    ancestors = [node for doc in documents for node in doc.get('ancestors', [])]
    assets = [asset for doc in documents for asset in doc.get('assets', [])]
    first = documents[0]
    expected = int(first.get('total_nodes') or first.get('total') or 0)
    node_ids = [node.get('node_id') for node in nodes]
    if len(nodes) != expected or len(set(node_ids)) != expected:
        raise SystemExit(f'incomplete/duplicate nodes: expected={expected}, got={len(nodes)}, unique={len(set(node_ids))}')
    by_asset = {asset['asset_id']: asset for asset in assets}
    snapshot = {
        'status': 'complete',
        'snapshot_id': first['snapshot_id'],
        'design_id': first['design_id'],
        'design_name': first['design_name'],
        'resolved_version': first['resolved_version'],
        'canvas': first['canvas'],
        'reference_size': first['reference_size'],
        'font_requirements': first.get('font_requirements', []),
        'total_nodes': expected,
        'assets': list(by_asset.values()),
        'nodes': nodes,
        'ancestors': ancestors,
        'coordinate_space': first.get('coordinate_space'),
        'coordinate_mapping': first.get('coordinate_mapping'),
        'source_pages': [str(path) for path in args.pages],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({
        'status': 'PASS',
        'snapshot_id': snapshot['snapshot_id'],
        'nodes': len(nodes),
        'assets': len(by_asset),
        'output': str(args.output),
    }, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
