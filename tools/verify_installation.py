"""Verify an offline source fixture and optionally re-render through production Flutter."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from PIL import Image, ImageChops, ImageStat

ROOT=Path(__file__).resolve().parents[1]


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--render',action='store_true');a=p.parse_args()
    example=ROOT/'examples/withdraw-2'
    manifest=json.loads((example/'manifest.json').read_text())
    for name,expected in manifest['sha256'].items():
        path=(example/name).resolve()
        if not path.is_relative_to(example):raise ValueError('Fixture path escapes example folder')
        if hashlib.sha256(path.read_bytes()).hexdigest()!=expected:raise ValueError('Fixture changed: '+name)
    source=json.loads((example/'source.json').read_text())
    if len(source['nodes'])!=source['total']:raise ValueError('Source node inventory incomplete')
    assert source['snapshot_id']==manifest['snapshot_id']
    output=ROOT/'.local/verification';output.mkdir(parents=True,exist_ok=True)
    report={'fixture_hashes':'PASS','source_nodes':len(source['nodes']),
            'source_snapshot':source['snapshot_id'],'render':'NOT_RUN',
            'scope':'Reproducible installation only; not whole-page visual acceptance or live MCP connectivity.'}
    if a.render:
        config=json.loads((ROOT/'.local/project.json').read_text())
        flutter=config['flutter'];png=output/'withdraw-production.png'
        env={**os.environ,'WITHDRAW_2_OUTPUT':str(png)}
        subprocess.run([flutter,'test','test/withdraw_2_render_test.dart','--no-pub'],cwd=ROOT/'flutter_ui_components',env=env,check=True)
        reference=Image.open(example/'baseline-production.png').convert('RGB')
        actual=Image.open(png).convert('RGB')
        if actual.size!=reference.size:raise ValueError('Rendered canvas differs from frozen baseline')
        diff=ImageChops.difference(reference,actual)
        mae=sum(ImageStat.Stat(diff).mean)/3
        report.update(render='PASS' if mae<=manifest['reproduction_max_mae'] else 'FAIL',
                      baseline_mae=round(mae,6),threshold=manifest['reproduction_max_mae'],
                      artifact=str(png.relative_to(ROOT)))
        comparison=Image.new('RGB',(actual.width*2+40,actual.height),(242,243,245))
        comparison.paste(reference,(0,0));comparison.paste(actual,(actual.width+40,0))
        comparison.save(output/'reproduction-comparison.png')
    (output/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(report,ensure_ascii=False,indent=2))
    return 2 if report['render']=='FAIL' else 0


if __name__=='__main__':raise SystemExit(main())
