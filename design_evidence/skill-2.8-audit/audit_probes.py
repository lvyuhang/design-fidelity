"""Audit only: deliberately weak coverage must not be mistaken for full fidelity."""
import importlib.util
import json
from pathlib import Path
import sys
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[2]
SKILL = Path('/Users/tan/.codex/skills/lanhu-design-fidelity')
sys.path.insert(0, str(SKILL/'scripts'))
spec = importlib.util.spec_from_file_location('fixture', SKILL/'tests/test_fidelity.py')
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
from preflight import check
from fidelity_contract import inventory, sha256
from visual_fidelity_gate import _load_nodes
OUT = Path(__file__).resolve().parent
results = []

def sync(t):
    (t.root/'source.json').write_text(json.dumps(t.e))
    for path in ['source.json','reference.png']:
        t.c['pinned_files'][path] = sha256(t.root/path)

def probe(name, change):
    t = m.GateTests(); t.setUp()
    try:
        change(t); sync(t)
        render = t.render()
        if render.returncode: raise RuntimeError(render.stderr)
        proc, report = t.gate()
        result = {'probe':name,'exit_code':proc.returncode,'status':report['status'],
                  'whole_region':report.get('candidates',{}).get('test',{}).get('regions',{}).get('whole')}
        results.append(result)
        (OUT/(name+'.json')).write_text(json.dumps(report,ensure_ascii=False,indent=2))
    finally: t.doCleanups()

probe('baseline', lambda t: None)

def missing_shadow(t):
    t.e['nodes'][0]['parent_id']='surface'; t.e['nodes'][1]['parent_id']='surface'
    t.e['nodes'][2]['bounds']['height']=80
    t.e['nodes'][2]['raw_style']={'shadow':[{'isEnabled':True,'blurRadius':8,'offsetY':5}]}
    im=Image.open(t.root/'reference.png'); ImageDraw.Draw(im).rectangle((10,80,89,84),fill=(245,235,215)); im.save(t.root/'reference.png')
probe('missing_parent_shadow', missing_shadow)

def missing_decoration(t, grouped=False):
    t.e['nodes'].append({'node_id':'quote','node_type':'shape','bounds':{'x':80,'y':20,'width':4,'height':3}})
    t.c['source_scope']['expected_node_count']=4
    t.c['regions']['whole']['node_ids']=['surface','quote'] if grouped else ['quote']
    t.c['coverage']['quote']={'status':'covered','checks':['regions.whole']}
    im=Image.open(t.root/'reference.png'); ImageDraw.Draw(im).rectangle((80,20,83,22),fill=(216,187,120)); im.save(t.root/'reference.png')
probe('missing_independent_decoration', missing_decoration)
probe('missing_grouped_decoration', lambda t: missing_decoration(t, grouped=True))

t = m.GateTests(); t.setUp()
try:
    t.e['nodes'][1]['text_spec']={'base_style':{'font_family':'Fixture','font_size':10,'line_height':10,'color':'#000000'}}
    t.e['nodes'][2]['node_type']='shape'
    sync(t); t.save()
    r=check(t.root/'contract.json', require_style_evidence=True)
    results.append({'probe':'strict_styles_without_shape_raw_style','status':r['status'],'style_gaps':r['style_gaps']})
finally: t.doCleanups()

spec=importlib.util.spec_from_file_location('old_contract',ROOT/'skills/lanhu-design-fidelity/scripts/fidelity_contract.py')
old=importlib.util.module_from_spec(spec); spec.loader.exec_module(old)
nodes=_load_nodes([ROOT/'design_evidence/full-page-models/source-part-1.json',ROOT/'design_evidence/full-page-models/source-part-2.json'])
ids=['11857F91-EAAB-4C0C-A518-9D0D2F73628B','A3FD2014-8642-473A-B0F5-4C17D694B015','D44A759A-F00C-4F91-B906-8D3AEA24B017','67A66F14-1BFC-4ED2-B7CC-CA53F587487F','D918BBDD-E8F9-4952-B1C0-818569C32B90']
a,b=old.inventory(nodes),inventory(nodes)
results.append({'probe':'actual_page_inventory_before_after','v2_7_1_count':len(a),'v2_8_0_count':len(b),'added':sorted(set(b)-set(a)), 'five_reported_missing_decorations_in_old':all(i in a for i in ids),'five_in_new':all(i in b for i in ids),'source_nodes_with_raw_style':sum(bool(n.get('raw_style')) for n in nodes.values())})
(OUT/'audit-results.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(results,ensure_ascii=False,indent=2))
