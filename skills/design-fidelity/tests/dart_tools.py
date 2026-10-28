"""Optional Dart syntax check for generated code.

Uses `FIDELITY_DART_SYNTAX` (any checker that takes file paths and exits non-zero
on syntax errors) or `dart format --output=none`. Returns None when neither is
available so tests can skip instead of passing silently.
"""
import os
import shutil
import subprocess


def dart_syntax_errors(*paths):
    checker = os.environ.get('FIDELITY_DART_SYNTAX')
    if checker:
        command = [checker, *map(str, paths)]
    elif shutil.which('dart'):
        command = ['dart', 'format', '--output=none', *map(str, paths)]
    else:
        return None
    result = subprocess.run(command, capture_output=True, text=True)
    return '' if result.returncode == 0 else (result.stdout + result.stderr)
