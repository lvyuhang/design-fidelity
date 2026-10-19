#!/usr/bin/env python3
"""Create a source-pinned visual-contract starter from Lanhu MCP evidence."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

from PIL import Image
from fidelity_contract import inventory, sha256, read_json
from source_requirements import requirements, source_gaps, is_small_visual, add_sample_drafts


def _read_json(path: Path) -> dict[str, Any]:
    data = read_json(path)
    if not isinstance(data, dict):
        raise ValueError(f"Evidence must be a JSON object: {path}")
    return data


def _require_same(values: list[Any], label: str) -> Any:
    first = values[0]
    if any(value != first for value in values[1:]):
        raise ValueError(f"Evidence mixes different {label}: {values}")
    return first


def _relative(path: Path, directory: Path) -> str:
    return os.path.relpath(path.resolve(), directory.resolve())


def visual_hints(node):
    """Hints for known raw fields; absence is not proof that no effect exists."""
    raw = node.get('raw_style') or {}
    effects = []
    for field in ('shadow', 'shadows', 'innerShadows', 'blur', 'effects'):
        value = raw.get(field, node.get(field))
        values = value if isinstance(value, list) else [value] if isinstance(value, dict) else []
        if any(v.get('isEnabled', True) and v.get('enabled', True) for v in values if isinstance(v, dict)):
            effects.append(field)
    return {'vector_data_present': bool(raw.get('points') or raw.get('path') or node.get('path')),
            'effect_fields': effects}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence", type=Path, action="append", required=True)
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--name", required=True)
    parser.add_argument("--max-mae", type=float, default=6.0)
    parser.add_argument("--max-p95", type=float, default=32.0)
    parser.add_argument("--effect-max-channel-delta", type=float, default=6.0, help="Draft only; review and freeze before compiling")
    args = parser.parse_args()
    if args.output.exists():
        parser.error("Output already exists; choose a new path to preserve the baseline")

    evidence_paths = [path.resolve() for path in args.evidence]
    evidence = [_read_json(path) for path in evidence_paths]
    snapshots = [item.get("snapshot_id") for item in evidence]
    versions = [item.get("resolved_version") for item in evidence]
    if not all(snapshots) or not all(versions):
        raise ValueError("Every evidence file needs snapshot_id and resolved_version")
    snapshot = _require_same(snapshots, "snapshot_id")
    version = _require_same(versions, "resolved_version")

    canvases = [item.get("canvas") for item in evidence]
    canvas = _require_same(canvases, "canvas")
    if not isinstance(canvas, dict) or not {"width", "height"} <= set(canvas):
        raise ValueError("Evidence canvas must contain width and height")
    for path, item in zip(evidence_paths, evidence):
        mapping = item.get("coordinate_mapping", {})
        if item.get("coordinate_space") != "source_canvas" or not mapping.get("verified"):
            raise ValueError(f"Unverified source_canvas mapping in {path}")

    reference_path = args.reference.resolve()
    reference_size = Image.open(reference_path).size
    scale_x = reference_size[0] / float(canvas["width"])
    scale_y = reference_size[1] / float(canvas["height"])
    if abs(scale_x - scale_y) > 1e-6:
        raise ValueError(
            f"Reference scale is inconsistent: x={scale_x:.6f}, y={scale_y:.6f}"
        )

    output_path = args.output.resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    contract = {
        "schema_version": 2,
        "workflow_version": 1,
        "require_style_evidence": True,
        "status": "draft",
        "name": args.name,
        "source_snapshot": snapshot,
        "source_version": version,
        "canvas": [canvas["width"], canvas["height"]],
        "render_scale": scale_x,
        "reference": _relative(reference_path, output_path.parent),
        "source_documents": [
            _relative(path, output_path.parent) for path in evidence_paths
        ],
        "regions": {
            "whole": {
                "label": "完整页面",
                "rect": [0, 0, canvas["width"], canvas["height"]],
                "max_mae": args.max_mae,
                "max_p95": args.max_p95,
            }
        },
        "features": {},
        "pinned_files": {_relative(path, output_path.parent): sha256(path)
                         for path in [reference_path, *evidence_paths]},
        "assets": [],
        "fonts": [],
        "implementation_inputs": [],
        "environment": {"renderer": "", "renderer_version": "", "platform": "",
                        "locale": "", "state": "", "text_scale": 1},
        "exclude_rects": [],
        "max_excluded_fraction": 0.2,
        "not_applicable": {},
        "relations": {},
        "color_samples": {},
    }
    nodes = {}
    for document in evidence:
        for node in [*document.get("ancestors", []), *document.get("nodes", [])]:
            key = node.get("node_id")
            if key:
                if key in nodes and nodes[key].get("bounds") != node.get("bounds"):
                    raise ValueError(f"Conflicting bounds for {key}")
                nodes[key] = {**nodes.get(key, {}), **node}
    counts = {d.get("total_nodes", d.get("total")) for d in evidence
              if d.get("total_nodes", d.get("total")) is not None}
    if len(counts) > 1:
        raise ValueError("Inconsistent source total_nodes")
    contract["source_scope"] = ({"kind": "page", "expected_node_count": counts.pop()}
                                if counts else {"kind": "provided_nodes", "reason": ""})
    selected = inventory(nodes)
    contract["node_decisions"] = {key: {"mode":"pending", "implementation":"", "symbol":""} for key in selected}
    contract["coverage"] = {key: {"status": "pending", "checks": [], "reason": ""} for key in selected}
    add_sample_drafts(contract, nodes, args.effect_max_channel_delta)
    for key,node in selected.items():
        if is_small_visual(node):
            contract['features']['small__'+key] = {
                'label':node.get('name',key), 'node_ids':[key], 'profile':'small_visual',
                'padding':[1,1,1,1], 'detector':{'kind':'review_required','min_pixels':1},
                'limits':{'max_center_delta':.75,'max_size_delta':.75,'max_edge_delta':.75,
                          'max_ink_ratio_delta':.25,'max_mask_iou_loss':.2}}
    suggestions = []
    for key, node in selected.items():
        text = node.get("text")
        hints = visual_hints(node)
        is_feature = bool(text or node.get("asset_ids") or hints['vector_data_present'])
        suggestions.append({"node_id": key, "label": node.get("name", key),
                            "text": text, "bounds": node["bounds"],
                            "asset_ids": node.get("asset_ids", []),
                            "evidence_hints": hints,
                            "implementation": "pending",
                            "suggested_check": "small_visual" if is_small_visual(node) else "features" if is_feature else "regions/color_samples",
                            "needs_review": True,
                            "detector_hint": "Choose using source colors and a clean crop; do not infer from name"})
    # Geometric candidates only: do not pretend overlap establishes semantic pairing.
    pairs = []
    feature_nodes = [n for n in selected.values() if n.get("text") or n.get("asset_ids")]
    for index, a in enumerate(feature_nodes):
        for b in feature_nodes[index+1:]:
            ab, bb = a["bounds"], b["bounds"]
            ac, bc = ab["y"]+ab["height"]/2, bb["y"]+bb["height"]/2
            gap = max(ab["x"], bb["x"]) - min(ab["x"]+ab["width"], bb["x"]+bb["width"])
            if abs(ac-bc) <= 8 and 0 <= gap <= 32:
                pairs.append({"node_ids": [a["node_id"], b["node_id"]], "metric": "center_y", "needs_review": True})
    suggestions_path = output_path.with_name(output_path.stem + ".suggestions.json")
    if suggestions_path.exists():
        raise ValueError("Suggestions file exists; choose a new output path")
    effect_candidates = [{'node_id': key, 'bounds': node.get('bounds'), **visual_hints(node), 'needs_review': True}
                         for key, node in nodes.items()
                         if node.get('effective_source_visible', node.get('source_visible')) is not False
                         and visual_hints(node)['effect_fields']]
    suggestions_path.write_text(json.dumps({"nodes": suggestions, "relation_candidates": pairs,
        "effect_candidates": effect_candidates,
        "effect_requirements": requirements(nodes, contract["canvas"]),
        "source_gaps": source_gaps(nodes, text_styles=True),
        "scope": "Only nodes contained in supplied evidence; finish MCP pagination before acceptance"}, ensure_ascii=False, indent=2)+"\n")
    output_path.write_text(
        json.dumps(contract, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Created: {output_path}")
    print(f"Snapshot: {snapshot}")
    print(f"Version: {version}")
    print(f"Canvas: {canvas['width']}x{canvas['height']} @ {scale_x:g}x")
    print("Add key regions, visible features, relations, and color samples before acceptance.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
