#!/usr/bin/env python3
"""Build the reviewed visual contract for Lanhu design `1备份 44`."""

from __future__ import annotations

import hashlib
import json
import os
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE_DIR = ROOT / "design_evidence" / "task-plan-44"
CONTRACT = EVIDENCE_DIR / "visual-contract.json"
SOURCE_FILES = [
    EVIDENCE_DIR / "source" / "overview.json",
    EVIDENCE_DIR / "source" / "source-02.json",
    EVIDENCE_DIR / "source" / "source-03.json",
]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def relative(path: Path) -> str:
    return os.path.relpath(path.resolve(), EVIDENCE_DIR.resolve())


def rgba(value: str | None) -> tuple[int, int, int]:
    match = re.search(r"rgba?\((\d+),(\d+),(\d+)", value or "")
    return tuple(map(int, match.groups())) if match else (24, 24, 27)


def detector_for(rgb: tuple[int, int, int]) -> dict:
    red, green, blue = rgb
    if red < 100 and green < 100 and blue < 100:
        return {"kind": "dark", "luma_max": 120, "min_pixels": 8}
    if red > green * 1.25 and red > blue * 1.25:
        return {
            "kind": "channel_range",
            "red": [max(0, red - 55), 255],
            "green": [max(0, green - 65), min(255, green + 65)],
            "blue": [max(0, blue - 65), min(255, blue + 65)],
            "min_pixels": 8,
        }
    if red - blue > 45 and green - blue > 10:
        return {
            "kind": "gold",
            "red_min": max(80, red - 60),
            "red_blue_min": 10,
            "green_blue_min": 5,
            "red_green_min": -24,
            "min_pixels": 8,
        }
    return {
        "kind": "color_distance",
        "rgb": [red, green, blue],
        "max_distance": 70,
        "min_pixels": 8,
    }


