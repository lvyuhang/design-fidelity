"""Measure the frozen two-state gender implementation, without visual repair."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json
import numpy as np
from PIL import Image, ImageDraw
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'design_evidence/gender-direct'
ASSETS=ROOT/'flutter_ui_components/assets/experiments/gender-direct'
ASSETS.mkdir(parents=True,exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
freeze=json.loads((OUT/'freeze.json').read_text())
code=ROOT/'flutter_ui_components/lib/experiments/gender_direct.dart'
assert sha(code)==freeze['code_sha256']==sha(OUT/'gender_direct.frozen.dart'), 'Frozen code changed'
sol_out=ROOT/'design_evidence/gender-sol56'
sol_freeze=json.loads((sol_out/'freeze.json').read_text())
sol_code=ROOT/'flutter_ui_components/lib/experiments/gender_sol56_direct.dart'
assert sha(sol_code)==sol_freeze['source']['sha256']==sha(sol_out/'gender_sol56_direct.frozen.dart'), 'Frozen 5.6 Sol code changed'
for name,digest in freeze['inputs'].items():
 assert sha(OUT/name)==digest, f'Frozen input changed: {name}'
for asset,digest in freeze['original_asset_hashes'].items():
 assert sha(ROOT/'flutter_ui_components'/asset)==digest, f'Original asset changed: {asset}'
regions={
 'canvas':('全画布（含资源缺口）',(0,0,375,350)),
 'common':('共同可验证区',(0,0,375,350)),
 'heading':('标题与副标题',(24,0,205,66)),
 'male_card':('男生卡片及阴影',(16,104,162,200)),
 'female_card':('女生卡片及阴影',(192,104,162,200)),
 'card_fill':('未选卡片内部填充',(40,128,110,28)),
 'shadow':('卡片底部阴影',(24,278,146,22)),
 'border':('卡片左上圆角',(28,115,32,32)),
 'male_icon':('男生原始图标',(65,163,64,64)),
 'female_icon':('女生原始图标',(241,163,64,64)),
 'background':('顶部渐变背景',(235,0,140,80)),
}
extra={
 'check':('选中角标',(315,113,25,25)),
 'warning':('警示条（排除盾牌）',(33,297,307,36)),
 'warning_text':('警示文字',(80,306,156,18)),
 'shield_gap':('盾牌缺失填充区',(295,299,37,34)),
}
report={'evaluated_at_utc':datetime.now(timezone.utc).isoformat(),'code_sha256':sha(code),
 'sol56_code_sha256':sha(sol_code),
 'models':{'sol56':{'model':'gpt-5.6-sol','reasoning_effort':'high','visual_revision_count':0},
           'direct':{'model':'gpt-6','reasoning_effort':'unspecified','visual_revision_count':0},
           'calibrated':{'model':'gpt-6','role':'existing corrected baseline'}},
 'visual_revision_count':0,'strict_blind_test':False,'standard_shadow_blur_enabled':True,
 'method':'Native 4x RGB MAE (0..255). No alignment or resizing. Lower is closer, not fidelity %. Common/warning exclude shield rect for BOTH variants. Full canvas and shield diagnostic retain it.',
 'excluded_region':[295,299,37,34], 'states':{},
 'font_hashes_at_evaluation':{p.name:sha(p) for p in (ROOT/'flutter_ui_components/assets/fonts').glob('*.otf')},
 'limitations':['5.6 Sol was isolated from existing implementations and metrics, but received source screenshots and JSON; this is not JSON-only.','The GPT-6 direct implementation came from an ongoing session with prior implementation knowledge; it is not a strict blind sample.','Fonts and 5 original exported assets verified and reused.','Calibrated shield uses a source preview crop; its low pixel error is not independent reconstruction.','Single attempt per model, two source states; metrics from the test renderer, browser checked separately.','The GPT-6 direct card shadow clipping and background blur mapping used prior experience before first render.']}
for state in ['none','female']:
 ref=ROOT/f'design_evidence/reference-gender_{state}-4x.png'
 assert sha(ref)==freeze['reference_hashes'][state]
 images={'reference':Image.open(ref).convert('RGB')}
 for variant in ['sol56','direct','calibrated']:
  images[variant]=Image.open(OUT/f'{state}-{variant}-4x.png').convert('RGB')
 assert all(im.size==(1500,1400) for im in images.values())
 item={'source_version':json.loads((OUT/f'{state}-input.json').read_text())['resolved_version'],'source_reference_sha256':sha(ref),'regions':{},'render_sha256':{}}
 report['states'][state]=item
 rs=regions | (extra if state=='female' else {})
 a=np.asarray(images['reference'],dtype=float)
 mask=np.ones(a.shape[:2],dtype=bool)
 if state=='female':mask[299*4:333*4,295*4:332*4]=False
 for variant in ['sol56','direct','calibrated']:
  d=np.abs(a-np.asarray(images[variant],dtype=float))
  heat=np.zeros(a.shape,dtype='uint8');heat[:,:,0]=np.clip(d.max(axis=2)*4,0,255).astype('uint8')
  Image.fromarray(heat).save(OUT/f'{state}-{variant}-heat-4x.png')
  item['render_sha256'][variant]=sha(OUT/f'{state}-{variant}-4x.png')
  for key,(label,(x,y,w,h)) in rs.items():
   crop=d[y*4:(y+h)*4,x*4:(x+w)*4]
   selected=np.ones(crop.shape[:2],dtype=bool)
   if key in ('common','warning'): selected=mask[y*4:(y+h)*4,x*4:(x+w)*4]
   pixels=crop[selected]
   region=item['regions'].setdefault(key,{'label':label,'rect':[x,y,w,h],'pixels_evaluated':int(selected.sum()),'excluded_shield':state=='female' and key in ('common','warning'),'resource_gap_diagnostic':key=='shield_gap'})
   region[variant]={'mae':round(float(pixels.mean()),4),'p95':round(float(np.percentile(pixels.max(axis=1),95)),4)}
 for name,im in images.items(): im.save(ASSETS/f'{state}-{name}.png')
 for key,(_,rect) in rs.items():
  if key in ('canvas','common'):continue
  x,y,w,h=rect
  for name,im in images.items():im.crop((x*4,y*4,(x+w)*4,(y+h)*4)).save(ASSETS/f'{state}-{key}-{name}.png')
 panel=Image.new('RGB',(1572,382),'#F2F3F5');draw=ImageDraw.Draw(panel)
 for i,(name,im) in enumerate(images.items()):
  draw.text((i*399+10,8),name.upper(),fill='#22242A')
  panel.paste(im.resize((375,350),Image.Resampling.LANCZOS),(i*399,32))
 panel.save(OUT/f'{state}-four-way.png')
 print(state, json.dumps({k:{v:d[v]['mae'] for v in ('sol56','direct','calibrated')} for k,d in item['regions'].items()},ensure_ascii=False))
for target in (OUT,ASSETS): (target/'evaluation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
