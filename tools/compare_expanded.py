"""Compare native Flutter raster output to non-resampled, tiled Lanhu references."""
from pathlib import Path
import json, hashlib
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'design_evidence'
resources=json.loads((OUT/'expanded-resources.json').read_text())
report={'method':'RGB absolute error, 0..255; exact 4x grids, no alignment fitting or rescaling. MAE is diagnostic, not a fidelity percentage.',
 'limitations':['Native Flutter test engine; browser visually checked separately.','Message icon outline lacks source paths and is approximate.','Backdrop blur validated on light empty-state background only.'], 'samples':{}}
# Tight ROIs separate components from their demonstration backdrops.
regions={'modal':{'body':(23,22,330,228),'title':(145,48,85,32),'primary_button':(193,178,140,46),'background':(0,0,375,16)},
 'nav':{'bar':(14,21,347,56),'message_icon':(109,32,24,23),'other_icons':(177,32,149,23)},
 'appeal':{'card':(16,4,343,116),'heading':(30,15,86,22),'button':(265,66,78,28),'shield':(278,12,68,79)}}
def stats(a,b):
 d=np.abs(a.astype(float)-b.astype(float))
 return {'mean_abs_rgb_0_255':round(float(d.mean()),4),'p95_max_channel_abs':round(float(np.percentile(d.max(axis=2),95)),4)}
thumbs=[]
for name in ['modal','nav','appeal']:
 ref=OUT/f'reference-{name}-4x.png'; actual=OUT/f'flutter-{name}-4x.png'
 src=Image.open(ref).convert('RGB');dst=Image.open(actual).convert('RGB'); assert src.size==dst.size
 a,b=np.array(src),np.array(dst)
 data={'snapshot':resources[name]['snapshot_id'],'version':resources[name]['resolved_version'],
  'pixel_size':list(src.size),'reference_sha256':hashlib.sha256(ref.read_bytes()).hexdigest(),
  'flutter_sha256':hashlib.sha256(actual.read_bytes()).hexdigest(), 'whole_stage':stats(a,b),'regions':{}}
 for key,(x,y,w,h) in regions[name].items():
  data['regions'][key]={'source_rect':[x,y,w,h],**stats(a[y*4:(y+h)*4,x*4:(x+w)*4],b[y*4:(y+h)*4,x*4:(x+w)*4])}
 report['samples'][name]=data
 d=np.abs(a.astype(float)-b.astype(float)).max(axis=2)
 heat=np.zeros_like(a);heat[:,:,0]=np.clip(d*4,0,255).astype('uint8')
 Image.fromarray(heat).save(OUT/f'diff-{name}-4x.png')
 h=src.height//4
 panel=Image.new('RGB',(774,h+40),'#F2F3F5')
 panel.paste(src.resize((375,h),Image.Resampling.LANCZOS),(0,30))
 panel.paste(dst.resize((375,h),Image.Resampling.LANCZOS),(399,30))
 draw=ImageDraw.Draw(panel);draw.text((8,8),f'{name.upper()} / LANHU',fill='#22242A');draw.text((407,8),'FLUTTER',fill='#22242A')
 panel.save(OUT/f'comparison-{name}.png');thumbs.append(panel)
canvas=Image.new('RGB',(774,sum(i.height for i in thumbs)),'#F2F3F5');y=0
for p in thumbs: canvas.paste(p,(0,y));y+=p.height
canvas.save(OUT/'expanded-source-vs-flutter.png')
(OUT/'expanded-validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
print(json.dumps(report['samples'],ensure_ascii=False,indent=2))
