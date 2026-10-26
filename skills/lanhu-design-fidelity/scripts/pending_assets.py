"""Explicit user-authorized local missing-source policy. No source fields are edited."""
import json,os,hashlib
from pathlib import Path

def load_policy(location):
    policy = json.loads(Path(location).read_text())
    if (not isinstance(policy, dict) or policy.get('policy') != 'placeholder_after_reinspection'
            or not isinstance(policy.get('nodes'), dict)):
        raise ValueError('INVALID_PENDING_ASSETS: expected policy=placeholder_after_reinspection and nodes object; use assets/pending-assets.example.json')
    for key, item in policy['nodes'].items():
        if not isinstance(item, dict) or not item.get('reason') or not item.get('evidence'):
            raise ValueError(f'INVALID_PENDING_ASSETS: {key} requires reason and hashed reinspection evidence')
        for entry in item['evidence']:
            if not isinstance(entry, dict) or not entry.get('path') or not entry.get('sha256'):
                raise ValueError(f'INVALID_PENDING_ASSETS: {key} evidence requires path and sha256')
    return policy

def pending_allowed(key,nodes):
    location=os.environ.get('LANHU_PENDING_ASSETS')
    if not location:return False
    policy_path=Path(location).resolve()
    policy=load_policy(policy_path)
    item=policy.get('nodes',{}).get(key)
    if not item or policy.get('policy')!='placeholder_after_reinspection':return False
    node=nodes.get(key,{})
    raw=node.get('raw_style') or {}
    if node.get('node_type') not in ('shape','shapePath','bitmap'):return False
    if raw.get('points') or raw.get('path') or node.get('path'):return False
    bounds=node.get('bounds',{})
    if not all(isinstance(bounds.get(k),(float,int)) for k in ('x','y','width','height')):return False
    asset_kinds = {}
    for entry in item.get('evidence',[]):
        p=Path(entry['path'])
        if not p.is_absolute():p=(policy_path.parent/p).resolve()
        if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest()!=entry['sha256']:return False
        document = json.loads(p.read_text())
        for asset in document.get('assets', []):
            asset_kinds.setdefault(asset.get('asset_id'), set()).add(asset.get('kind'))
    if any(asset_kinds.get(identity) != {'render_fallback'} for identity in node.get('asset_ids', [])):
        return False
    return bool(item.get('evidence')) and bool(item.get('reason'))
