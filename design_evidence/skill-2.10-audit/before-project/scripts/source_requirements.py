"""Source-derived obligations. Reference pixels, never implementation values, are the oracle."""
from __future__ import annotations
import math


def enabled(value):
    return isinstance(value, dict) and value.get('isEnabled', True) and value.get('enabled', True)


def visible(node):
    b = node.get('bounds') or {}
    return (node.get('effective_source_visible', node.get('source_visible')) is not False
            and b.get('width', 0) > 0 and b.get('height', 0) > 0)


def effects(node):
    raw = node.get('raw_style') or {}
    result = {}
    for field in ('shadow', 'shadows', 'innerShadows', 'blur', 'effects'):
        value = raw.get(field, node.get(field))
        values = value if isinstance(value, list) else [value] if isinstance(value, dict) else []
        for i, item in enumerate(values):
            if enabled(item):
                result[f'{field}:{i}'] = {'kind': 'shadow' if field in ('shadow','shadows') else 'local_effect', 'source': item}
    for field in ('fills', 'borders'):
        for i, item in enumerate(raw.get(field) or []):
            if not enabled(item): continue
            if item.get('type') == 'gradient' or item.get('fillType') == 1:
                result[f'{field}:{i}:gradient'] = {'kind': 'gradient', 'source': item.get('gradient', {})}
            if field == 'borders':
                result[f'{field}:{i}'] = {'kind': 'local_effect', 'source': item}
    # Lanhu raw node opacity is a percentage; fill opacity is a separate 0..1 field.
    if raw.get('opacity') not in (None, 100):
        result['opacity'] = {'kind': 'local_effect', 'source': {'opacity': raw['opacity']}}
    if raw.get('hasClippingMask'):
        result['mask'] = {'kind': 'local_effect', 'source': {'hasClippingMask': True}}
    return result


def source_gaps(nodes, text_styles=False):
    gaps = []
    for key, node in nodes.items():
        if not visible(node): continue
        raw = node.get('raw_style') or {}
        if not node.get('text') and not set(raw).intersection({'fills','borders','shadow','shadows','opacity','points','hasClippingMask','effects','blur'}):
            gaps.append({'node_id': key, 'missing': ['raw_style'], 'kind': 'visual_source_unknown'})
        if text_styles and node.get('text'):
            font = raw.get('font') or {}
            spec = (node.get('text_spec') or {}).get('base_style') or {}
            fields = {'font_family': spec.get('font_family') or font.get('font'),
                      'font_size': spec.get('font_size', font.get('size')),
                      'line_height': spec.get('line_height', font.get('line')),
                      'color': spec.get('color', font.get('color'))}
            missing = [k for k,v in fields.items() if v is None or v == '']
            if missing: gaps.append({'node_id': key, 'text': node['text'], 'missing': missing, 'kind': 'text_source_unknown'})
    return gaps


def is_small_visual(node):
    b = node['bounds']
    return (not node.get('text') and node.get('node_type') in ('shape','bitmap','shapePath','symbol')
            and (max(b['width'], b['height']) <= 96 or min(b['width'], b['height']) <= 4))


def _rect_at(x, y, size=1):
    # Align tiny ROIs to logical pixels; round-to-even could otherwise produce an empty 1px crop.
    return [math.floor(x), math.floor(y), size, size]


def sample_points(node, effect):
    """Only automate linear gradients and ordinary outer shadows; unsupported stays pending."""
    b, src = node['bounds'], effect['source']
    x,y,w,h = [b[k] for k in ('x','y','width','height')]
    if effect['kind'] == 'gradient':
        if src.get('type') not in (None, 'linear') or src.get('gradientType',0) != 0: return []
        a,z = src.get('from',{}), src.get('to',{})
        if not {'x','y'} <= a.keys() or not {'x','y'} <= z.keys(): return []
        if a == z: return []
        return [{'role': role, 'rect': _rect_at(x+(a['x']+(z['x']-a['x'])*t)*w,
                                             y+(a['y']+(z['y']-a['y'])*t)*h)}
                for role,t in [('start',.1),('middle',.5),('end',.9)]]
    if effect['kind'] == 'shadow':
        blur = src.get('blurRadius',src.get('blur'))
        if not isinstance(blur,(int,float)) or blur <= 0: return []
        dx,dy = src.get('offsetX',0),src.get('offsetY',0)
        spread = max(0,src.get('spread',0))
        horizontal = abs(dx) > abs(dy)
        sign = 1 if (dx if horizontal else dy) >= 0 else -1
        distance = abs(dx if horizontal else dy)+spread
        edge_x,edge_y = ((x+w if sign>0 else x, y+h/2) if horizontal
                        else (x+w/2,y+h if sign>0 else y))
        return [{'role':role,'rect':_rect_at(edge_x+(sign*d if horizontal else 0),
                                           edge_y+(0 if horizontal else sign*d))}
                for role,d in [('edge',.5),('peak',max(1,distance)),('tail',max(2,distance+blur))]]
    return []


