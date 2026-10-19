"""Extract explicitly labeled preview-only media fixtures, never whole widgets.
These pixels are not independent originals and are excluded from fidelity metrics.
"""
from pathlib import Path
from PIL import Image
import json, hashlib
ROOT=Path(__file__).resolve().parents[1]
out=ROOT/'flutter_ui_components/assets/fixtures'
out.mkdir(exist_ok=True)
feed=Image.open(ROOT/'design_evidence/reference-feed-4x.png').convert('RGB')
comments=Image.open(ROOT/'design_evidence/reference-comments-4x.png').convert('RGB')
gender=Image.open(ROOT/'design_evidence/reference-gender_female-4x.png').convert('RGB')
items=[('feed-photo',feed,(4,1,181.5,242),'photo + baked image-count badge; original bitmap URL absent'),('feed-avatar',feed,(11,294,15,15),'avatar preview crop'),('comment-avatar',comments,(16,47,30,30),'avatar preview crop'),('reply-avatar',comments,(53,232,24,24),'avatar preview crop'),('warning-shield',gender,(295,299,37,34),'decorative icon preview crop; boolean fill path absent')]
manifest=[]
for name,img,(x,y,w,h),gap in items:
 crop=img.crop(tuple(round(v*4) for v in (x,y,x+w,y+h)))
 path=out/(name+'.png');crop.save(path)
 manifest.append({'name':name,'kind':'preview_crop_fallback','source_region_relative':[x,y,w,h],'pixel_size':list(crop.size),'limitation':gap,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'exclude_from_independent_metrics':True})
# Isolate the half-column card inside a 375px review stage without stretching it.
stage=Image.new('RGB',(1500,1368),(254,253,250))
stage.paste(feed,(371,44))
stage.save(ROOT/'flutter_ui_components/assets/reference/feed-stage.png')
stage.save(ROOT/'design_evidence/reference-feed-stage-4x.png')
(ROOT/'design_evidence/preview-media-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
