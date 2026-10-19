"""Evaluate, never repair, the frozen MCP first-pass implementation."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, shutil
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'design_evidence/appeal-direct'
ASSETS=ROOT/'flutter_ui_components/assets/experiments/appeal-direct'
ASSETS.mkdir(parents=True,exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
freeze=json.loads((OUT/'freeze.json').read_text())
code=ROOT/'flutter_ui_components/lib/experiments/appeal_direct.dart'
assert sha(code)==freeze['code_sha256']==sha(OUT/'appeal_direct.frozen.dart'), 'Frozen implementation changed; evaluation aborted.'
ref=ROOT/'design_evidence/reference-appeal-4x.png'
images={'reference':Image.open(ref).convert('RGB')}
for name in ['direct','calibrated']:images[name]=Image.open(OUT/f'{name}-4x.png').convert('RGB')
assert all(im.size==(1500,500) for im in images.values())
regions={'card':('整张卡片',(16,4,343,116)),
 'title':('标题文字',(30,15,86,22)),
 'fields':('字段与结果',(30,48,176,62)),
 'divider':('分隔线',(30,40,315,4)),
 'button':('申诉按钮',(265,66,78,28)),
 'shadow':('按钮下方阴影',(251,96,102,23)),
 'shield':('原始盾牌资源',(278,12,68,50)),
 'fill':('背景填充',(118,10,144,25))}
a=np.array(images['reference']).astype(float)
report={'evaluated_at_utc':datetime.now(timezone.utc).isoformat(),
 'source_version':'84ebb977-1081-434c-9147-12e6147c820b','code_sha256':sha(code),
 'visual_revision_count':0,'strict_blind_test':False,'standard_shadow_blur_enabled':True,
 'method':'Exact native 4x RGB grids, no alignment optimization or resampling. MAE is 0..255, lower is better, not a fidelity percentage. Regions selected after freeze; all regions reported.',
 'source_reference_sha256':sha(ref),'regions':{},'render_sha256':{},
 'font_hashes_at_evaluation':{p.name:sha(p) for p in (ROOT/'flutter_ui_components/assets/fonts').glob('*.otf')},
 'limitations':['Single component, one attempt, source-backed initial screenshot allowed.','Model retains prior context; not a strict blind test.','Same source PNG and font family used in both variants.','Test-renderer metrics; browser checked separately.','Title, fields and button regions contain background; metrics are diagnostic rather than perceptual acceptance scores.']}
for name in ['direct','calibrated']:
 b=np.array(images[name]).astype(float);d=np.abs(a-b)
 heat=np.zeros_like(a,dtype='uint8');heat[:,:,0]=np.clip(d.max(axis=2)*4,0,255).astype('uint8')
 Image.fromarray(heat).save(OUT/f'{name}-heat-4x.png')
 report['render_sha256'][name]=sha(OUT/f'{name}-4x.png')
 for key,(label,(x,y,w,h)) in regions.items():
  region=report['regions'].setdefault(key,{'label':label,'rect':[x,y,w,h]})
  diff=d[y*4:(y+h)*4,x*4:(x+w)*4]
  region[name]={'mae':round(float(diff.mean()),4),'p95':round(float(np.percentile(diff.max(axis=2),95)),4)}
for name,im in images.items():im.save(ASSETS/f'{name}.png')
for key,(_,rect) in regions.items():
 x,y,w,h=rect
 for name,im in images.items():im.crop((x*4,y*4,(x+w)*4,(y+h)*4)).save(ASSETS/f'{key}-{name}.png')
for name in ['direct','calibrated']:shutil.copyfile(OUT/f'{name}-heat-4x.png',ASSETS/f'{name}-heat.png')
panel=Image.new('RGB',(1173,157),'#F2F3F5');draw=ImageDraw.Draw(panel)
for i,name in enumerate(images):
 draw.text((i*399+10,8),name.upper(),fill='#22242A')
 panel.paste(images[name].resize((375,125),Image.Resampling.LANCZOS),(i*399,32))
panel.save(OUT/'three-way-comparison.png')
(OUT/'evaluation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
(ASSETS/'evaluation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
print(json.dumps(report['regions'],ensure_ascii=False,indent=2))