def requirements(nodes, canvas):
    result = []
    for key,n in nodes.items():
        if not visible(n): continue
        for effect_key, effect in effects(n).items():
            samples = sample_points(n,effect)
            in_canvas = lambda r: r[0]>=0 and r[1]>=0 and r[0]+r[2]<=canvas[0] and r[1]+r[3]<=canvas[1]
            result.append({'node_id':key,'effect_key':effect_key,'kind':effect['kind'],
                           'samples':samples if samples and all(in_canvas(s['rect']) for s in samples) else [],
                           'needs_review':True})
    return result


def add_sample_drafts(c, nodes, tolerance):
    """Explicit opt-in; creates candidates without marking the contract ready."""
    if not isinstance(tolerance,(int,float)) or not math.isfinite(tolerance) or tolerance < 0:
        raise ValueError('auto_effect_samples.max_channel_delta must be finite and nonnegative')
    samples = c.setdefault('color_samples',{})
    existing = {(s.get('effect',{}).get('node_id'),s.get('effect',{}).get('key'),s.get('effect',{}).get('role')) for s in samples.values()}
    for r in requirements(nodes,c['canvas']):
        for s in r['samples']:
            identity = (r['node_id'],r['effect_key'],s['role'])
            if identity in existing: continue
            name = 'effect__'+'__'.join(identity)
            if name in samples: raise ValueError(f'Generated sample name collision: {name}')
            samples[name]={'label':name,'node_ids':[r['node_id']], 'rect':s['rect'],
                           'effect':{'node_id':r['node_id'],'key':r['effect_key'],'role':s['role']},
                           'max_channel_delta':tolerance}


def _sample_rect(spec, node):
    if 'rect' in spec: return spec['rect']
    b=node['bounds']; a=spec.get('anchor',[.5,.5]); size=spec.get('size',[1,1])
    return [b['x']+b['width']*a[0]-size[0]/2,b['y']+b['height']*a[1]-size[1]/2,*size]


def _reviewed_sample_position(spec, actual, expected, node, effect):
    """Allow an exposed point on the same gradient band/shadow edge, with review evidence."""
    a = [actual[0]+actual[2]/2, actual[1]+actual[3]/2]
    e = [expected[0]+expected[2]/2, expected[1]+expected[3]/2]
    if max(abs(a[i]-e[i]) for i in (0,1)) <= 1: return True
    if not spec.get('review_reason','').strip(): return False
    b=node['bounds']; src=effect['source']
    if effect['kind']=='gradient':
        dx=(src['to']['x']-src['from']['x'])*b['width']
        dy=(src['to']['y']-src['from']['y'])*b['height']
        length=math.hypot(dx,dy)
        return (b['x']<=a[0]<=b['x']+b['width'] and b['y']<=a[1]<=b['y']+b['height']
                and abs((a[0]-e[0])*dx+(a[1]-e[1])*dy)/length<=1)
    if effect['kind']=='shadow':
        horizontal=abs(src.get('offsetX',0))>abs(src.get('offsetY',0))
        normal,tangent=(0,1) if horizontal else (1,0)
        lo=b['y'] if horizontal else b['x']; span=b['height'] if horizontal else b['width']
        return abs(a[normal]-e[normal])<=1 and lo<=a[tangent]<=lo+span
    return False


