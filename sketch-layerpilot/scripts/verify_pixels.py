from pathlib import Path
import json
from PIL import Image
p = Path(__file__).resolve().parents[1] / 'evidence'
r = json.loads((p / 'native-report.json').read_text())
edge = json.loads((p / 'native-edge-report.json').read_text())
a = Image.open(p / 'before.png').convert('RGBA')
b = Image.open(p / 'after.png').convert('RGBA')
checks = {
    'pixelIdentical': a.size == b.size and a.tobytes() == b.tobytes(),
    'size': a.size,
    'PNGScalesCorrect': all(Image.open(Path(r['exports']['directory']) / f['file']).size == (24*f['scale'], 24*f['scale']) for f in r['exports']['files'])
}
fixture = Image.open(p / 'fixture.png').convert('RGB')
for key, bounds in [('crop', (20, 20, 60, 60)), ('mask', (0, 0, 40, 40))]:
    img = Image.open(Path(edge[key]['directory']) / edge[key]['files'][0]['file']).convert('RGB')
    checks[key + 'MatchesVisiblePixels'] = img.size == (40, 40) and img.tobytes() == fixture.crop(bounds).tobytes()
assert all(value for key, value in checks.items() if key != 'size'), checks
(p / 'pixel-report.json').write_text(json.dumps(checks, indent=2) + '\n')
print(checks)
before = Image.open(p / 'slices-before.png').convert('RGBA')
after = Image.open(p / 'slices-after.png').convert('RGBA')
icon = Image.open(p / 'slice-icon.png').convert('RGBA')
photo = Image.open(p / 'slice-photo.png').convert('RGBA')
mask = Image.open(p / 'slice-mask.png').convert('RGBA')
original = Image.open(p / 'fixture.png').convert('RGBA')
slice_checks = {
    'canvasUnchanged': before.size == after.size and before.tobytes() == after.tobytes(),
    'transparentIconBackground': icon.size == (40, 40) and icon.getpixel((0, 0))[3] == 0 and icon.getpixel((20, 20)) == (255, 0, 0, 255),
    'photoPixelsPreserved': photo.size == original.size and photo.tobytes() == original.tobytes(),
    'maskPixelsPreserved': mask.size == (40, 40) and mask.tobytes() == original.crop((0, 0, 40, 40)).tobytes()
}
assert all(slice_checks.values()), slice_checks
(p / 'slice-pixel-report.json').write_text(json.dumps(slice_checks, indent=2) + '\n')
print(slice_checks)

layout_report = json.loads((p / 'layout-native-report.json').read_text())
layout_checks = {}
for case in layout_report['cases']:
    name = case['name']
    before = Image.open(p / ('layout-' + name + '-before.png')).convert('RGBA')
    after = Image.open(p / ('layout-' + name + '-after.png')).convert('RGBA')
    layout_checks[name] = before.size == after.size and before.tobytes() == after.tobytes()
assert all(layout_checks.values()), layout_checks
(p / 'layout-pixel-report.json').write_text(json.dumps(layout_checks, indent=2) + '\n')
print(layout_checks)

# Standard glyph canvases must contain only the artwork, with transparent margins.
import xml.etree.ElementTree as ET
before = Image.open(p / 'v5-before.png').convert('RGBA')
after = Image.open(p / 'v5-after.png').convert('RGBA')
glyph = Image.open(p / 'v5-glyph.png').convert('RGBA')
svg = ET.parse(p / 'v5-glyph.svg').getroot()
v5_checks = {
    'canvasUnchanged': before.size == after.size and before.tobytes() == after.tobytes(),
    'uniformSVGCanvas': svg.attrib.get('viewBox') == '0 0 24 24' and svg.attrib.get('width') == '24px' and svg.attrib.get('height') == '24px',
    'noEmbeddedBitmap': not any(x.tag.endswith('image') for x in svg.iter()),
    'transparentMargin': glyph.size == (24, 24) and glyph.getpixel((0, 0))[3] == 0 and glyph.getpixel((23, 23))[3] == 0,
    'glyphBoundsCentered': glyph.getchannel('A').getbbox() == (6, 4, 18, 20),
    'noButtonBackground': not any(r > 240 and g > 240 and b > 240 and a > 0 for r, g, b, a in glyph.getdata()),
}
assert all(v5_checks.values()), v5_checks
(p / 'v5-pixel-report.json').write_text(json.dumps(v5_checks, indent=2) + '\n')
print(v5_checks)
