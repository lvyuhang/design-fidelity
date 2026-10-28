"""Source-derived next steps, not claims of complete geometry or visual approval."""
from __future__ import annotations
import json
from pending_assets import pending_allowed


def source_disposition(key, nodes):
    node = nodes[key]
    raw = node.get('raw_style') or {}
    if node.get('text'):
        return {'state': 'text', 'action': 'verify_font_and_text_runs'}
    if pending_allowed(key, nodes):
        return {'state':'missing_vector_candidate','action':'preserve_shape_and_disclose_unavailable_vector',
                'reason':'hashed reinspection supports authorized placeholder'}
    if node.get('asset_ids'):
        return {'state': 'asset_candidate', 'action': 'verify_export_and_asset_frame',
                'source_node': key}
    parent, seen = node.get('parent_id'), {key}
    while parent in nodes and parent not in seen:
        seen.add(parent)
        if nodes[parent].get('asset_ids'):
            return {'state': 'ancestor_asset_candidate',
                    'action': 'inspect_ancestor_asset_coverage', 'source_node': parent}
        parent = nodes[parent].get('parent_id')
    if parent in seen:
        return {'state': 'unknown', 'action': 'repair_source_parent_cycle'}
    if not raw:
        return {'state': 'unknown', 'action': 'inspect_raw_style'}
    # A bitmap's points may describe its clipping shape, not the image content.
    if node.get('node_type') == 'bitmap':
        return {'state': 'missing_bitmap_candidate',
                'action': 'preserve_container_and_placeholder_image_only'}
    paths = [('raw_style.points', raw.get('points')),
             ('raw_style.path', raw.get('path')), ('path', node.get('path'))]
    refs = [pointer for pointer, value in paths if value]
    if refs:
        return {'state': 'vector_candidate', 'action': 'inspect_path_and_parent_effects',
                'geometry_refs': refs}
    if pending_allowed(key, nodes):
        return {'state':'missing_vector_candidate','action':'preserve_shape_and_disclose_unavailable_vector','reason':'source unresolved after reinspection; user authorized placeholder'}
    if node.get('node_type') in ('shape', 'shapePath'):
        # An absent key is not evidence of an absent path. Never fabricate empty
        # fields in normalized input to turn UNKNOWN into a missing-source claim.
        explicit_empty = ('points' in raw or 'path' in raw or 'path' in node)
        if explicit_empty and not any(n.get('parent_id') == key for n in nodes.values()):
            return {'state': 'missing_vector_candidate',
                    'action': 'preserve_shape_and_disclose_unavailable_vector'}
        return {'state': 'unknown', 'action': 'inspect_complete_node_and_children'}
    return {'state': 'native_review', 'action': 'implement_source_layout_and_effects'}


def placeholder_issue(key, nodes):
    result = source_disposition(key, nodes)
    if result['state'] in ('missing_bitmap_candidate', 'missing_vector_candidate'):
        return None
    return {'code': 'MISSING_SOURCE_NOT_ESTABLISHED', 'node_id': key,
            'source_state': result['state'], 'next_action': result['action'],
            'source_node': result.get('source_node'),
            'message': 'Unread, unavailable-to-this-renderer, and confirmed missing are different states; '
                       'a placeholder reason cannot override source evidence.'}


def disposition_groups(keys, nodes):
    groups = {}
    for key in keys:
        facts = source_disposition(key, nodes)
        signature = json.dumps(facts, sort_keys=True)
        groups.setdefault(signature, {**facts, 'node_ids': []})['node_ids'].append(key)
    return list(groups.values())
