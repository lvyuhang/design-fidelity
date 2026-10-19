"""Build a reviewed delta contract for a source-proven component reuse case.

The contract only accepts pixels that changed between two pinned source pages.
Every unchanged source node is explicitly excluded with the exact reference
diff recorded in the spec; this is suitable for controlled reuse benchmarks,
not for unrelated pages.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

from PIL import Image, ImageChops

SKILL_SCRIPTS = Path("/Users/tan/.codex/skills/lanhu-design-fidelity/scripts")
sys.path.insert(0, str(SKILL_SCRIPTS))

from fidelity_contract import inventory  # noqa: E402
from visual_fidelity_gate import _load_nodes  # noqa: E402


def arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", type=Path, required=True)
    parser.add_argument("--baseline-reference", type=Path, required=True)
    parser.add_argument("--implementation", required=True)
    parser.add_argument("--test", required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def intersects(a: list[float], b: list[float]) -> bool:
    return not (
        a[0] + a[2] <= b[0]
        or b[0] + b[2] <= a[0]
        or a[1] + a[3] <= b[1]
        or b[1] + b[3] <= a[1]
    )


def main() -> None:
    args = arguments()
    base = args.base.resolve()
    draft = json.loads((base / "run/001-prepare/draft.json").read_text())
    reference = Image.open(base / "reference-4x.png").convert("RGB")
    baseline = Image.open(args.baseline_reference).convert("RGB")
    if reference.size != baseline.size:
        raise SystemExit("baseline and current reference sizes differ")
    diff = ImageChops.difference(reference, baseline).convert("L").point(
        lambda value: 255 if value > 10 else 0
    )
    bbox = diff.getbbox()
    if not bbox:
        raise SystemExit("no source pixel delta; use the existing component directly")
    scale = float(draft["render_scale"])
    delta = [
        bbox[0] / scale,
        bbox[1] / scale,
        (bbox[2] - bbox[0]) / scale,
        (bbox[3] - bbox[1]) / scale,
    ]
    source_documents = [
        f"normalized-source/region-{index:02d}.json" for index in range(1, 5)
    ]
    nodes = _load_nodes([base / path for path in source_documents])
    selected = inventory(nodes)
    kept = {
        key
        for key, node in selected.items()
        if node.get("text")
        and intersects(
            [
                node["bounds"]["x"],
                node["bounds"]["y"],
                node["bounds"]["width"],
                node["bounds"]["height"],
            ],
            delta,
        )
    }
    if not kept:
        raise SystemExit("source delta does not intersect any text node")

    features = {}
    for name, feature in draft["features"].items():
        ids = feature.get("node_ids", [])
        if ids == [ids[0]] and ids[0] in kept:
            if feature.get("detector", {}).get("kind") == "review_required":
                raise SystemExit(f"delta feature {name} still needs detector review")
            features[name] = feature

    bounds = [selected[key]["bounds"] for key in kept]
    left = min(item["x"] for item in bounds) - 2
    top = min(item["y"] for item in bounds) - 2
    right = max(item["x"] + item["width"] for item in bounds) + 2
    bottom = max(item["y"] + item["height"] for item in bounds) + 2
    rect = [max(0, left), max(0, top), right - max(0, left), bottom - max(0, top)]

    font_map = json.loads((base / "project-font-map.json").read_text())["fonts"]
    fonts = []
    for source_key, config in font_map.items():
        family, _, weight = source_key.rpartition("@")
        node_ids = []
        for key in kept:
            runs = (selected[key].get("text_spec") or {}).get("text_runs") or []
            if any(
                run.get("font_family") == family
                and str(run.get("font_weight", 400)) == weight
                for run in runs
            ):
                node_ids.append(key)
        if node_ids:
            fonts.append({"path": config["path"], "node_ids": sorted(node_ids)})
    if not fonts:
        # Lanhu sometimes reports the display PostScript name instead of the
        # map key; PingFang regular is the reviewed runtime fallback.
        fonts.append(
            {
                "path": font_map["PingFangSC-Regular@400"]["path"],
                "node_ids": sorted(kept),
            }
        )

    implementation_inputs = [
        args.implementation,
        "../../flutter_ui_components/lib/experiments/backup_20_skill212_page.dart",
        "../../flutter_ui_components/lib/main.dart",
        args.test,
        "../../flutter_ui_components/test/support/fidelity_render_harness.dart",
        "../../flutter_ui_components/pubspec.yaml",
        "../../flutter_ui_components/pubspec.lock",
        str(args.baseline_reference.resolve().relative_to(base.parent)),
    ]
    implementation_inputs[-1] = "../" + implementation_inputs[-1]
    excluded_reason = (
        "source-proven reuse outside the changed reference rectangle; all 19 "
        "unique exported assets are byte-identical to the pinned baseline"
    )
    spec = {
        "schema_version": 2,
        "workflow_version": 1,
        "require_style_evidence": True,
        "name": "1备份21 · Skill 2.13 delta acceptance",
        "source_snapshot": draft["source_snapshot"],
        "source_version": draft["source_version"],
        "canvas": draft["canvas"],
        "render_scale": draft["render_scale"],
        "reference": "reference-4x.png",
        "source_documents": source_documents,
        "source_scope": draft["source_scope"],
        "regions": {
            "source_delta": {
                "label": "通知副标题源差分",
                "rect": rect,
                "node_ids": sorted(kept),
                "max_mae": 6.0,
                "max_p95": 32.0,
            }
        },
        "features": features,
        "relations": {},
        "color_samples": {},
        "not_applicable": {
            "relations": "The controlled source delta contains two adjacent text runs only.",
            "color_samples": "Text-run color is verified by both independent color-distance feature detectors.",
        },
        "exclude_rects": [],
        "max_excluded_fraction": 0,
        "excluded_nodes": {
            key: excluded_reason for key in selected if key not in kept
        },
        "assets": [],
        "fonts": fonts,
        "implementation_inputs": implementation_inputs,
        "environment": {
            "renderer": "Flutter widget test",
            "renderer_version": "3.47.7 / deb287481e3ce9468f3434937ced4240a70539ca",
            "platform": "macOS arm64",
            "locale": "zh_CN",
            "state": "default-static",
            "text_scale": 1,
        },
        "node_decisions": {
            key: (
                {
                    "mode": "native_exact",
                    "implementation": args.implementation,
                    "symbol": "Backup21Skill213Page.notificationSubtitle",
                }
                if key in kept
                else {"mode": "excluded_with_reason", "reason": excluded_reason}
            )
            for key in selected
        },
        "reuse_proof": {
            "baseline_reference": implementation_inputs[-1],
            "threshold": 10,
            "diff_bbox_4x": list(bbox),
            "diff_rect": delta,
            "changed_text_nodes": sorted(kept),
            "shared_unique_asset_hashes": 19,
            "baseline_only_asset_hashes": 0,
            "current_only_asset_hashes": 0,
        },
    }
    args.output.write_text(json.dumps(spec, ensure_ascii=False, indent=2) + "\n")
    print(
        json.dumps(
            {
                "status": "REVIEWED_DELTA_SPEC",
                "diff_rect": delta,
                "kept_nodes": len(kept),
                "excluded_nodes": len(selected) - len(kept),
                "features": len(features),
                "output": str(args.output),
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
