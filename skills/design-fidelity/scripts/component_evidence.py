"""Source-group evidence with explicit dependencies and reversible compression.

This is an implementation input, never a detector or an acceptance receipt.
Groups come from source hierarchy; flat sibling content must be selected explicitly.
"""
from collections import Counter
from copy import deepcopy
import json
import os
from pathlib import Path

from fidelity_contract import inventory, read_json, sha256
from scene_requirements import backdrop_blur
from source_disposition import disposition_groups


def packed(value):
    return json.dumps(value,ensure_ascii=False,separators=(',',':'))


def node_aliases(nodes):
    reserved=set(nodes)|{n.get('parent_id') for n in nodes.values() if n.get('parent_id')}
    prefix='@n'
    while any(key.startswith(prefix) for key in reserved):
        prefix='@'+prefix
    keys=sorted(nodes,key=lambda k:(nodes[k].get('source_order')
                if isinstance(nodes[k].get('source_order'),(int,float)) else float('inf'),k))
    return {key:prefix+str(i+1) for i,key in enumerate(keys)}


def map_references(value,mapping,field='',used=None):
    """Rewrite declared identity fields only; never rewrite user text or numbers."""
    used=set() if used is None else used
    def ref(v):
        if isinstance(v,str) and v in mapping:
            used.add(v)
            return mapping[v]
        return v
    if isinstance(value,list):
        return [ref(v) if field in ('node_ids','roots') else map_references(v,mapping,field,used)
                for v in value]
    if isinstance(value,dict):
        return {(ref(k) if field in ('samples','dependency_candidates') else k):
                map_references(v,mapping,k,used) for k,v in value.items()}
    if field in ('node_id','parent_id','owner_candidate','asset_owner_candidate'):
        return ref(value)
    if field=='id' and isinstance(value,str):
        # Scene IDs consist of a node identity plus a stable obligation suffix.
        for key in sorted(mapping,key=len,reverse=True):
            if value.startswith(key+'/'):
                used.add(key)
                suffix=value[len(key):]
                # Boundary obligations also carry the mask ID after /boundary/.
                for original,alias in mapping.items():
                    if suffix.endswith('/'+original):
                        used.add(original)
                        suffix=suffix[:-len(original)]+alias
                        break
                return mapping[key]+suffix
    return value


def unpack_packet(packet):
    content={k:v for k,v in packet.items() if k!='node_aliases'}
    return map_references(content,packet.get('node_aliases',{}))


def factor_styles(groups):
    """Factor only keys present in every style. Absence is never a default value."""
    if not groups:
        return {}, []
    common=set.intersection(*(set(g['style']) for g in groups))
    defaults={}
    for key in sorted(common):
        counts=Counter(packed(g['style'][key]) for g in groups)
        value,count=counts.most_common(1)[0]
        if count>1:
            defaults[key]=json.loads(value)
    result=[{'overrides':{k:v for k,v in g['style'].items()
                         if k not in defaults or packed(v)!=packed(defaults[k])},
             'instances':g['instances']} for g in groups]
    if len(packed([defaults,result])) >= len(packed([{},groups])):
        return {}, [{'overrides':g['style'],'instances':g['instances']} for g in groups]
    return defaults,result


def expand_brief(packet):
    """Decode the view exactly, used to verify no source facts were discarded."""
    result=deepcopy(unpack_packet(packet)['brief'])
    defaults=result.pop('visual_style_defaults')
    result['visual_style_groups']=[{'style':{**defaults,**g['overrides']},
                                   'instances':g['instances']} for g in result['visual_style_groups']]
    base=result.pop('asset_base_dir')
    for asset in result['assets']:
        if 'path_relative' in asset:
            asset['path']=str(Path(base)/asset.pop('path_relative'))
    return result


def descendants(nodes,roots):
    selected=set(roots)
    while True:
        expanded=selected|{k for k,n in nodes.items() if n.get('parent_id') in selected}
        if expanded==selected:
            return selected
        selected=expanded


def overlaps(a,b):
    return (min(a['x']+a['width'],b['x']+b['width']) > max(a['x'],b['x']) and
            min(a['y']+a['height'],b['y']+b['height']) > max(a['y'],b['y']))


