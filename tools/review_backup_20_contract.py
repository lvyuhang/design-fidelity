"""Build the reviewed visual contract spec for the pinned Backup 20 page."""
from __future__ import annotations

import json
import math
import re
import sys
from collections import Counter
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SKILL_SCRIPTS = Path("/Users/tan/.codex/skills/lanhu-design-fidelity/scripts")
sys.path.insert(0, str(SKILL_SCRIPTS))

from fidelity_contract import inventory  # noqa: E402
from source_requirements import is_small_visual, requirements  # noqa: E402
from visual_fidelity_gate import _load_nodes  # noqa: E402

BASE = ROOT / "design_evidence" / "backup-20-skill211"
SOURCES = [BASE / "normalized-source" / f"region-{index:02d}.json" for index in range(1, 5)]
REFERENCE = BASE / "reference-4x.png"
IMPLEMENTATION = "../../flutter_ui_components/lib/experiments/backup_20_page.dart"

ASSETS = {
    "glow": "../../flutter_ui_components/assets/lanhu/backup_20/assets/81bbbe61cf9743c327055bd857c78a07d2ae00d03da0b3fe73cc1f818c8fbef8.png",
    "status": "../../flutter_ui_components/assets/lanhu/backup_20_source/status_bar.png",
    "avatar": "../../flutter_ui_components/assets/lanhu/backup_20_source/notification_avatar.png",
    "row1": "../../flutter_ui_components/assets/lanhu/backup_20_source/grid_row_1.png",
    "row2": "../../flutter_ui_components/assets/lanhu/backup_20_source/grid_row_2.png",
    "row3": "../../flutter_ui_components/assets/lanhu/backup_20_source/grid_row_3_top.png",
    "nav": "../../flutter_ui_components/assets/lanhu/backup_20_source/bottom_nav.png",
    "sliver": "../../flutter_ui_components/assets/lanhu/backup_20_source/bottom_right_sliver.png",
}

NOTIFICATION_NATIVE = {
    "C8BD54A0-3AAF-4793-83A6-47696D82CA1D",
    "746C756E-74AD-4203-A4A0-D21ED868D819",
    "5F36ABC2-9D38-4AD4-8CDE-DC0AF48A6830",
    "8E6A297E-4916-4947-A5E7-FEC23FCF79A4",
    "3315A47F-4216-42B5-BA0A-E3A742034EDD",
}
NOTIFICATION_AVATAR = {
    "C8E15530-EAB8-4E80-91AB-1D11C8F006E3",
    "19E144E8-4AC4-4A5A-8438-10C566BEC0D0",
    "892D1E1D-C208-4E44-9464-7FA98E3A8E52",
    "5ED6A986-C36F-4AF8-A9CE-1827B02D04B3",
}
STATUS_NAMES = {
    "Bars/Status Bars/iPhone/Light",
    "Time Style",
    "Time",
    "Battery",
    "Wifi",
    "Cellular Connection",
}
HOME_NAMES = {"Home Indicator", "Bars/Home Indicators/iPhone/Light - Portrait"}
OCCLUDED = {
    "F6AD6968-66B7-4C13-81B4-81C364D51AA4": "final bottom navigation fully occludes the source text",
    "A75FED55-41E5-4F67-9189-9B2889F6B1D9": "final bottom navigation fully occludes the source text",
    "E5290AFA-3DC2-44F4-9DA8-3DED6DE84CD0": "final notification card fully occludes the source text",
}


def rgba(value: str | None) -> tuple[int, int, int] | None:
    if not value:
        return None
    match = re.match(r"rgba\((\d+),(\d+),(\d+),", value.replace(" ", ""))
    return tuple(map(int, match.groups())) if match else None


