"""Source-derived obligations. Reference pixels, never implementation values, are the oracle."""
from __future__ import annotations
import math
from pending_assets import pending_allowed
from scene_requirements import backdrop_blur, validate_scene_checks
from source_disposition import placeholder_issue
from system_chrome import chrome_members


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
                kind = 'shadow' if field in ('shadow','shadows') else 'local_effect'
                if field == 'blur' and backdrop_blur(raw): kind = 'backdrop'
                result[f'{field}:{i}'] = {'kind': kind, 'source': item}
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


def source_gaps(nodes, text_styles=False, decisions=None, assets=()):
    gaps = []
    chrome = chrome_members(nodes)
    for key, node in nodes.items():
        if not visible(node): continue
        if key in chrome: continue  # OS-drawn; reserved, never implemented or traced.
        raw = node.get('raw_style') or {}
        explicit_empty_artboard = node.get('node_type') in ('artboard', 'artboard-group') and raw.get('hasBackgroundColor') is False
        if not explicit_empty_artboard and not node.get('text') and not set(raw).intersection({'fills','borders','shadow','shadows','opacity','points','hasClippingMask','effects','blur'}):
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
        # A source-driven renderer cannot recover a painted shape from color
        # metadata alone.  Bounds describe layout, not the vector silhouette.
        # Require original geometry/asset (or a later explicit reviewed
        # fallback) before implementation instead of letting a model guess.
        paints = [item for field in ('fills', 'borders')
                  for item in (raw.get(field) or []) if enabled(item)]
        has_effect = bool(effects(node))
        has_geometry = bool(raw.get('points') or raw.get('path') or node.get('path'))
        if (not node.get('text') and node.get('node_type') in ('shape', 'shapePath')
                and (paints or has_effect) and not has_geometry
                and not geometry_resolved(key, nodes, decisions, assets)):
            gaps.append({'node_id': key, 'missing': ['vector_geometry_or_original_asset'],
                         'kind': 'geometry_source_unknown'})
    return gaps


def geometry_resolved(key, nodes, decisions=None, assets=()):
    """Source asset ancestry is a preparation candidate, not acceptance proof.

    Once decisions exist, require this node's declared asset/placeholder or
    nonvisibility disposition. Existing obligation checks validate that
    disposition, pinned files, shape, effects and visual coverage separately.
    """
    if decisions is not None:
        d = decisions.get(key, {})
        mode = d.get('mode')
        if mode in ('original_asset', 'render_fallback'):
            return bool(d.get('asset')) and d['asset'] in assets
        return mode in ('missing_asset_placeholder', 'excluded_with_reason')
    if pending_allowed(key, nodes):
        return True
    seen = set()
    while key in nodes and key not in seen:
        seen.add(key)
        node = nodes[key]
        if node.get('asset_ids'):
            return True
        key = node.get('parent_id')
    return False


