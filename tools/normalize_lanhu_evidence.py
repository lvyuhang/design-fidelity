"""Normalize Sketch-global asset points into a Lanhu artboard coordinate space."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--origin-x", type=float, required=True)
    parser.add_argument("--origin-y", type=float, required=True)
    parser.add_argument("--root-node", required=True)
    return parser.parse_args()


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    args = arguments()
    args.output.mkdir(parents=True, exist_ok=True)
    files = []
    adjusted_assets = 0
    adjusted_root = False
    for source in sorted(args.source.glob("region-*.json")):
        document = json.loads(source.read_text())
        for asset in document.get("assets", []):
            point = asset.get("source_point")
            if point and "x" in point and "y" in point:
                point["x"] -= args.origin_x
                point["y"] -= args.origin_y
                adjusted_assets += 1
        for node in document.get("nodes", []):
            if node.get("node_id") == args.root_node:
                node.setdefault("raw_style", {})["isVisible"] = True
                node["raw_style"].setdefault("opacity", 100)
                node["source_visible"] = True
                node["effective_source_visible"] = True
                adjusted_root = True
        document["evidence_adapter"] = {
            "kind": "sketch_artboard_origin",
            "source_origin": {"x": args.origin_x, "y": args.origin_y},
            "reason": (
                "asset source_point values are Sketch-document global while "
                "node bounds and reference pixels are artboard-local"
            ),
        }
        output = args.output / source.name
        output.write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n")
        files.append(
            {
                "source": str(source),
                "source_sha256": digest(source),
                "normalized": str(output),
                "normalized_sha256": digest(output),
            }
        )
    if not files or not adjusted_root:
        raise SystemExit("normalization failed: missing region files or root node")
    receipt = {
        "status": "complete",
        "source_origin": {"x": args.origin_x, "y": args.origin_y},
        "root_node": args.root_node,
        "adjusted_asset_records": adjusted_assets,
        "root_visibility_completed": adjusted_root,
        "files": files,
    }
    (args.output / "normalization-receipt.json").write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2) + "\n"
    )
    print(json.dumps(receipt, ensure_ascii=False))


if __name__ == "__main__":
    main()