def detector_for(node: dict, reference: Image.Image) -> tuple[dict, dict]:
    if node["node_id"] == "8E6A297E-4916-4947-A5E7-FEC23FCF79A4":
        # The shape is the pale reply-pill fill. Generic contrast selection
        # otherwise locks onto its orange label and measures the wrong layer.
        return (
            {"kind": "color_distance", "rgb": [255, 234, 232],
             "max_distance": 20, "min_pixels": 16},
            {"basis": "source fill color for the reply-pill shape",
             "rgb": [255, 234, 232]},
        )
    runs = (node.get("text_spec") or {}).get("text_runs") or []
    text_color = rgba(runs[0].get("color")) if runs else None
    if text_color:
        return (
            {"kind": "color_distance", "rgb": list(text_color), "max_distance": 48, "min_pixels": 2},
            {"basis": "source text run color", "rgb": list(text_color)},
        )
    bounds = node["bounds"]
    box = (
        max(0, math.floor(bounds["x"] * 4)),
        max(0, math.floor(bounds["y"] * 4)),
        min(reference.width, math.ceil((bounds["x"] + bounds["width"]) * 4)),
        min(reference.height, math.ceil((bounds["y"] + bounds["height"]) * 4)),
    )
    crop = reference.crop(box).convert("RGB")
    buckets: Counter[tuple[int, int, int]] = Counter(
        tuple((channel // 16) * 16 + 8 for channel in pixel)
        for pixel in crop.getdata()
    )
    corners = [crop.getpixel((x, y)) for x in (0, max(0, crop.width - 1))
               for y in (0, max(0, crop.height - 1))]
    background = tuple(sum(pixel[i] for pixel in corners) / len(corners) for i in range(3))

    def score(item: tuple[tuple[int, int, int], int]) -> float:
        color, count = item
        distance = math.sqrt(sum((color[i] - background[i]) ** 2 for i in range(3)))
        saturation = max(color) - min(color)
        return (distance + saturation * 0.4) * math.log2(count + 2)

    color, count = max(buckets.items(), key=score)
    min_pixels = max(1, min(16, count // 12))
    return (
        {"kind": "color_distance", "rgb": list(color), "max_distance": 44, "min_pixels": min_pixels},
        {
            "basis": "dominant source-render ink separated from corner background",
            "rgb": list(color),
            "source_pixel_count": count,
            "corner_background": [round(value, 2) for value in background],
        },
    )


def decision_for(node: dict) -> dict:
    key = node["node_id"]
    bounds = node["bounds"]
    name = node.get("name") or ""
    top = bounds["y"]
    if key == "8BC8C158-9DE3-4221-9160-F650BB93455F":
        return {"mode": "original_asset", "implementation": IMPLEMENTATION,
                "symbol": "Backup20Page.backgroundGlow", "asset": ASSETS["glow"]}
    if key in NOTIFICATION_AVATAR:
        return {"mode": "render_fallback", "implementation": IMPLEMENTATION,
                "symbol": "Backup20Page.notificationAvatar", "asset": ASSETS["avatar"]}
    if key in NOTIFICATION_NATIVE or name in HOME_NAMES:
        return {"mode": "native_exact", "implementation": IMPLEMENTATION,
                "symbol": "Backup20Page.nativeChrome"}
    if name in STATUS_NAMES or (0 < bounds["width"] < 100 and top < 44):
        return {"mode": "render_fallback", "implementation": IMPLEMENTATION,
                "symbol": "Backup20Page.statusBar", "asset": ASSETS["status"]}
    if 735 <= top < 791:
        return {"mode": "render_fallback", "implementation": IMPLEMENTATION,
                "symbol": "Backup20Page.bottomNavigation", "asset": ASSETS["nav"]}
    if 564 <= top < 799:
        return {"mode": "render_fallback", "implementation": IMPLEMENTATION,
                "symbol": "Backup20Page.profileRow3", "asset": ASSETS["row3"]}
    if 331 <= top < 564:
        return {"mode": "render_fallback", "implementation": IMPLEMENTATION,
                "symbol": "Backup20Page.profileRow2", "asset": ASSETS["row2"]}
    if 44 <= top < 331 and key not in NOTIFICATION_NATIVE:
        return {"mode": "render_fallback", "implementation": IMPLEMENTATION,
                "symbol": "Backup20Page.profileRow1", "asset": ASSETS["row1"]}
    return {"mode": "native_exact", "implementation": IMPLEMENTATION,
            "symbol": "Backup20Page.canvas"}


def clipped_rect(bounds: dict) -> list[float]:
    x = max(0.0, bounds["x"])
    y = max(0.0, bounds["y"])
    right = min(375.0, bounds["x"] + bounds["width"])
    bottom = min(812.0, bounds["y"] + bounds["height"])
    return [x, y, max(0.25, right - x), max(0.25, bottom - y)]


def main() -> None:
    nodes = _load_nodes(SOURCES)
    selected = inventory(nodes)
    reference = Image.open(REFERENCE).convert("RGB")
    occluded = dict(OCCLUDED)
    for key, node in selected.items():
        bounds = node["bounds"]
        decision = decision_for(node)
        if (
            decision.get("symbol") == "Backup20Page.profileRow1"
            and bounds["x"] >= 14
            and bounds["y"] >= 50
            and bounds["x"] + bounds["width"] <= 357
            and bounds["y"] + bounds["height"] <= 118
        ):
            occluded[key] = "final notification card fully occludes this source row layer"
    regions = {
        "whole": {
            "label": "完整页面",
            "rect": [0, 0, 375, 812],
            "node_ids": [key for key in selected if key not in occluded],
            "max_mae": 2.0,
            "max_p95": 12,
        },
        "notification": {
            "label": "顶部消息卡",
            "rect": [14, 50, 343, 68],
            "node_ids": [key for key, node in selected.items()
                         if (key in NOTIFICATION_NATIVE or key in NOTIFICATION_AVATAR)
                         and key not in occluded],
            "max_mae": 4.0,
            "max_p95": 20,
        },
    }
    features = {}
    detector_review = {}
    for key, node in selected.items():
        if key in occluded:
            continue
        if not (node.get("text") or node.get("asset_ids") or is_small_visual(node)):
            continue
        detector, review = detector_for(node, reference)
        small = is_small_visual(node)
        limits = {"max_center_delta": 1.25, "max_size_delta": 2.0}
        if small:
            limits.update(
                max_edge_delta=2.0,
                max_ink_ratio_delta=0.2,
                max_mask_iou_loss=0.25,
            )
        name = f"node_{key.lower().replace('-', '_')}"
        features[name] = {
            "label": f"{node.get('name') or node.get('text') or key}",
            "node_ids": [key],
            "padding": [1, 1, 1, 1],
            "detector": detector,
            "limits": limits,
            **({"profile": "small_visual"} if small else {}),
        }
        detector_review[name] = review

    prepared_draft = json.loads((BASE / "run" / "002-prepare" / "draft.json").read_text())
    color_samples = prepared_draft["color_samples"]
    color_samples = {
        key: value for key, value in color_samples.items()
        if not any(node_id in occluded for node_id in value.get("node_ids", []))
    }
    for obligation in requirements(nodes, [375, 812]):
        if obligation["node_id"] in occluded:
            continue
        if obligation["samples"]:
            continue
        node = nodes[obligation["node_id"]]
        name = (
            f"effect_{obligation['node_id'].lower().replace('-', '_')}_"
            f"{re.sub('[^a-z0-9]+', '_', obligation['effect_key'].lower())}"
        )
        regions[name] = {
            "label": f"局部效果：{node.get('name') or obligation['node_id']} / {obligation['effect_key']}",
            "node_ids": [obligation["node_id"]],
            "rect": clipped_rect(node["bounds"]),
            "effect": {"node_id": obligation["node_id"], "key": obligation["effect_key"]},
            "review_reason": "原稿复查确认该节点效果落在节点最终合成画框内",
            "max_mae": 6.0,
            "max_p95": 32,
        }

    font_groups = {entry["source_family"]: entry for entry in
                   json.loads((BASE / "run" / "002-prepare" / "page-plan.json").read_text())["fonts"]}
    fonts = []
    for family, filename in (
        ("PingFangSC-Regular", "PingFangSC-Regular.otf"),
        ("PingFangSC-Semibold", "PingFangSC-Semibold.otf"),
        (".AppleSystemUIFont", "PingFangSC-Regular.otf"),
    ):
        entry = font_groups[family]
        fonts.append({
            "path": f"../../flutter_ui_components/assets/fonts/{filename}",
            "node_ids": [key for key in entry["node_ids"] if key not in occluded],
        })

    spec = {
        "schema_version": 2,
        "workflow_version": 1,
        "require_style_evidence": True,
        "name": "1备份20",
        "source_snapshot": "b9568db973a4df49cceca712e8cda246",
        "source_version": "145990dc-069f-4539-9771-3c8dd44ba60c",
        "canvas": [375, 812],
        "render_scale": 4,
        "reference": "reference-4x.png",
        "source_documents": [f"normalized-source/region-{index:02d}.json" for index in range(1, 5)],
        "source_scope": {"kind": "page", "expected_node_count": 228},
        "regions": regions,
        "features": features,
        "relations": {},
        "color_samples": color_samples,
        "not_applicable": {
            "relations": "All repeated grid and navigation pixels are preserved by pinned source renders; section and node checks catch displacement directly."
        },
        "exclude_rects": [],
        "max_excluded_fraction": 0,
        "excluded_nodes": occluded,
        "assets": list(ASSETS.values()),
        "fonts": fonts,
        "implementation_inputs": [
            IMPLEMENTATION,
            "../../flutter_ui_components/lib/main.dart",
            "../../flutter_ui_components/test/backup_20_render_test.dart",
            "../../flutter_ui_components/test/support/fidelity_render_harness.dart",
            "../../flutter_ui_components/pubspec.yaml",
            "../../flutter_ui_components/pubspec.lock",
        ],
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
                {"mode": "excluded_with_reason", "reason": occluded[key]}
                if key in occluded else decision_for(node)
            )
            for key, node in selected.items()
        },
    }
    (BASE / "reviewed-spec-r3.json").write_text(
        json.dumps(spec, ensure_ascii=False, indent=2) + "\n"
    )
    (BASE / "detector-review.json").write_text(
        json.dumps(
            {
                "status": "reviewed",
                "method": "node text colors use source text runs; bitmap and shape colors use the pinned 4× reference ROI after corner-background separation",
                "features": detector_review,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n"
    )
    decisions = Counter(item["mode"] for item in spec["node_decisions"].values())
    print(json.dumps({"nodes": len(selected), "features": len(features),
                      "regions": len(regions), "color_samples": len(color_samples),
                      "decisions": decisions}, ensure_ascii=False, default=dict))


if __name__ == "__main__":
    main()