def is_small_visual(node):
    b = node['bounds']
    raw = node.get('raw_style') or {}
    return (not node.get('text') and not raw.get('hasClippingMask')
            and node.get('node_type') in ('shape','bitmap','shapePath','symbol')
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


def _painted(node):
    raw = node.get('raw_style') or {}
    return bool(node.get('text') or node.get('asset_ids') or node.get('node_type') == 'bitmap'
                or any(enabled(v) for field in ('fills','borders') for v in raw.get(field, [])))


def _occluded(node, rect, nodes):
    order = node.get('source_order')
    if not isinstance(order, (int,float)):
        return False
    cx,cy = rect[0]+rect[2]/2, rect[1]+rect[3]/2
    for other in nodes.values():
        oo=other.get('source_order'); b=other.get('bounds') or {}
        if (other is node or not isinstance(oo,(int,float)) or oo <= order
                or not visible(other) or not _painted(other)):
            continue
        if b['x'] <= cx <= b['x']+b['width'] and b['y'] <= cy <= b['y']+b['height']:
            return True
    return False


def _exposed_sample(node, effect, sample, nodes):
    """Move a covered gradient sample along the same color band using source order only."""
    if not _occluded(node, sample['rect'], nodes) or effect['kind'] != 'gradient':
        return sample
    b,src=node['bounds'],effect['source']; a,z=src.get('from',{}),src.get('to',{})
    dx=(z.get('x',0)-a.get('x',0))*b['width']; dy=(z.get('y',0)-a.get('y',0))*b['height']
    length=math.hypot(dx,dy)
    if not length:
        return sample
    tx,ty=-dy/length,dx/length
    cx,cy=sample['rect'][0]+.5,sample['rect'][1]+.5
    limit=math.ceil(math.hypot(b['width'],b['height']))
    for distance in range(1,limit+1):
        for sign in (1,-1):
            rect=_rect_at(cx+tx*distance*sign,cy+ty*distance*sign)
            if (b['x'] <= rect[0] and b['y'] <= rect[1]
                    and rect[0]+1 <= b['x']+b['width'] and rect[1]+1 <= b['y']+b['height']
                    and not _occluded(node,rect,nodes)):
                return {**sample,'rect':rect,'review_reason':
                        'Automatic source-order relocation to an exposed point on the same gradient band.'}
    return sample


def requirements(nodes, canvas):
    result = []
    for key,n in nodes.items():
        if not visible(n): continue
        for effect_key, effect in effects(n).items():
            samples = [_exposed_sample(n,effect,s,nodes) for s in sample_points(n,effect)]
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


def validate_exclusion(key, decision, nodes, canvas):
    """Exclusions explain nonvisibility, never lack of implementation validation."""
    proof = decision.get('exclusion') or {}
    node = nodes[key]
    b = node['bounds']
    if proof.get('kind') == 'outside_canvas':
        if b['x']+b['width'] <= 0 or b['y']+b['height'] <= 0 or b['x'] >= canvas[0] or b['y'] >= canvas[1]:
            return
        raise ValueError(f'{key}: outside_canvas exclusion intersects the canvas')
    if proof.get('kind') == 'fully_occluded':
        occluder = nodes.get(proof.get('by'))
        if occluder and visible(occluder):
            raw = occluder.get('raw_style') or {}
            # Only a later, opaque, axis-aligned rectangle can be proved here.
            # Conservative central rectangle avoids asserting coverage in corners.
            points = raw.get('points') or []
            corners = {(p.get('point', {}).get('x'), p.get('point', {}).get('y')) for p in points}
            rectangle = corners == {(0,0),(1,0),(1,1),(0,1)} and not any(
                p.get('hasCurveTo') or p.get('hasCurveFrom') for p in points)
            solid = any(enabled(f) and f.get('type') == 'color' and
                        f.get('opacity', 1) == 1 and (f.get('color') or {}).get('a') == 1
                        for f in raw.get('fills', []))
            ancestry_opaque = True
            current = occluder
            seen = set()
            while current:
                identity = current.get('node_id', id(current))
                if identity in seen:
                    ancestry_opaque = False
                    break
                seen.add(identity)
                style = current.get('raw_style') or {}
                if style.get('opacity',100) != 100 or style.get('rotation',0) != 0 or style.get('blendMode',0) != 0 or style.get('hasClippingMask'):
                    ancestry_opaque = False
                current = nodes.get(current.get('parent_id'))
            a = occluder['bounds']
            radius = max(raw.get('radius') or [0])
            contained = (b['x'] >= a['x']+radius and b['y'] >= a['y']+radius and
                         b['x']+b['width'] <= a['x']+a['width']-radius and
                         b['y']+b['height'] <= a['y']+a['height']-radius)
            above = (isinstance(occluder.get('source_order'), (int,float)) and
                     isinstance(node.get('source_order'), (int,float)) and
                     occluder['source_order'] > node['source_order'])
            if rectangle and solid and ancestry_opaque and contained and above:
                return
        raise ValueError(f'{key}: fully_occluded needs a covering opaque source rectangle above the node')
    if proof.get('kind') == 'system_chrome':
        if key in chrome_members(nodes, canvas):
            return
        raise ValueError(f'{key}: system_chrome exclusion only applies to detected status bar / home indicator layers')
    raise ValueError(f'{key}: exclusion needs verifiable nonvisibility; unchanged/reused source is not an exemption. Reuse the checks, not an unchecked baseline')


def validate_visual_exclusion(key, decision, nodes, contract):
    """Allow pixel exclusion only when a verified foreground depends on a missing backdrop."""
    proof=decision.get('visual_exclusion') or {}
    if proof.get('kind')!='missing_backdrop':
        raise ValueError(f'{key}: unsupported visual_exclusion')
    backdrop_id=proof.get('by'); backdrop=nodes.get(backdrop_id); node=nodes[key]
    if (not backdrop or contract.get('node_decisions',{}).get(backdrop_id,{}).get('mode')!='missing_asset_placeholder'
            or not pending_allowed(backdrop_id,nodes)):
        raise ValueError(f'{key}: visual_exclusion backdrop must be a verified missing asset')
    a,b=node['bounds'],backdrop['bounds']
    overlap=max(0,min(a['x']+a['width'],b['x']+b['width'])-max(a['x'],b['x']))*max(0,min(a['y']+a['height'],b['y']+b['height'])-max(a['y'],b['y']))
    if overlap<=0 or node.get('source_order',-1)<=backdrop.get('source_order',-1):
        raise ValueError(f'{key}: visual_exclusion must identify a source-visible foreground above the missing backdrop')
    verification=proof.get('verification')
    if verification not in contract.get('implementation_inputs',[]) or not proof.get('assertion','').strip():
        raise ValueError(f'{key}: visual_exclusion requires a pinned executable verification and assertion')


def validate_obligations(c, nodes, selected):
    if c.get('workflow_version') != 1:
        raise ValueError('Missing workflow_version: 1; migrate with reviewed node_decisions (legacy: diagnostic only)')
    for key, decision in c.get('node_decisions', {}).items():
        if key in nodes and decision.get('mode') == 'missing_asset_placeholder':
            issue = placeholder_issue(key, nodes)
            if issue:
                raise ValueError(f"{issue['code']}: {key}; source_state={issue['source_state']}; "
                                 f"next_action={issue['next_action']}; {issue['message']}")
    gaps = source_gaps(nodes, text_styles=True,
                       decisions=c.get('node_decisions', {}), assets=c.get('assets', []))
    if gaps:
        first=gaps[0]
        raise ValueError(f"Source evidence unknown: {len(gaps)} nodes; {first['node_id']} nodes lack source styles ({first['missing']}); inspect before acceptance")
    decisions=c.get('node_decisions',{})
    if set(decisions) != set(selected):
        raise ValueError('node_decisions must match visible inventory; no missing or stale decisions')
    scene = validate_scene_checks(c, nodes)
    required_effects=requirements(nodes,c['canvas'])
    for key,node in selected.items():
        d=decisions[key]; mode=d.get('mode'); excluded=c['coverage'][key].get('status')=='excluded'
        visual_exclusion=bool(d.get('visual_exclusion'))
        if mode not in ('native_exact','original_asset','render_fallback','missing_asset_placeholder','excluded_with_reason'):
            raise ValueError(f'{key}: unresolved implementation decision')
        if excluded != (mode in ('missing_asset_placeholder','excluded_with_reason') or visual_exclusion):
            raise ValueError(f'{key}: exclusion and implementation decision disagree')
        if mode != 'excluded_with_reason':
            if d.get('implementation') not in c.get('implementation_inputs',[]) or not d.get('symbol','').strip():
                raise ValueError(f'{key}: implementation file and symbol required')
        if mode in ('original_asset','render_fallback') and d.get('asset') not in c.get('assets',[]):
            raise ValueError(f'{key}: original/render asset must be pinned')
        if excluded:
            if not d.get('reason','').strip(): raise ValueError(f'{key}: exclusion reason required')
            if visual_exclusion:
                validate_visual_exclusion(key,d,nodes,c)
            elif mode == 'excluded_with_reason':
                validate_exclusion(key, d, nodes, c['canvas'])
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
        if c['coverage'].get(key,{}).get('status')=='excluded':
            # Missing content retains effects via a fresh executable scene check.
            if decisions.get(key,{}).get('mode') == 'missing_asset_placeholder' and key+'/placeholder_effect/'+ek not in scene:
                raise ValueError(f'{key}/{ek}: placeholder cannot waive source effects')
            continue
        if (req['kind']=='backdrop' and key+'/backdrop' in scene) or (ek=='mask' and key+'/clip' in scene):
            continue
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
    return {'effect_obligations':len(required_effects),'scene_obligations':len(scene),'implementation_decisions':len(decisions),'unaccounted_visible_nodes':0}
