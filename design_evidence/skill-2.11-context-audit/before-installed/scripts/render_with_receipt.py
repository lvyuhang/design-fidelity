#!/usr/bin/env python3
"""Run the project's renderer and bind its fresh PNG to inputs and contract."""
from __future__ import annotations
import argparse
import json
import subprocess
import sys
import time
from pathlib import Path
from fidelity_contract import read_json, sha256, input_hashes, verify_files


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--contract', required=True, type=Path)
    parser.add_argument('--candidate', required=True, type=Path)
    parser.add_argument('--receipt', required=True, type=Path)
    parser.add_argument('--cwd', required=True, type=Path)
    parser.add_argument('--timeout', type=int, default=300)
    parser.add_argument('command', nargs=argparse.REMAINDER)
    args = parser.parse_args()
    command = args.command[1:] if args.command[:1] == ['--'] else args.command
    if not command:
        raise ValueError('Provide renderer command after --')
    contract_path = args.contract.resolve()
    candidate = args.candidate.resolve()
    receipt_path = args.receipt.resolve()
    if candidate == receipt_path or contract_path in (candidate, receipt_path):
        raise ValueError('Contract, candidate and receipt paths must differ')
    c = read_json(contract_path)
    verify_files(c, contract_path.parent)
    before = input_hashes(c, contract_path.parent)
    contract_hash = sha256(contract_path)
    protected = {(contract_path.parent / p).resolve() for p in before}
    if candidate in protected or receipt_path in protected:
        raise ValueError('Output would overwrite an input')
    previous = candidate.stat() if candidate.exists() else None
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.write_text(json.dumps({'status': 'NOT_EVALUATED', 'reason': 'Render in progress'}))
    started = time.time_ns()
    result = subprocess.run(command, cwd=args.cwd.resolve(), timeout=args.timeout, check=False)
    if result.returncode:
        raise ValueError(f'Renderer exited {result.returncode}; no new receipt written')
    if not candidate.is_file():
        raise ValueError('Renderer did not produce candidate PNG')
    current = candidate.stat()
    if previous and (current.st_mtime_ns, current.st_ctime_ns, current.st_size) == (previous.st_mtime_ns, previous.st_ctime_ns, previous.st_size):
        raise ValueError('Candidate was not rewritten; stale screenshot')
    from PIL import Image
    expected = tuple(round(n*c['render_scale']) for n in c['canvas'])
    with Image.open(candidate) as image:
        if image.format != 'PNG' or image.size != expected:
            raise ValueError(f'Expected PNG {expected}, got {image.format} {image.size}')
    if input_hashes(c, contract_path.parent) != before or sha256(contract_path) != contract_hash:
        raise ValueError('Inputs or contract changed while rendering')
    receipt = {'schema_version': 1, 'contract_sha256': contract_hash,
               'candidate_sha256': sha256(candidate), 'environment': c['environment'],
               'inputs': before, 'command': command, 'cwd': str(args.cwd.resolve()),
               'exit_code': 0, 'started_ns': started, 'finished_ns': time.time_ns()}
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2, allow_nan=False)+'\n')
    print(f'Render receipt: {receipt_path}')
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (ValueError, OSError, subprocess.TimeoutExpired) as error:
        print(f'NOT_EVALUATED: {error}', file=sys.stderr)
        raise SystemExit(2)