def paint_bounds(node):
    b=node.get('bounds') or {};raw=node.get('raw_style') or {};origin=raw.get('ddsOriginFrame') or {}
    if all(k in raw for k in ('influenceLeft','influenceTop','influenceWidth','influenceHeight')) and all(k in origin for k in ('x','y')):
        return {'x':raw['influenceLeft']-origin['x']+b['x'],
                'y':raw['influenceTop']-origin['y']+b['y'],
                'width':raw['influenceWidth'],'height':raw['influenceHeight']}
    return b


def closure(nodes,roots,scenes):
    if not roots or set(roots)-nodes.keys():
        raise ValueError('Select existing source-group node IDs, or all')
    selected=descendants(nodes,roots)
    included=set(selected)
    reasons={}

    def add(key,reason):
        if key not in nodes:
            return
        included.add(key)
        if key not in selected:
            reasons.setdefault(key,set()).add(reason)

    while True:
        before=set(included)
        for key in list(included):
            parent=nodes[key].get('parent_id')
            if parent:
                add(parent,'ancestor')
        for scene in scenes:
            if set(scene['node_ids']) & included:
                for key in scene['node_ids']:
                    add(key,'scene:'+scene['kind'])
        for key in list(included):
            n=nodes[key];raw=n.get('raw_style') or {};bounds=n.get('bounds') or {}
            if not all(k in bounds for k in ('x','y','width','height')):
                continue
            if backdrop_blur(raw):
                # Conservative candidates, not a claim that geometry proves rendering.
                for other,m in nodes.items():
                    b=paint_bounds(m)
                    if (m.get('effective_source_visible',m.get('source_visible')) is False
                        or not all(k in b for k in ('x','y','width','height'))):
                        continue
                    order,prior=n.get('source_order'),m.get('source_order')
                    behind=(not isinstance(order,(int,float)) or not isinstance(prior,(int,float)) or prior<order)
                    if other!=key and behind and overlaps(bounds,b):
                        add(other,'backdrop_overlap_candidate')
            # Sibling mask chains depend on source ordering and break flags. Include
            # the candidate chain instead of guessing the exact clipping semantics.
            siblings=[(k,m) for k,m in nodes.items() if m.get('parent_id')==n.get('parent_id')]
            masks=[k for k,m in siblings if (m.get('raw_style') or {}).get('hasClippingMask')]
            if masks and (key in selected or raw.get('hasClippingMask')):
                for other,_ in siblings:
                    for candidate in descendants(nodes,[other]):
                        add(candidate,'mask_chain_candidate')
        if before==included:
            return selected,included,{k:sorted(v) for k,v in reasons.items()}


def scenes_flat(brief):
    return [{**{k:v for k,v in g.items() if k!='instances'},**i}
            for g in brief['scene_requirements'] for i in g['instances']]


def subset_brief(brief,included):
    result=deepcopy(brief)
    for section in ('text_style_groups','visual_style_groups'):
        groups=[]
        for group in result[section]:
            group['instances']=[i for i in group['instances'] if i['node_id'] in included]
            if group['instances']:
                groups.append(group)
        result[section]=groups
    for section in ('assets','missing_bitmaps'):
        result[section]=[v for v in result[section] if v['node_id'] in included]
    effects=[]
    for effect in result['effect_requirements']:
        effect['node_ids']=[k for k in effect['node_ids'] if k in included]
        effect['samples']={k:v for k,v in effect['samples'].items() if k in included}
        if effect['node_ids']:
            effects.append(effect)
    result['effect_requirements']=effects
    groups=[]
    for g in result['scene_requirements']:
        g['instances']=[i for i in g['instances'] if set(i['node_ids']) & included]
        if g['instances']:
            groups.append(g)
    result['scene_requirements']=groups
    ids={i['node_id'] for key in ('text_style_groups','visual_style_groups')
         for g in result[key] for i in g['instances']}
    result['inventory_count']=len(ids)
    return result


