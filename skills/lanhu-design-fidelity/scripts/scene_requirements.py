"""Source-derived scene dependencies, with executable project checks.

These checks supplement reference pixels when placeholders hide compositing.
No project names, node IDs or renderer-specific implementation live here.
"""
from __future__ import annotations
import math
import subprocess
import time
from pathlib import Path


def backdrop_blur(raw):
    blur = raw.get('blur') or {}
    return (blur.get('isEnabled', True) and blur.get('enabled', True)
            and (blur.get('blurType') == 3 or blur.get('type') in
                 ('背景模糊', 'background', 'backdrop', 'backgroundBlur')))


def _visible(n):
    b = n.get('bounds') or {}
    return (n.get('effective_source_visible', n.get('source_visible')) is not False
            and b.get('width', 0) > 0 and b.get('height', 0) > 0)


def scene_requirements(nodes):
    result = []
    masks = {k:n for k,n in nodes.items() if _visible(n)
             and (n.get('raw_style') or {}).get('hasClippingMask')}
    for key, n in nodes.items():
        if not _visible(n): continue
        raw = n.get('raw_style') or {}
        if backdrop_blur(raw):
            result.append({'id':key+'/backdrop', 'kind':'backdrop', 'node_ids':[key],
                           'verify':['source_parameters', 'backdrop_response', 'clip_extent']})
        if key in masks:
            result.append({'id':key+'/clip', 'kind':'clip', 'node_ids':[key],
                           'verify':['source_geometry', 'clip_scope']})
        # An exported sibling crossing a mask boundary may be the silhouette,
        # rim, floating action or shadow. Do not absorb it into that mask.
        if not n.get('asset_ids'): continue
        b = n['bounds']
        for mask_key, mask in masks.items():
            a = mask['bounds']
            overlap = (min(a['x']+a['width'],b['x']+b['width']) > max(a['x'],b['x'])
                       and min(a['y']+a['height'],b['y']+b['height']) > max(a['y'],b['y']))
            contained = (a['x'] <= b['x'] and a['y'] <= b['y'] and
                         b['x']+b['width'] <= a['x']+a['width']+.001 and
                         b['y']+b['height'] <= a['y']+a['height']+.001)
            order, mo = n.get('source_order'), mask.get('source_order')
            if (overlap and not contained and b['width']*b['height'] < a['width']*a['height']
                    and n.get('parent_id') != mask.get('parent_id')
                    and isinstance(order,(int,float)) and isinstance(mo,(int,float)) and order > mo):
                result.append({'id':key+'/boundary/'+mask_key, 'kind':'boundary_overlay',
                               'node_ids':[key,mask_key],
                               'verify':['asset_frame', 'source_order', 'clip_scope', 'visible_contour']})
    return result


def validate_scene_checks(c, nodes):
    """A declaration cannot satisfy a scene obligation without a runnable test."""
    required = {r['id']:r for r in scene_requirements(nodes)}
    # Missing content is not nonvisibility. It cannot waive clips/overlays/blur.
    for key, d in c.get('node_decisions',{}).items():
        if d.get('mode') == 'missing_asset_placeholder':
            from source_requirements import effects
            for effect_key in effects(nodes[key]):
                identity = key+'/placeholder_effect/'+effect_key
                required[identity] = {'id':identity,'kind':'placeholder_effect','node_ids':[key],
                                      'verify':['source_parameters','isolated_render']}
    required = {k:r for k,r in required.items() if not all(
        c.get('node_decisions',{}).get(n,{}).get('mode') == 'excluded_with_reason'
        for n in r['node_ids'])}
    covered = set()
    for name, check in c.get('scene_checks',{}).items():
        bindings = check.get('obligations',[])
        if not bindings or len(bindings) != len(set(bindings)) or set(bindings)-required.keys():
            raise ValueError(f'{name}: scene check has unknown/duplicate/empty obligations')
        command = check.get('command')
        if not isinstance(command,list) or not command or not all(isinstance(s,str) and s for s in command):
            raise ValueError(f'{name}: scene check requires argv, not shell text')
        if not isinstance(check.get('cwd','.'),str) or not check.get('cwd','.'):
            raise ValueError(f'{name}: scene check cwd must be a path')
        test = check.get('test_file')
        if test not in c.get('implementation_inputs',[]) or not check.get('assertions','').strip():
            raise ValueError(f'{name}: scene test file must be hashed with implementation; explain observable assertions')
        timeout = check.get('timeout_seconds',60)
        if isinstance(timeout,bool) or not isinstance(timeout,(int,float)) or not math.isfinite(timeout) or not 0 < timeout <= 300:
            raise ValueError(f'{name}: scene check timeout must be in (0,300]')
        covered.update(bindings)
    if set(required)-covered:
        raise ValueError('Unverified scene dependencies: '+', '.join(sorted(set(required)-covered))+
                         '; add source-bound scene_checks; missing content is not an exemption')
    return set(required)


def run_scene_checks(c, directory):
    results = {}
    for name, check in c.get('scene_checks',{}).items():
        started = time.monotonic()
        run = subprocess.run(check['command'], cwd=Path(directory)/check.get('cwd','.'), capture_output=True,
                             text=True, timeout=check.get('timeout_seconds',60), check=False)
        if run.returncode:
            raise ValueError(f'Scene check {name} failed ({run.returncode}):\n'+
                             (run.stdout+run.stderr)[-6000:])
        results[name] = {'command':check['command'], 'exit_code':0,
                         'cwd':check.get('cwd','.'),
                         'obligations':check['obligations'], 'seconds':round(time.monotonic()-started,4)}
    return results


def verify_scene_receipt(receipt, c):
    results = receipt.get('scene_checks',{})
    if set(results) != set(c.get('scene_checks',{})):
        raise ValueError('Missing or stale scene-check results in render receipt')
    for name, check in c.get('scene_checks',{}).items():
        r = results[name]
        if (r.get('exit_code') != 0 or r.get('command') != check['command']
                or r.get('cwd') != check.get('cwd','.') or r.get('obligations') != check['obligations']):
            raise ValueError(f'{name}: scene check did not succeed for this contract')
