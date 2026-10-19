#!/usr/bin/env python3
"""Run a logged legacy diagnostic for the frozen 2026 platform evidence."""
from __future__ import annotations
import argparse, json, os, subprocess, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = Path('/Users/tan/.codex/skills/lanhu-design-fidelity/scripts')
sys.path.insert(0, str(SKILL))
from round_log import RoundLog
from fidelity_contract import sha256

def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--note',required=True)
    a=p.parse_args();out=a.output.resolve();out.mkdir(parents=True,exist_ok=False)
    contract=ROOT/'design_evidence/full-page-models/visual-contract.json'
    implementation=ROOT/'flutter_ui_components/lib/experiments/platform_intro_optimized_page.dart'
    test=ROOT/'flutter_ui_components/test/platform_intro_optimized_render_test.dart'
    log=RoundLog(ROOT/'design_evidence/platform-intro-optimized/task-run.json')
    ticket=log.begin(contract,out,a.note,command={'test':sha256(test),'implementation':sha256(implementation),'gate':'legacy diagnostic'})
    started=time.monotonic();stages=[];status='NOT_EVALUATED';gate_status='NOT_EVALUATED';failures=[]
    try:
        render=out/'render.png';begin=time.monotonic()
        r=subprocess.run(['flutter','test','--no-pub','test/platform_intro_optimized_render_test.dart'],
            cwd=ROOT/'flutter_ui_components',env={**os.environ,'PLATFORM_OPTIMIZED_OUTPUT':str(render)},
            stdout=(out/'render.log').open('w'),stderr=subprocess.STDOUT)
        stages.append({'name':'render','seconds':round(time.monotonic()-begin,3),'exit_code':r.returncode})
        if r.returncode: raise ValueError('Flutter render or interaction test failed')
        begin=time.monotonic();g=subprocess.run([sys.executable,str(ROOT/'tools/visual_fidelity_gate.py'),
            '--contract',str(contract),'--candidate',f'optimized={render}','--output-dir',str(out/'gate')],
            stdout=(out/'gate.log').open('w'),stderr=subprocess.STDOUT)
        stages.append({'name':'diagnostic_gate','seconds':round(time.monotonic()-begin,3),'exit_code':g.returncode})
        report=json.loads((out/'gate/visual-gate-report.json').read_text());candidate=report['candidates']['optimized']
        failures=[{'check':f'{group}.{key}','failures':value.get('failures',[])}
            for group in ('regions','features','relations','colors') for key,value in candidate[group].items() if not value['passed']]
        gate_status='DIAGNOSTIC_MATCH' if candidate['passed'] else 'DIAGNOSTIC_DIFFERENCES'
        status='DIAGNOSTIC';metrics={k:v['metrics'] for k,v in candidate['regions'].items()}
    except Exception as e:
        status='NOT_EVALUATED';error=str(e);metrics={}
    result={'status':status,'scope':'Legacy frozen v1 contract diagnostic; never a v2 visual PASS',
        'seconds':round(time.monotonic()-started,3),'gate_status':gate_status,'failures':failures,
        'metrics':metrics,'stages':stages,**({'error':error} if 'error' in locals() else {})}
    (out/'run.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');log.finish(ticket,result)
    print(json.dumps({'round':ticket['round_number'],'attempt':ticket['attempt_number'],**result},ensure_ascii=False))
    return 2  # Diagnostic history never grants current implementation acceptance.
if __name__=='__main__': raise SystemExit(main())