def component_packet(brief,nodes,plan,roots):
    all_page=roots==['all']
    roots=list(nodes) if all_page else roots
    selected,included,reasons=closure(nodes,roots,scenes_flat(brief))
    source=subset_brief(brief,included)
    normalized=deepcopy(source)
    defaults,groups=factor_styles(normalized['visual_style_groups'])
    normalized['visual_style_defaults']=defaults
    normalized['visual_style_groups']=groups
    paths=[a['path'] for a in normalized['assets'] if a.get('path')]
    base=os.path.commonpath([str(Path(p).parent) for p in paths]) if paths else ''
    normalized['asset_base_dir']=base
    for asset in normalized['assets']:
        if asset.get('path'):
            asset['path_relative']=str(Path(asset.pop('path')).relative_to(base))
    known=inventory(nodes)
    # Non-painting parent groups still establish frames and visibility. Preserve
    # unknown visibility instead of synthesizing neutral metadata to pass gates.
    frame_roots=({k for k,n in nodes.items() if n.get('parent_id') not in nodes} if all_page else set(roots))
    frames=[{k:n.get(k) for k in ('node_id','parent_id','name','bounds','source_order',
                                 'source_visible','effective_source_visible')}
            for key,n in nodes.items() if key in included and (key not in known or key in frame_roots)]
    text_runs=[{'node_id':n['node_id'],'runs':n['runs']} for n in plan['nodes']
               if n['node_id'] in included and len(n.get('runs',[]))>1]
    original={a['node_id'] for a in source['assets'] if a.get('kind')=='exported_asset'}
    geometries=[{'node_id':key,'pointer':'/raw_style/points'} for key,n in nodes.items()
                if key in included and key not in original and (n.get('raw_style') or {}).get('points')]
    result={'schema_version':1,'scope':'implementation evidence; not acceptance',
            'encoding':'node_aliases maps short IDs to source IDs; visual style = defaults + overrides; asset path = base_dir / path_relative',
            'source_pins':plan.get('pinned_inputs',{}),
            'selection':{'roots':['all'] if all_page else roots,
                         'hierarchy_only':True,'selected_nodes':len(selected),
                         'included_nodes':len(included),'unselected_page_inventory':len(set(known)-included)},
            'dependency_candidates':reasons,'parent_frames':frames,
            'source_decision_groups':disposition_groups(sorted(set(known) & included), nodes),
            'mixed_text_runs':text_runs,'geometry_refs':geometries,
            'issues':[i for i in plan['issues'] if not i.get('node_id') or i['node_id'] in included],
            'brief':normalized}
    mapping=node_aliases(nodes);used=set()
    encoded=map_references(result,mapping,used=used)
    encoded['node_aliases']={mapping[key]:key for key in mapping if key in used}
    if unpack_packet(encoded)!=result:
        raise ValueError('Node reference compression failed lossless reconstruction')
    if json.dumps(expand_brief(encoded),sort_keys=True)!=json.dumps(source,sort_keys=True):
        raise ValueError('Component compression failed lossless reconstruction')
    return encoded


def component_index(nodes,brief):
    parents={n.get('parent_id') for n in nodes.values()}
    mapping=node_aliases(nodes)
    return {'source':brief['source'],'page_inventory':brief['inventory_count'],
            'note':'Source groups are navigation, not inferred business components. Flat siblings may require multiple selected roots; all includes the whole page.',
            'components':[{'node_id':mapping[key],'name':n.get('name'),'bounds':n.get('bounds'),
                           'descendant_count':len(descendants(nodes,[key]))}
                          for key,n in nodes.items() if key in parents],
            'views':['component --component NODE_ID (repeat for flat siblings)','component --component all']}


def write_component(folder,evidence,roots=None):
    """Immutable prepared-source query; refuse stale source, font or reference inputs."""
    import hashlib
    from visual_fidelity_gate import _load_nodes
    folder=Path(folder)
    plan=read_json(folder/'page-plan.json')
    for path,digest in plan.get('pinned_inputs',{}).items():
        if sha256(path)!=digest:
            raise ValueError('Prepared source changed; rerun prepare before component inspection')
    expected={str(Path(p).resolve()) for p in evidence}
    if not expected <= set(plan.get('pinned_inputs',{})):
        raise ValueError('Component evidence differs from prepared inputs')
    brief=read_json(folder/'implementation-brief.json')
    nodes=_load_nodes(evidence)
    if roots is None:
        data=component_index(nodes,brief)
        filename='component-index.json'
    else:
        reverse={v:k for k,v in node_aliases(nodes).items()}
        roots=[reverse.get(k,k) for k in roots]
        if 'all' in roots and roots!=['all']:
            raise ValueError('all cannot be combined with individual roots')
        data=component_packet(brief,nodes,plan,roots)
        key=hashlib.sha256(packed(sorted(roots)).encode()).hexdigest()[:16]
        filename=f'component-{key}.json'
    path=folder/filename
    content=packed(data)+'\n'
    if path.exists() and path.read_text()!=content:
        raise ValueError('Prepared component changed; preserve prior artifacts and rerun prepare')
    if not path.exists():
        path.write_text(content)
    return path
