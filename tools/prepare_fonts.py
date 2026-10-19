"""Prepare local-only subsets of the installed source font for Flutter Web."""
from pathlib import Path
import hashlib
import json
import shutil
from fontTools import subset
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parents[1]
font_paths = list(Path('/System/Library/AssetsV2/com_apple_MobileAsset_Font8').glob('*/AssetData/PingFang.ttc'))
if not font_paths:
    raise SystemExit('Exact source font PingFang.ttc is not available; do not silently substitute it.')
source = font_paths[0]
out = ROOT / 'flutter_ui_components/assets/fonts'
out.mkdir(parents=True, exist_ok=True)
text = ''.join(p.read_text() for p in (ROOT / 'flutter_ui_components/lib').rglob('*.dart'))
# Source-render fallbacks still carry source text obligations. Include the
# pinned page's text runs so the runtime font subset remains complete when a
# label moves from a crop back to a native Flutter widget.
for evidence in (ROOT / 'design_evidence' / 'backup-20-skill211' / 'source').glob('region-*.json'):
    document = json.loads(evidence.read_text())
    text += ''.join(node.get('text') or '' for node in document.get('nodes', []))
text += ''.join(chr(c) for c in range(32, 127))
receipt = {'source': str(source), 'sha256': hashlib.sha256(source.read_bytes()).hexdigest(), 'fonts': []}
for index, name, weight in [(3, 'PingFangSC-Regular', 400), (7, 'PingFangSC-Medium', 500), (11, 'PingFangSC-Semibold', 600)]:
    font = TTFont(source, fontNumber=index)
    assert font['name'].getDebugName(6) == name
    sub = subset.Subsetter()
    sub.populate(text=text)
    sub.subset(font)
    dest = out / f'{name}.otf'
    font.save(dest)
    receipt['fonts'].append({'postscript_name': name, 'weight': weight, 'bytes': dest.stat().st_size,
                            'sha256': hashlib.sha256(dest.read_bytes()).hexdigest()})
    print(dest.name, dest.stat().st_size)
(ROOT / 'design_evidence/font-receipt.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2))
ref = ROOT / 'flutter_ui_components/assets/reference'
ref.mkdir(parents=True, exist_ok=True)
shutil.copyfile(ROOT / 'design_evidence/reference-region.png', ref / 'reference-region.png')