def validate_obligations(c, nodes, selected):
    if c.get('workflow_version') != 1:
        raise ValueError('Missing workflow_version: 1; migrate with reviewed node_decisions (legacy: diagnostic only)')
    gaps = source_gaps(nodes, text_styles=True)
    if gaps:
        first=gaps[0]
        raise ValueError(f"Source evidence unknown: {len(gaps)} nodes; {first['node_id']} nodes lack source styles ({first['missing']}); inspect before acceptance")
    decisions=c.get('node_decisions',{})
    if set(decisions) != set(selected):
        raise ValueError('node_decisions must match visible inventory; no missing or stale decisions')
    required_effects=requirements(nodes,c['canvas'])
    for key,node in selected.items():
        d=decisions[key]; mode=d.get('mode'); excluded=c['coverage'][key].get('status')=='excluded'
        if mode not in ('native_exact','original_asset','render_fallback','missing_asset_placeholder','excluded_with_reason'):
            raise ValueError(f'{key}: unresolved implementation decision')
        if excluded != (mode in ('missing_asset_placeholder','excluded_with_reason')):
            raise ValueError(f'{key}: exclusion and implementation decision disagree')
        if mode != 'excluded_with_reason':
            if d.get('implementation') not in c.get('implementation_inputs',[]) or not d.get('symbol','').strip():
                raise ValueError(f'{key}: implementation file and symbol required')
        if mode in ('original_asset','render_fallback') and d.get('asset') not in c.get('assets',[]):
            raise ValueError(f'{key}: original/render asset must be pinned')
        if excluded:
            if not d.get('reason','').strip(): raise ValueError(f'{key}: exclusion reason required')
            if mode=='missing_asset_placeholder' and d.get('shape') not in ('circle','rounded_rect','rect','source_path'):
                raise ValueError(f'{key}: placeholder must declare source shape')
            continue
        if is_small_visual(node):
            checks=[c.get('features',{}).get(ref.partition('.')[2],{}) for ref in c['coverage'][key]['checks'] if ref.startswith('features.')]
            if not any(s.get('node_ids')==[key] and s.get('profile')=='small_visual' for s in checks):
                raise ValueError(f'{key}: small visual requires an independent small_visual feature')
    # An enabled source effect cannot be satisfied by an unrelated center-color or whole-page region.
    tagged={}
    for name,s in c.get('color_samples',{}).items():
        e=s.get('effect')
        if not e: continue
        key=e.get('node_id'); effect_key=e.get('key')
        if key not in nodes or effect_key not in effects(nodes[key]): raise ValueError(f'{name}: unknown source effect')
        if not s.get('blocking',True) or s.get('node_ids')!=[key]: raise ValueError(f'{name}: effect sample must block and target one node')
        r=_sample_rect(s,nodes[key])
        if r[2] > 4 or r[3] > 4: raise ValueError(f'{name}: effect sample is too broad')
        identity=(key,effect_key,e.get('role'))
        if identity in tagged: raise ValueError(f'{name}: duplicate effect role')
        tagged[identity]=(r,s)
    for req in required_effects:
        key,ek=req['node_id'],req['effect_key']
        if c['coverage'].get(key,{}).get('status')=='excluded': continue
        expected=req['samples']
        if not expected:
            # Complex/occluded/clipped effects require a precise local pixel check, explicitly reviewed.
            valid=False
            for s in c.get('regions',{}).values():
                if s.get('effect')=={'node_id':key,'key':ek} and s.get('node_ids')==[key] and s.get('blocking',True) and s.get('review_reason','').strip():
                    valid=True
            if not valid: raise ValueError(f'{key}/{ek}: needs reviewed local effect region; automatic samples unavailable')
            continue
        for sample in expected:
            role=sample['role']; actual=tagged.get((key,ek,role))
            if not actual: raise ValueError(f'{key}/{ek}: missing effect sample {role}')
            a,spec=actual
            if not _reviewed_sample_position(spec,a,sample['rect'],nodes[key],effects(nodes[key])[ek]):
                raise ValueError(f'{key}/{ek}/{role}: sample outside source-derived position')
        centers={(round(tagged[(key,ek,s['role'])][0][0],4),round(tagged[(key,ek,s['role'])][0][1],4)) for s in expected}
        if len(centers)<3: raise ValueError(f'{key}/{ek}: effect samples must be distinct')
    return {'effect_obligations':len(required_effects),'implementation_decisions':len(decisions),'unaccounted_visible_nodes':0}
