"""Run core and real Sketch tests, then validate output pixels."""
from pathlib import Path
import argparse
import json
import subprocess
import sys

root = Path(__file__).resolve().parents[1]
p = argparse.ArgumentParser()
p.add_argument('--node', default='node')
p.add_argument('--python', default=sys.executable)
p.add_argument('--sketchtool', default='/Applications/Sketch.app/Contents/Resources/sketchtool/bin/sketchtool')
a = p.parse_args()
for module in ['core', 'regions', 'layout', 'glyphs', 'pixels', 'canvas']:
    subprocess.run([a.node, '-e', f'console.log(require("./tests/{module}.test.cjs")())'], cwd=root, check=True)
for file in (root / 'LayerPilot.sketchplugin/Contents/Sketch').rglob('*.js'):
    subprocess.run([a.node, '--check', str(file)], check=True)
for module, stages in [('native', ['run']), ('native-edge', ['run']), ('native-slices', ['run']), ('native-layout', ['run']), ('native-v5', ['run']), ('native-ux', ['run']), ('native-window-scope', ['run']), ('native-visual', ['run']), ('native-overlay', ['run']), ('native-async', ['run','undo']), ('native-undo', ['prepare', 'apply', 'verifyOrganize', 'applySlices', 'verify'])]:
    report_name = {'native': 'native-report', 'native-edge': 'native-edge-report', 'native-slices': 'slices-report', 'native-layout': 'layout-native-report', 'native-v5': 'v5-native-report', 'native-ux': 'ux-native-report', 'native-window-scope': 'window-scope-report', 'native-visual': 'visual-native-report', 'native-overlay': 'overlay-report', 'native-async': 'async-report', 'native-undo': 'undo-report'}[module]
    report_path = root / 'evidence' / (report_name + '.json')
    report_path.unlink(missing_ok=True)
    for stage in stages:
        code = f'require({json.dumps(str(root / "tests" / (module + ".js")))}).{stage}({json.dumps(str(root))});'
        completed = subprocess.run([a.sketchtool, 'run-script', code, '--without-activating=YES', '--timeout=30'], text=True, capture_output=True, check=True)
        if completed.stderr:
            print(completed.stderr)
    report = json.loads(report_path.read_text())
    assert report['success'], report
    print(report_name, 'PASS')
subprocess.run([a.python, str(root / 'scripts/verify_pixels.py')], check=True)
