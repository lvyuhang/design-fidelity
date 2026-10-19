"""Create installable and source ZIPs; stdlib only."""
from pathlib import Path
import hashlib
import json
import zipfile

root = Path(__file__).resolve().parents[1]
bundle = root / 'LayerPilot.sketchplugin'
manifest = json.loads((bundle / 'Contents/Sketch/manifest.json').read_text())
assert [c['identifier'] for c in manifest['commands']] == ['organize', 'assets']
for command in manifest['commands']:
    assert (bundle / 'Contents/Sketch' / command['script']).is_file()
resources = bundle / 'Contents/Resources'
(resources / 'THIRD_PARTY_NOTICES.md').write_bytes((root / 'THIRD_PARTY_NOTICES.md').read_bytes())
(resources / 'README.md').write_bytes((root / 'README.md').read_bytes())
(resources / 'UX_AUDIT.md').write_bytes((root / 'UX_AUDIT.md').read_bytes())
(resources / 'LICENSE').write_bytes((root / 'LICENSE').read_bytes())
dist = root / 'dist'
dist.mkdir(exist_ok=True)
version = manifest['version']
archives = []
for source in (False, True):
    path = dist / f'LayerPilot-{version}{"-source" if source else ""}.zip'
    files = sorted(root.rglob('*') if source else bundle.rglob('*'))
    with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as archive:
        for file in files:
            if not file.is_file():
                continue
            rel = file.relative_to(root)
            if source and (rel.parts[0] == 'dist' or '__pycache__' in rel.parts or file.name == '.DS_Store'):
                continue
            if source and rel.parts[0] == 'evidence' and (len(rel.parts) != 2 or file.name not in {
                'before.png', 'after.png', 'fixture.png', 'LayerPilot-Demo.sketch',
                'native-report.json', 'native-edge-report.json', 'pixel-report.json', 'undo-report.json', 'fix-report.json', 'slices-report.json', 'slice-pixel-report.json', 'slice-document-report.json', 'organize-document-report.json', 'organize-v0.4-document-report.json', 'layout-native-report.json', 'layout-pixel-report.json', 'v5-native-report.json', 'v5-pixel-report.json', 'organize-v0.5-document-report.json', 'slices-v0.5.1-document-report.json', 'ux-native-report.json', 'window-scope-report.json', 'visual-native-report.json', 'overlay-report.json', 'async-report.json', 'responsiveness-report.json', 'progress-heartbeat-before.json', 'progress-heartbeat-after.json'
            }):
                continue
            name = str(Path('sketch-layerpilot') / rel) if source else str(rel)
            archive.write(file, name)
    with zipfile.ZipFile(path) as archive:
        assert archive.testzip() is None
    archives.append({'file': path.name, 'bytes': path.stat().st_size, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
(dist / 'checksums.json').write_text(json.dumps(archives, indent=2) + '\n')
print(json.dumps(archives, indent=2))
