"""Freeze the reviewed v2 contract for the 1备份 45 cold-start run."""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SOURCE_FILES = [ROOT / "source" / f"region-{index}.json" for index in (1, 2, 3)]
CONTRACT = ROOT / "visual-contract-final.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


nodes: dict[str, dict] = {}
for source in SOURCE_FILES:
    for node in json.loads(source.read_text(encoding="utf-8"))["nodes"]:
        nodes[node["node_id"]] = node

parents = {node.get("parent_id") for node in nodes.values()}
inventory = {
    node_id: node
    for node_id, node in nodes.items()
    if node.get("effective_source_visible", node.get("source_visible")) is not False
    and node.get("bounds", {}).get("width", 0) > 0
    and node.get("bounds", {}).get("height", 0) > 0
    and (node.get("text") or node.get("asset_ids") or node_id not in parents)
}

missing_bitmap_ids = {
    "1099297A-C920-4DC0-84B9-9D950348AF8A",
    "91C7F81B-BBAB-4A81-AF88-0DF6194FDCBD",
    "FF75EE8E-F764-423A-973B-8CCD6C8E3499",
    "506F6A95-2DFC-4F73-B1A7-2EA2F755E1A4",
    "9AA03999-E623-438A-96D5-DCFB3BE0CE59",
    "2C34E24F-8122-4743-A948-449551EDF921",
    "D046C2A8-0AD8-4167-ABE8-80C765C91008",
    "BFE10B6B-F12E-459D-9AC3-F0235C7BFF65",
    "109A27EE-A12C-4E3C-B782-DC637A1ED913",
    "15F0F477-CEA7-4135-BD2F-8DEC2712E08E",
    "71E736BD-69F4-4BBB-AA46-E1825CEB7E8D",
}
bad_bounds_assets = {
    "A17B4782-E31F-49C6-9872-73BCCCFAF1CE": "蓝湖返回的关系图标组边界为 152×752，与可见 14×14 图标不一致；已使用导出原图并人工核对",
    "67548D3B-BC03-40CB-B6C2-724FEEA4FE16": "礼物卡背景原图与未切礼物/星币图层重叠，颜色分割会被缺图占位污染；原始 PNG 哈希与整卡区域继续受门禁约束",
}


def text_rgb(node: dict) -> list[int]:
    runs = node.get("text_spec", {}).get("text_runs", [])
    value = runs[0].get("color", "") if runs else ""
    match = re.search(r"rgba\((\d+),(\d+),(\d+),", value)
    return [int(match.group(i)) for i in (1, 2, 3)] if match else [34, 36, 42]


features: dict[str, dict] = {}
coverage: dict[str, dict] = {}
region_nodes: list[str] = []
font_nodes = {"regular": [], "semibold": [], "fallback": []}

for node_id, node in inventory.items():
    short = node_id.split("-")[0].lower()
    if node_id in missing_bitmap_ids:
        coverage[node_id] = {
            "status": "excluded",
            "checks": [],
            "reason": "蓝湖节点只有位图引用而无可导出原始素材；Flutter 使用同形占位，几何由组件测试覆盖",
        }
        continue
    if node_id in bad_bounds_assets:
        coverage[node_id] = {
            "status": "excluded",
            "checks": [],
            "reason": bad_bounds_assets[node_id],
        }
        continue
    if node.get("text"):
        feature_id = f"text_{short}"
        features[feature_id] = {
            "label": f"文字：{node['text']}",
            "node_ids": [node_id],
            "padding": [2, 2, 2, 2],
            "detector": {
                "kind": "color_distance",
                "rgb": text_rgb(node),
                "max_distance": 72,
                "min_pixels": 4,
            },
            "limits": {"max_center_delta": 2.0, "max_size_delta": 3.0},
        }
        family = node.get("text_spec", {}).get("text_runs", [{}])[0].get("font_family", "")
        if node_id == "36B70533-B6B5-43C5-B7AE-2BCE24788E85":
            font_nodes["fallback"].append(node_id)
        else:
            font_nodes["semibold" if "Semibold" in family else "regular"].append(node_id)
        coverage[node_id] = {"status": "covered", "checks": [f"features.{feature_id}"], "reason": ""}
    elif node.get("asset_ids"):
        feature_id = f"asset_{short}"
        is_large = node_id == "67548D3B-BC03-40CB-B6C2-724FEEA4FE16"
        spec = {
            "label": f"蓝湖原始切图：{node.get('name') or short}",
            "node_ids": [node_id],
            "padding": [2, 2, 2, 2],
            "detector": {
                "kind": "gold" if is_large else "dark",
                "luma_max": 210,
                "min_pixels": 4,
            },
            "limits": {"max_center_delta": 2.0, "max_size_delta": 3.0},
        }
        if not is_large:
            spec["profile"] = "small_visual"
            spec["limits"].update(
                max_edge_delta=2.0,
                max_ink_ratio_delta=0.45,
                max_mask_iou_loss=0.55,
            )
        features[feature_id] = spec
        coverage[node_id] = {"status": "covered", "checks": [f"features.{feature_id}"], "reason": ""}
    else:
        region_nodes.append(node_id)
        coverage[node_id] = {"status": "covered", "checks": ["regions.whole"], "reason": ""}

