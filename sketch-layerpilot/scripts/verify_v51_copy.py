"""Verify private document proof without publishing source artwork."""
from pathlib import Path
import json
import xml.etree.ElementTree as ET
from PIL import Image
root = Path(__file__).resolve().parents[1]
p = root / 'evidence/private-v0.5.1'
report = json.loads((p / 'report.json').read_text())
assert report['success'], report
checks = {}
for scale in (1, 2):
    before = Image.open(p / f'before-{scale}x.png').convert('RGBA')
    after = Image.open(p / f'after-{scale}x.png').convert('RGBA')
    checks[f'unchangedAt{scale}x'] = before.size == after.size and before.tobytes() == after.tobytes()
for name in ('play-a', 'play-b', 'heart'):
    svg = ET.parse(p / f'{name}.svg').getroot()
    checks[name + 'SVG16'] = svg.attrib['viewBox'] == '0 0 16 16'
    checks[name + 'NoBitmap'] = not any(x.tag.endswith('image') for x in svg.iter())
    img = Image.open(p / f'{name}.png').convert('RGBA')
    checks[name + 'TransparentMargin'] = img.size == (16, 16) and all(img.getpixel(x)[3] == 0 for x in ((0, 0), (15, 15), (15, 0), (0, 15)))
    if name.startswith('play'):
        checks[name + 'OneTrianglePath'] = sum(x.tag.endswith('path') for x in svg.iter()) == 1
        checks[name + 'OnlyWhitePixels'] = all(r == g == b == 255 for r, g, b, a in img.get_flattened_data() if a > 0)
assert all(checks.values()), checks
summary = {'checks': checks, 'nativeChecks': report['checks'], 'candidateCount': report['found'], 'updatedSlices': report['slices']['updated'] + report['selectedSlice']['updated'], 'textCollisionSkips': len(report['slices']['errors'])}
(root / 'evidence/slices-v0.5.1-document-report.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n')
print(json.dumps(summary, ensure_ascii=False))
