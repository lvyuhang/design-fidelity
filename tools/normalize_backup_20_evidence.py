"""Adapt Lanhu's Sketch-global export points to the artboard coordinate space."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "design_evidence" / "backup-20-skill211" / "source"
OUTPUT = ROOT / "design_evidence" / "backup-20-skill211" / "normalized-source"
ORIGIN = {"x": 1800, "y": 197}
ROOT_NODE = "FE471ACA-C56E-43F5-BC1C-F3ED5244FE40"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    files = []
    adjusted_assets = 0
    adjusted_root = False
    for source in sorted(SOURCE.glob("region-*.json")):
        document = json.loads(source.read_text())
        for asset in document.get("assets", []):
            point = asset.get("source_point")
            if point and "x" in point and "y" in point:
                point["x"] -= ORIGIN["x"]
                point["y"] -= ORIGIN["y"]
                adjusted_assets += 1
        for node in document.get("nodes", []):
            if node.get("node_id") == ROOT_NODE:
                node.setdefault("raw_style", {})["isVisible"] = True
                node["raw_style"].setdefault("opacity", 100)
                node["source_visible"] = True
                node["effective_source_visible"] = True
                adjusted_root = True
        document["evidence_adapter"] = {
            "kind": "sketch_artboard_origin",
            "source_origin": ORIGIN,
            "reason": (
                "asset source_point values are Sketch-document global while "
                "node bounds and reference pixels are artboard-local"
            ),
        }
        output = OUTPUT / source.name
        output.write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n")
        files.append(
            {
                "source": str(source.relative_to(ROOT)),
                "source_sha256": digest(source),
                "normalized": str(output.relative_to(ROOT)),
                "normalized_sha256": digest(output),
            }
        )
    receipt = {
        "status": "complete",
        "source_origin": ORIGIN,
        "adjusted_asset_records": adjusted_assets,
        "root_visibility_completed": adjusted_root,
        "files": files,
    }
    (OUTPUT / "normalization-receipt.json").write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2) + "\n"
    )
    print(json.dumps(receipt, ensure_ascii=False))


if __name__ == "__main__":
    main()