asset_paths = sorted(
    "../../flutter_ui_components/assets/lanhu/message_backup_45/assets/" + path.name
    for path in (ROOT / "source" / "assets" / "assets").glob("*.png")
)
fonts = [
    {"path": "../../flutter_ui_components/assets/fonts/PingFangSC-Regular.otf", "node_ids": font_nodes["regular"]},
    {"path": "../../flutter_ui_components/assets/fonts/PingFangSC-Semibold.otf", "node_ids": font_nodes["semibold"]},
    {"path": "../../flutter_ui_components/assets/fonts/ArialUnicode-Gift.ttf", "node_ids": font_nodes["fallback"]},
]
implementation_inputs = [
    "../../flutter_ui_components/lib/main.dart",
    "../../flutter_ui_components/lib/experiments/two_page_fidelity_lab.dart",
    "../../flutter_ui_components/lib/experiments/message_backup_45_page.dart",
    "../../flutter_ui_components/test/message_backup_45_render_test.dart",
    "../../flutter_ui_components/pubspec.yaml",
    "../../flutter_ui_components/pubspec.lock",
]

contract = {
    "schema_version": 2,
    "status": "ready",
    "name": "1备份 45",
    "source_snapshot": "4c1aaffb700882fdac4b8c53752b2b88",
    "source_version": "2d5f61f5-e46d-4412-9f7b-98359416f994",
    "canvas": [375, 812],
    "render_scale": 4.0,
    "reference": "source/reference.png",
    "source_documents": ["source/region-1.json", "source/region-2.json", "source/region-3.json"],
    "regions": {
        "whole": {"label": "完整聊天页面", "rect": [0, 0, 375, 812], "node_ids": region_nodes, "max_mae": 10, "max_p95": 42},
        "header": {"label": "状态栏与会话标题", "rect": [0, 0, 375, 121], "max_mae": 11, "max_p95": 46},
        "conversation": {"label": "消息内容区域", "rect": [0, 121, 375, 551], "max_mae": 10, "max_p95": 42},
        "composer": {"label": "底部输入与工具区", "rect": [0, 672, 375, 140], "max_mae": 9, "max_p95": 38},
    },
    "features": features,
    "pinned_files": {},
    "assets": asset_paths,
    "fonts": fonts,
    "implementation_inputs": implementation_inputs,
    "environment": {
        "renderer": "flutter-test-skia",
        "renderer_version": "Flutter 3.47.7 / engine deb287481e",
        "platform": "macOS widget-test 375x812 @4x",
        "locale": "zh_CN",
        "state": "message-backup-45-chat-static",
        "text_scale": 1,
    },
    "exclude_rects": [
        {"rect": [44, 51, 30, 30], "reason": "顶部头像原图未提供；保留圆形缺图占位"},
        {"rect": [17, 135, 30, 30], "reason": "聊天头像原图未提供；保留圆形缺图占位"},
        {"rect": [17, 187, 30, 30], "reason": "聊天头像原图未提供；保留圆形缺图占位"},
        {"rect": [331, 240, 30, 30], "reason": "本人头像原图未提供；保留圆形缺图占位"},
        {"rect": [17, 298, 30, 30], "reason": "聊天头像原图未提供；保留圆形缺图占位"},
        {"rect": [331, 357, 30, 30], "reason": "本人头像原图未提供；保留圆形缺图占位"},
        {"rect": [17, 412, 30, 30], "reason": "聊天头像原图未提供；保留圆形缺图占位"},
        {"rect": [17, 465, 30, 30], "reason": "聊天头像原图未提供；保留圆形缺图占位"},
        {"rect": [17, 518, 30, 30], "reason": "聊天头像原图未提供；保留圆形缺图占位"},
        {"rect": [62, 527, 55, 55], "reason": "礼物图片原图未提供；保留圆角缺图占位"},
        {"rect": [121, 558, 19, 19], "reason": "星币图片原图未提供；保留圆形缺图占位"},
    ],
    "max_excluded_fraction": 0.05,
    "not_applicable": {},
    "relations": {
        "voice_left_alignment": {
            "label": "左侧语音波形与时长垂直对齐",
            "features": ["asset_1139571f", "text_5c7a0789"],
            "metric": "center_y",
            "max_delta": 1.5,
        },
        "header_relation_alignment": {
            "label": "标题与关系入口垂直关系",
            "features": ["text_3bc3f877", "text_1209c315"],
            "metric": "center_y",
            "max_delta": 1.5,
        },
    },
    "color_samples": {
        "page_background": {"label": "会话背景", "rect": [365, 300, 6, 40], "max_channel_delta": 5},
        "composer_surface": {"label": "底部输入区背景", "rect": [4, 760, 6, 30], "max_channel_delta": 7},
    },
    "source_scope": {"kind": "page", "expected_node_count": 143},
    "coverage": coverage,
}

pin_paths = [contract["reference"], *contract["source_documents"], *asset_paths, *(item["path"] for item in fonts)]
contract["pinned_files"] = {path: sha256((ROOT / path).resolve()) for path in pin_paths}
CONTRACT.write_text(json.dumps(contract, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"nodes": len(nodes), "inventory": len(inventory), "features": len(features), "excluded_nodes": len(missing_bitmap_ids) + len(bad_bounds_assets)}, ensure_ascii=False))
