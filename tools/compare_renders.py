"""Diagnostic pixel comparisons, not a fabricated percentage of design fidelity."""
from pathlib import Path
import json
import hashlib
import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'design_evidence'
report = {
    'snapshot_id': 'ed07411fb68b9878b1395ab190b98915',
    'version_id': '18f1a6ed-585a-4b77-801b-7a9d5e726810',
    'source_canvas': [375, 812],
    'test_raster_scale': 4,
    'method': 'Unscaled source PNG versus Flutter test-engine PNG; RGB absolute error in 0–255 channels. No acceptance percentage is inferred.',
    'limitations': ['This is a native Flutter test-engine comparison; the browser is also visually checked separately.',
                    'Font antialiasing, gradient rounding and blur kernels can differ between Sketch and Flutter.'],
    'fixtures': {},
}

def stats(a, b):
    diff = np.abs(a.astype(float) - b.astype(float))
    return {'mean_abs_rgb_0_255': round(float(diff.mean()), 4),
            'p95_max_channel_abs': round(float(np.percentile(diff.max(axis=2), 95)), 4)}

for name in ['buttons', 'agreement']:
    source_path = OUT / f'reference-{name}-4x.png'
    actual_path = OUT / f'flutter-{name}-4x.png'
    source = Image.open(source_path).convert('RGB')
    actual = Image.open(actual_path).convert('RGB')
    assert source.size == actual.size
    a, b = np.array(source), np.array(actual)
    data = {'pixel_size': list(source.size), 'source_sha256': hashlib.sha256(source_path.read_bytes()).hexdigest(),
            'render_sha256': hashlib.sha256(actual_path.read_bytes()).hexdigest(), **stats(a,b)}
    report['fixtures'][name] = data
    heat = np.abs(a.astype(float)-b.astype(float)).max(axis=2)
    heat = np.clip(heat * 4, 0, 255).astype('uint8')
    visual = np.zeros((*heat.shape, 3), dtype='uint8')
    visual[:,:,0] = heat
    Image.fromarray(visual).save(OUT / f'diff-{name}-4x.png')
    if name == 'buttons':
        data['text_ink_bounds'] = []
        for label,y in [('wechat',405),('qq',473),('phone',541),('apple',609)]:
            x0,y0 = (172-24)*4,(y+15-393)*4
            entry={'provider':label}
            for image_name, image in [('source',a),('flutter',b)]:
                crop=image[y0:y0+80,x0:x0+320]
                yy,xx=np.where(crop.mean(axis=2)<160)
                entry[image_name]=[int(xx.min()),int(yy.min()),int(xx.max()),int(yy.max())]
            entry['max_boundary_delta_in_source_pixels']=max(abs(x-y) for x,y in zip(entry['source'],entry['flutter']))/4
            data['text_ink_bounds'].append(entry)
        data['fill_patch'] = stats(a[88:124,184:344],b[88:124,184:344])

(OUT/'validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
source=Image.open(OUT/'reference-region.png').convert('RGB').resize((375,395),Image.Resampling.LANCZOS)
actual=Image.open(OUT/'flutter-region-4x.png').convert('RGB').resize((375,395),Image.Resampling.LANCZOS)
canvas=Image.new('RGB',(774,437),(242,243,245))
canvas.paste(source,(0,30));canvas.paste(actual,(399,30))
draw=ImageDraw.Draw(canvas)
draw.text((8,8),'LANHU - SOURCE',fill='#22242A')
draw.text((407,8),'FLUTTER - RENDER',fill='#22242A')
canvas.save(OUT/'source-vs-flutter.png')
print(json.dumps(report['fixtures'],ensure_ascii=False,indent=2))
