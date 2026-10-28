#!/usr/bin/env python3
"""Compatibility entrypoint; shared implementation lives in the packaged skill."""
from pathlib import Path
import runpy

if __name__ == '__main__':
    runner = Path(__file__).resolve().parents[1] / 'skills/design-fidelity/scripts/run_flutter.py'
    runpy.run_path(str(runner), run_name='__main__')
