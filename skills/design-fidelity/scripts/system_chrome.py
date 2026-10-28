"""OS-drawn chrome (status bar, home indicator) inside design mock-ups.

Designers paste the iOS status bar and home indicator into artboards; the app
never paints them. Treating them as page content forced models to fake Wi-Fi /
signal glyphs without source paths, which blocked whole runs. This module
identifies them from source facts only (layer name or geometry plus a clock
text), so prepare, codegen, compile and the gate agree on the same nodes.
"""
from __future__ import annotations

import re

STATUS_BAR_NAME = re.compile(r'status\s*bars?|statusbar|状态栏', re.I)
HOME_INDICATOR_NAME = re.compile(r'home\s*indicators?|homeindicator|底部横条|home\s*bar', re.I)
CLOCK_TEXT = re.compile(r'\d{1,2}:\d{2}')
MAX_STATUS_BAR_HEIGHT = 54
MAX_HOME_INDICATOR_HEIGHT = 40


def canvas_of(nodes: dict) -> tuple[float, float] | None:
    """The artboard frame when the evidence has exactly one root artboard."""
    roots = [n for n in nodes.values() if n.get('parent_id') not in nodes]
    boards = [n for n in roots if n.get('node_type') in ('artboard', 'artboard-group')]
    if len(boards) == 1:
        b = boards[0].get('bounds') or {}
        if b.get('width') and b.get('height'):
            return float(b['width']), float(b['height'])
    return None


def _descendants(key: str, children: dict) -> list[str]:
    out, stack = [], list(children.get(key, []))
    while stack:
        item = stack.pop()
        out.append(item)
        stack.extend(children.get(item, []))
    return out


def detect_system_chrome(nodes: dict, canvas=None) -> list[dict]:
    """Top-level chrome layers: [{node_id, kind, rect, members}]."""
    canvas = canvas or canvas_of(nodes)
    if not canvas:
        return []
    width, height = float(canvas[0]), float(canvas[1])
    children: dict = {}
    for key, node in nodes.items():
        children.setdefault(node.get('parent_id'), []).append(key)
    root_ids = [k for k, n in nodes.items() if n.get('parent_id') not in nodes]
    top_level = []
    for root in root_ids:
        if nodes[root].get('node_type') in ('artboard', 'artboard-group'):
            top_level.extend(children.get(root, []))
        else:
            top_level.append(root)
    found = []
    for key in sorted(top_level, key=lambda k: (nodes[k].get('source_order', 0), k)):
        node = nodes[key]
        b = node.get('bounds') or {}
        x, y = float(b.get('x', -1)), float(b.get('y', -1))
        w, h = float(b.get('width', 0)), float(b.get('height', 0))
        name = str(node.get('name') or '')
        members = _descendants(key, children)
        kind = None
        if STATUS_BAR_NAME.search(name) and y < 1 and h <= MAX_STATUS_BAR_HEIGHT:
            kind = 'statusBar'
        elif HOME_INDICATOR_NAME.search(name) and y + h >= height - 1 and h <= MAX_HOME_INDICATOR_HEIGHT:
            kind = 'homeIndicator'
        elif abs(x) < 1 and abs(w - width) < 1 and y < 1 and h <= MAX_STATUS_BAR_HEIGHT and any(
                isinstance(nodes[m].get('text'), str) and CLOCK_TEXT.fullmatch(nodes[m]['text'].strip())
                for m in members):
            kind = 'statusBar'
        if kind:
            found.append({'node_id': key, 'kind': kind, 'rect': [x, y, w, h], 'members': members})
    return found


def chrome_members(nodes: dict, canvas=None) -> dict[str, dict]:
    """Every chrome node and descendant -> its chrome entry."""
    result = {}
    for entry in detect_system_chrome(nodes, canvas):
        for key in (entry['node_id'], *entry['members']):
            result[key] = entry
    return result


def chrome_exclusion_shapes(nodes: dict, canvas=None) -> list[dict]:
    """Source-derived exclusion rectangles for the gate (deduplicated)."""
    shapes, seen = [], set()
    for entry in detect_system_chrome(nodes, canvas):
        rect = tuple(entry['rect'])
        if rect in seen:
            continue
        seen.add(rect)
        shapes.append({'shape': 'rect', 'rect': list(rect),
                       'reason': f"system_chrome:{entry['kind']} (OS-drawn, not app content)"})
    return shapes
