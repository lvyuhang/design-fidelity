"""Pin acceptance semantics independently from implementation revisions."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def acceptance_policy(c):
    # Labels/review prose do not affect measurements. Every other check field does.
    checks = {group: {name: {k: v for k, v in spec.items()
                            if k not in ('label', 'review_reason', 'reason')}
                      for name, spec in c.get(group, {}).items()}
              for group in ('regions', 'features', 'relations', 'color_samples')}
    engine = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
              for p in Path(__file__).parent.glob('*.py')
              if p.name in ('visual_fidelity_gate.py','fidelity_contract.py','source_requirements.py','preflight.py')}
    return {'engine_sha256':engine, **checks, **{k: c.get(k) for k in (
        'schema_version', 'workflow_version', 'source_snapshot', 'source_version',
        'source_scope', 'canvas', 'render_scale', 'environment',
        'max_excluded_fraction')},
        'coverage': {k: {f: v.get(f) for f in ('status', 'checks')}
                     for k, v in c.get('coverage', {}).items()},
        'exclude_rects': [v['rect'] for v in c.get('exclude_rects', [])],
        'reference_sha256': c.get('pinned_files', {}).get(c.get('reference')),
        'source_hashes': sorted(c.get('pinned_files', {}).get(p, '')
                                for p in c.get('source_documents', []))}


def differences(before, after, prefix=''):
    if isinstance(before, dict) and isinstance(after, dict):
        result = []
        for key in sorted(before.keys() | after.keys()):
            path = f'{prefix}.{key}' if prefix else key
            if key not in before or key not in after:
                result.append(path)
            else:
                result.extend(differences(before[key], after[key], path))
        return result
    return [] if before == after else [prefix]
