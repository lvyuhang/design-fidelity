"""Report per-region signed RGB drift; never a full-page acceptance score."""
import argparse,json
import numpy as np
from PIL import Image

def measure(reference, actual, regions, threshold=.5):
    if reference.shape != actual.shape: raise ValueError('Image sizes differ')
    rows=[]
    for name,box in regions.items():
        x,y,right,bottom=box
        if not (0<=x<right<=reference.shape[1] and 0<=y<bottom<=reference.shape[0]): raise ValueError('Invalid region '+name)
        delta=actual[y:bottom,x:right,:3].astype(float)-reference[y:bottom,x:right,:3].astype(float)
        bias=delta.mean(axis=(0,1));mae=np.abs(delta).mean(axis=(0,1));p95=np.percentile(np.abs(delta),95,axis=(0,1))
        rows.append(dict(region=name,box=box,bias_rgb=bias.tolist(),mae_rgb=mae.tolist(),p95_abs_rgb=p95.tolist(),passed=bool(np.max(np.abs(bias))<=threshold and np.max(p95)<=threshold)))
    return dict(status='LOCAL_PASS' if rows and all(r['passed'] for r in rows) else 'LOCAL_FAIL',threshold=threshold,regions=rows,scope='Frozen blank-background regions only; no full-page PASS')

def main():
    p=argparse.ArgumentParser();p.add_argument('--reference',required=True);p.add_argument('--actual',required=True);p.add_argument('--regions',required=True);p.add_argument('--output',required=True);a=p.parse_args()
    spec=json.load(open(a.regions));r=measure(np.array(Image.open(a.reference).convert('RGB')),np.array(Image.open(a.actual).convert('RGB')),spec['regions'],spec['threshold'])
    with open(a.output,'w') as f:json.dump(r,f,indent=2)
    print(r['status']);return 0 if r['status']=='LOCAL_PASS' else 2
if __name__=='__main__':raise SystemExit(main())
