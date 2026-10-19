"""Source-grid comparison; all preview-derived media are excluded, never scored."""
from pathlib import Path
import json, hashlib
import numpy as np
from PIL import Image,ImageDraw
OUT=Path(__file__).resolve().parents[1]/'design_evidence'
rois={
 'feed-stage':{'caption':(104.75,260,165.5,36),'author_status_like':(104,303,173,20)},
 'gender_none':{'title':(27,1,180,42),'male':(30,117,134,164),'female':(206,117,134,164)},
 'gender_female':{'title':(27,1,180,42),'selected':(206,113,134,168),'warning_text_icon':(42,297,216,36)},
 'comments':{'title':(17,9,85,17),'first_comment':(52,47,212,70),'nested_reply':(85,233,240,86),'expand':(52,325,125,30)}
}
exclusions={'feed-stage':[(96.75,12,181.5,242),(103.75,305,15,15)],'gender_none':[],
 'gender_female':[(295,299,37,34)],'comments':[(16,47,30,30),(16,147,30,30),(53,232,24,24)]}
def rect(v):x,y,w,h=v;return tuple(round(t*4) for t in (x,y,x+w,y+h))
def stats(a,b,mask):
 d=np.abs(a.astype(float)-b.astype(float))[mask]
 return {'pixels':int(mask.sum()),'mean_abs_rgb_0_255':round(float(d.mean()),4),'p95_max_channel_abs':round(float(np.percentile(d.max(axis=1),95)),4)}
report={'method':'RGB absolute error on immutable native 4x grids, no fitting/rescaling. Preview-derived photos, avatars and shield excluded. These metrics are not a fidelity percentage.','samples':{}}
panels=[]
for name in rois:
 src=Image.open(OUT/f'reference-{name}-4x.png').convert('RGB');dst=Image.open(OUT/f'flutter-{name}-4x.png').convert('RGB');assert src.size==dst.size
 a,b=np.array(src),np.array(dst);mask=np.ones(a.shape[:2],bool)
 for r in exclusions[name]:x,y,x2,y2=rect(r);mask[y:y2,x:x2]=False
 evidence=json.loads((OUT/f"{name.replace('-stage','')}-source.json").read_text())
 data={'snapshot_id':evidence['snapshot_id'],'resolved_version':evidence['resolved_version'],'reference_sha256':hashlib.sha256((OUT/f'reference-{name}-4x.png').read_bytes()).hexdigest(),'flutter_sha256':hashlib.sha256((OUT/f'flutter-{name}-4x.png').read_bytes()).hexdigest(),'independent_pixels':stats(a,b,mask),'excluded_rects':exclusions[name],'regions':{}}
 for k,r in rois[name].items():
  x,y,x2,y2=rect(r);data['regions'][k]=stats(a[y:y2,x:x2],b[y:y2,x:x2],mask[y:y2,x:x2])
 report['samples'][name]=data
 diff=np.abs(a.astype(float)-b.astype(float)).max(axis=2);heat=np.zeros_like(a);heat[:,:,0]=np.clip(diff*4,0,255).astype('uint8');heat[~mask]=[35,65,90]
 Image.fromarray(heat).save(OUT/f'diff-{name}-4x.png')
 h=src.height//4;panel=Image.new('RGB',(774,h+30),'#F2F3F5');panel.paste(src.resize((375,h),Image.Resampling.LANCZOS),(0,30));panel.paste(dst.resize((375,h),Image.Resampling.LANCZOS),(399,30));draw=ImageDraw.Draw(panel);draw.text((8,8),name+' / LANHU',fill='#22242A');draw.text((407,8),'FLUTTER',fill='#22242A');panel.save(OUT/f'comparison-{name}.png');panels.append(panel)
canvas=Image.new('RGB',(774,sum(p.height for p in panels)),'#F2F3F5');y=0
for p in panels:canvas.paste(p,(0,y));y+=p.height
canvas.save(OUT/'requested-source-vs-flutter.png');(OUT/'requested-validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print(json.dumps(report,ensure_ascii=False,indent=2))