def main() -> None:
    documents = [json.loads(path.read_text()) for path in SOURCE_FILES]
    nodes: dict[str, dict] = {}
    suggestions: dict[str, dict] = {}
    for document in documents:
        for node in [*document.get("ancestors", []), *document.get("nodes", [])]:
            node_id = node.get("node_id")
            if node_id:
                nodes[node_id] = {**nodes.get(node_id, {}), **node}
        for suggestion in document.get("dds_layout_suggestions", []):
            node_id = suggestion.get("node_id")
            if node_id:
                suggestions[node_id] = {
                    **suggestions.get(node_id, {}),
                    **suggestion.get("style", {}),
                }

    parents = {node.get("parent_id") for node in nodes.values()}
    inventory = {
        node_id: node
        for node_id, node in nodes.items()
        if node.get("effective_source_visible", node.get("source_visible", True)) is not False
        and node.get("bounds", {}).get("width", 0) > 0
        and node.get("bounds", {}).get("height", 0) > 0
        and (node.get("text") or node.get("asset_ids") or node_id not in parents)
    }

    missing_bitmaps = {
        "279C55CE-5877-4BBF-B54E-5911B222546A": "头像位图没有 asset_id，MCP 返回 NoAssets，显示未切图色块。",
        "F9D266C7-4E8E-4457-9101-AF9D8E87F35B": "叫醒铃声位图没有 asset_id，显示未切图色块。",
        "3739EAF2-06B1-4022-B398-B395A9B91101": "睡前陪伴位图没有 asset_id，显示未切图色块。",
        "D5BAC799-A869-43C7-A96A-B0372C38A786": "失眠哄睡位图没有 asset_id，显示未切图色块。",
        "16D00A1F-B22D-42A9-AF8E-21AAA5A16BEB": "初级任务包图标没有可导出的原始素材，显示未切图色块。",
        "0811403E-78EA-46FF-A6C2-3165E38BA454": "关系图标没有可导出的原始素材，显示未切图色块。",
        "94ED355F-9520-45E2-97DA-437A6C2DB527": "关系图标没有可导出的原始素材，显示未切图色块。",
        "FF31F439-1AC7-4A82-B646-08A7DD70DC08": "关系图标没有可导出的原始素材，显示未切图色块。",
        "C331DE19-4566-4E30-84FE-681C81E528F1": "发私信图标没有可导出的原始素材，显示未切图色块。",
        "4AA365FC-66BC-45EB-A841-76D6C447D55B": "发私信图标没有可导出的原始素材，显示未切图色块。",
        "B431A994-9542-4C1B-A909-38E6F219D58E": "已过期印章没有可导出的原始素材，显示圆形未切图色块。",
        "07170E12-8CFD-4936-81DB-20E58C2711AD": "已过期印章没有可导出的原始素材，显示圆形未切图色块。",
        "1A06AA28-8C6F-4475-8C68-82E09FE93A0F": "已过期印章没有可导出的原始素材，显示圆形未切图色块。",
        "FBD5B190-A244-4F91-A25A-366F0D7B8E84": "已过期印章没有可导出的原始素材，显示圆形未切图色块。",
        "3F8E161F-206C-4E5C-94C2-334720C6D22A": "已过期印章文字属于未导出素材，显示圆形未切图色块。",
    }

    text_features: dict[str, dict] = {}
    regular_nodes: list[str] = []
    semibold_nodes: list[str] = []
    for node_id, node in inventory.items():
        if node_id in missing_bitmaps:
            continue
        if not node.get("text"):
            continue
        base = node.get("text_spec", {}).get("base_style", {})
        runs = node.get("text_spec", {}).get("text_runs", [])
        raw_font = node.get("raw_style", {}).get("font", {})
        color = (
            suggestions.get(node_id, {}).get("color")
            or next(
                (
                    fill.get("color", {}).get("value")
                    for fill in node.get("raw_style", {}).get("fills", [])
                    if fill.get("isEnabled", True)
                    and fill.get("type") == "color"
                    and fill.get("color", {}).get("a", 1) > 0
                ),
                None,
            )
            or base.get("color")
            or (runs[0].get("color") if runs else None)
            or raw_font.get("color", {}).get("value")
        )
        rgb = rgba(color)
        key = f"text_{node_id[:8].lower()}"
        text_features[key] = {
            "label": node.get("text"),
            "node_ids": [node_id],
            "padding": [1, 1, 1, 1],
            "detector": detector_for(rgb),
            "limits": {
                "max_center_delta": 2.5,
                "max_size_delta": 3,
                "max_edge_delta": 3,
                "max_ink_ratio_delta": 0.5,
            },
        }
        weights = {run.get("font_weight") for run in runs}
        raw_weight = raw_font.get("styles", [{}])[0].get("fontWeight")
        suggested_weight = suggestions.get(node_id, {}).get("fontWeight")
        (semibold_nodes if 600 in weights or raw_weight == 600 or suggested_weight == "600" else regular_nodes).append(node_id)

    nontext_nodes = [
        node_id
        for node_id, node in inventory.items()
        if not node.get("text") and node_id not in missing_bitmaps
    ]
    features = {
        **text_features,
        "expiry_underline": {
            "label": "到期时间底部高亮线",
            "node_ids": ["46E8F6F9-05FF-411B-B09E-DED92BB0072C"],
            "padding": [1, 1, 1, 1],
            "detector": {
                "kind": "channel_range",
                "red": [245, 255],
                "green": [225, 250],
                "blue": [175, 225],
                "min_pixels": 300,
            },
            "limits": {
                "max_center_delta": 1.5,
                "max_size_delta": 1,
                "max_edge_delta": 1,
                "max_ink_ratio_delta": 0.25,
            },
        },
        "date_check": {
            "label": "17日完成勾选",
            "node_ids": ["72D53999-41E9-4D45-88A5-C9B9A1CC7FE7"],
            "padding": [2, 2, 2, 2],
            "detector": {
                "kind": "color_distance",
                "rgb": [131, 198, 133],
                "max_distance": 50,
                "min_pixels": 300,
            },
            "limits": {
                "max_center_delta": 0.75,
                "max_size_delta": 0.75,
                "max_edge_delta": 0.75,
                "max_ink_ratio_delta": 0.25,
            },
        },
        "relationship_chevron": {
            "label": "关系入口右箭头",
            "node_ids": ["DE69682B-95C7-4E49-BC26-BA67187726C1"],
            "padding": [2, 2, 2, 2],
            "detector": {
                "kind": "channel_range",
                "red": [130, 220],
                "green": [80, 160],
                "blue": [0, 100],
                "min_pixels": 80,
            },
            "limits": {
                "max_center_delta": 0.75,
                "max_size_delta": 0.75,
                "max_edge_delta": 0.75,
                "max_ink_ratio_delta": 0.3,
            },
        },
        "complete_chevron": {
            "label": "去完成右箭头",
            "node_ids": ["AF5F7638-3FC0-409F-AA0C-165C7EDFB106"],
            "padding": [2, 2, 2, 2],
            "detector": {
                "kind": "channel_range",
                "red": [140, 230],
                "green": [80, 160],
                "blue": [0, 100],
                "min_pixels": 80,
            },
            "limits": {
                "max_center_delta": 0.75,
                "max_size_delta": 0.75,
                "max_edge_delta": 0.75,
                "max_ink_ratio_delta": 0.3,
            },
        },
        "progress_knob": {
            "label": "任务进度滑块",
            "node_ids": ["1081AEC8-AD88-4ED8-957E-24362A86AEB3"],
            "padding": [1, 1, 1, 1],
            "detector": {"kind": "dark", "luma_max": 55, "min_pixels": 100},
            "limits": {
                "max_center_delta": 1,
                "max_size_delta": 1.5,
                "max_edge_delta": 1.5,
                "max_ink_ratio_delta": 0.25,
            },
        },
        "home_indicator": {
            "label": "Home Indicator",
            "node_ids": ["F5F075E5-AD3C-4A87-BDDB-EF0BBEB04C17"],
            "padding": [1, 1, 1, 1],
            "detector": {"kind": "dark", "luma_max": 30, "min_pixels": 1000},
            "limits": {
                "max_center_delta": 1,
                "max_size_delta": 1,
                "max_edge_delta": 1,
                "max_ink_ratio_delta": 0.12,
            },
        },
    }

    coverage: dict[str, dict] = {}
    feature_for_node = {
        node_id: name
        for name, spec in features.items()
        for node_id in spec.get("node_ids", [])
    }
    for node_id, node in inventory.items():
        if node_id in missing_bitmaps:
            coverage[node_id] = {
                "status": "excluded",
                "checks": [],
                "reason": missing_bitmaps[node_id],
            }
        elif node.get("text"):
            coverage[node_id] = {
                "status": "covered",
                "checks": [f"features.{feature_for_node[node_id]}"],
                "reason": "",
            }
        elif node_id in feature_for_node:
            coverage[node_id] = {
                "status": "covered",
                "checks": [f"features.{feature_for_node[node_id]}"],
                "reason": "",
            }
        else:
            coverage[node_id] = {
                "status": "covered",
                "checks": ["regions.whole"],
                "reason": "",
            }

    reference = EVIDENCE_DIR / "reference.png"
    regular_font = ROOT / "flutter_ui_components" / "assets" / "fonts" / "PingFangSC-Regular.otf"
    semibold_font = ROOT / "flutter_ui_components" / "assets" / "fonts" / "PingFangSC-Semibold.otf"
    asset_export = EVIDENCE_DIR / "asset-export.json"
    pinned = [reference, *SOURCE_FILES, regular_font, semibold_font, asset_export]

    contract = {
        "schema_version": 2,
        "status": "ready",
        "name": "task-plan-44",
        "source_snapshot": "c6a7d292fc945718c9df15b499eea634",
        "source_version": "356bb545-d906-4a17-b86f-5dc62a6e4cdf",
        "canvas": [375, 812],
        "render_scale": 4,
        "reference": "reference.png",
        "source_documents": ["source/overview.json", "source/source-02.json", "source/source-03.json"],
        "source_scope": {"kind": "page", "expected_node_count": 125},
        "regions": {
            "whole": {
                "label": "完整任务计划页",
                "rect": [0, 0, 375, 812],
                "node_ids": nontext_nodes,
                "max_mae": 13,
                "max_p95": 58,
            }
        },
        "features": features,
        "relations": {
            "profile_name_subtitle_alignment": {
                "label": "昵称与身份说明垂直居中",
                "features": ["text_762965a6", "text_c1c2340b"],
                "metric": "center_y",
                "max_delta": 1,
            }
        },
        "color_samples": {
            "card_surface": {
                "label": "任务卡白色表面",
                "rect": [320, 430, 6, 6],
                "max_channel_delta": 5,
            },
            "today_surface": {
                "label": "今天日期黑色表面",
                "rect": [145, 315, 5, 5],
                "max_channel_delta": 5,
            },
            "expiry_underline_color": {
                "label": "到期时间底部高亮线颜色",
                "rect": [290, 232, 3, 3],
                "max_channel_delta": 6,
            },
            "header_shadow_edge": {
                "label": "任务计划卡片底部阴影边缘",
                "rect": [80, 375, 200, 1],
                "max_channel_delta": 6,
            },
            "header_shadow_fade": {
                "label": "任务计划卡片底部阴影衰减",
                "rect": [80, 380, 200, 1],
                "max_channel_delta": 6,
            },
        },
        "coverage": coverage,
        "pinned_files": {
            relative(path): digest(path) for path in pinned
        },
        "assets": [],
        "fonts": [
            {
                "path": relative(regular_font),
                "family": "SourcePingFang",
                "weight": 400,
                "node_ids": sorted(regular_nodes),
            },
            {
                "path": relative(semibold_font),
                "family": "SourcePingFang",
                "weight": 600,
                "node_ids": sorted(semibold_nodes),
            },
        ],
        "implementation_inputs": [
            "../../flutter_ui_components/lib/experiments/task_plan_44_page.dart",
            "../../flutter_ui_components/lib/main.dart",
            "../../flutter_ui_components/test/task_plan_44_render_test.dart",
            "../../flutter_ui_components/pubspec.yaml",
            "../../flutter_ui_components/pubspec.lock",
            "../../tools/build_task_plan_44_contract.py",
        ],
        "environment": {
            "renderer": "flutter_test_repaint_boundary",
            "renderer_version": "Flutter 3.47.7 / engine deb2874385",
            "platform": "macOS arm64 software rasterizer",
            "locale": "zh_CN",
            "state": "TaskPlan44Screen default deterministic state at 375x812",
            "text_scale": 1,
        },
        "exclude_rects": [
            {"rect": [18, 103, 50, 50], "reason": "头像位图未导出"},
            {"rect": [88, 134, 14, 14], "reason": "关系图标未导出"},
            {"rect": [277, 120, 16, 16], "reason": "发私信图标未导出"},
            {"rect": [33, 219, 20, 20], "reason": "初级任务包图标未导出"},
            {"rect": [33, 440, 39, 39], "reason": "叫醒铃声位图未导出"},
            {"rect": [35, 569, 38, 38], "reason": "睡前陪伴位图未导出"},
            {"rect": [35, 699, 39, 39], "reason": "失眠哄睡位图未导出"},
            {"rect": [270, 675, 65, 65], "reason": "已过期印章未导出"},
        ],
        "max_excluded_fraction": 0.045,
        "not_applicable": {},
    }
    CONTRACT.write_text(json.dumps(contract, ensure_ascii=False, indent=2) + "\n")
    print(f"wrote {CONTRACT}")
    print(f"inventory={len(inventory)} covered={sum(v['status'] == 'covered' for v in coverage.values())} excluded={sum(v['status'] == 'excluded' for v in coverage.values())}")


if __name__ == "__main__":
    main()
