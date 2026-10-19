#!/usr/bin/env python3
"""Build reviewed v2 contracts for the two saved Lanhu evidence bundles.

The initializer remains the source of the draft.  This script records the
project-specific review decisions so coverage can be reproduced and audited.
It never reads a candidate render and therefore cannot tune acceptance limits
to an implementation result.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def node_color(node: dict) -> tuple[int, int, int]:
    raw = node.get("raw_style") or {}
    font = raw.get("font") or {}
    color = font.get("color")
    if color:
        return color["r"], color["g"], color["b"]
    for collection in (raw.get("fills") or [], raw.get("borders") or []):
        for paint in collection:
            if paint.get("isEnabled", True) is False:
                continue
            color = paint.get("color")
            if color:
                return color["r"], color["g"], color["b"]
            stops = ((paint.get("gradient") or {}).get("colorStops") or [])
            if stops:
                color = stops[0]["color"]
                return color["r"], color["g"], color["b"]
    return (255, 255, 255)


ASSET_RGB = {
    "EC741E48-B99B-4FDE-AC53-6D25014604EE": (145, 145, 155),
    "BFD28ECB-F3CC-4BFF-99F0-1449715FBCDB": (76, 193, 104),
    "324B46DA-9403-48D1-BEE5-30A9DD42C03D": (76, 193, 104),
    "CD2154E5-F768-4E1E-AF15-C8537ED0E763": (76, 193, 104),
    "D8100ECE-DEBC-4A99-A7E6-85F223476F24": (230, 181, 94),
    "4D57E0F4-80B9-4090-BF77-DC5811FC8978": (230, 181, 94),
    "72295535-D486-4329-9239-2DE5B4D95F7E": (230, 181, 94),
    "4A941CF3-51F0-4337-A999-F25ECA160903": (232, 199, 123),
    "E0530DED-3970-49D8-AA0F-6FBD35E284E0": (230, 181, 94),
    "43EB1873-0E87-45E1-B98A-E10EC077CEAA": (230, 181, 94),
}


def detector_for(node: dict, *, small: bool = False) -> dict:
    rgb = ASSET_RGB.get(node["node_id"], node_color(node))
    opacity = (node.get("raw_style") or {}).get("opacity", 100)
    if opacity < 100 and min(rgb) >= 220:
        return {"kind": "light", "luma_min": 150, "min_pixels": 8}
    # Exact source color plus anti-aliasing. The ROI is the source node box,
    # so this remains more selective than broad dark/light classification.
    distance = 24 if node["node_id"] == "4A941CF3-51F0-4337-A999-F25ECA160903" else (68 if small else 74)
    return {
        "kind": "color_distance",
        "rgb": list(rgb),
        "max_distance": distance,
        "min_pixels": 4 if small else 8,
    }


def add_feature(contract: dict, node: dict, feature_id: str, *, small=False,
                padding=(2, 2, 2, 2), label: str | None = None) -> str:
    limits = {"max_center_delta": 1.0, "max_size_delta": 1.5}
    if small:
        limits.update({
            "max_edge_delta": 1.0,
            "max_ink_ratio_delta": 0.25,
            "max_mask_iou_loss": 0.25,
        })
    contract["features"][feature_id] = {
        "label": label or node.get("name") or feature_id,
        "node_ids": [node["node_id"]],
        "padding": list(padding),
        "detector": detector_for(node, small=small),
        "limits": limits,
        **({"profile": "small_visual"} if small else {}),
    }
    contract["coverage"][node["node_id"]] = {
        "status": "covered",
        "checks": [f"features.{feature_id}"],
        "reason": "",
    }
    return feature_id


def build(case: str, *, target_order: int, masks: list[dict],
          regions: dict, key_small: set[str], key_assets: set[str],
          relations: list[tuple[str, str, str, str]], colors: dict,
          asset_dir: str, page_file: str, test_file: str,
          hidden_reason: str, max_excluded_fraction: float) -> None:
    base = ROOT / "design_evidence" / case
    draft_path = base / "visual-contract-v2.json"
    contract = json.loads(draft_path.read_text())
    snapshot = json.loads((base / "source/snapshot.json").read_text())
    nodes = {n["node_id"]: n for n in snapshot["nodes"]}
    parents = {n.get("parent_id") for n in nodes.values()}

    def inventory_node(n: dict) -> bool:
        b = n.get("bounds") or {}
        return (n.get("effective_source_visible", n.get("source_visible")) is not False
                and b.get("width", 0) > 0 and b.get("height", 0) > 0
                and (n.get("text") or n.get("asset_ids") or n["node_id"] not in parents))

    inventory = {k: n for k, n in nodes.items() if inventory_node(n)}
    contract.update({
        "status": "ready",
        "source_scope": {"kind": "page", "expected_node_count": len(nodes)},
        "regions": regions,
        "features": {},
        "relations": {},
        "color_samples": colors,
        "exclude_rects": masks,
        "max_excluded_fraction": max_excluded_fraction,
        "not_applicable": {},
        "coverage": {},
        "environment": {
            "renderer": "flutter-test-skia",
            "renderer_version": "Flutter 3.47.7 / engine deb287481e",
            "platform": "macOS widget-test 375x812 @4x",
            "locale": "zh_CN",
            "state": case,
            "text_scale": 1,
        },
    })

    # All non-text, non-asset leaves are still accounted for by blocking
    # regional checks. Salient small visuals receive independent contour gates.
    region_ids = list(contract["regions"])
    default_region = region_ids[0]
    contract["regions"][default_region].setdefault("node_ids", [])

    font_nodes = {"Regular": [], "Medium": [], "Semibold": []}
    feature_by_node: dict[str, str] = {}

    for node_id, node in inventory.items():
        b = node["bounds"]
        order = node.get("source_order", 0)
        is_target = order >= target_order
        is_visible_header = b["y"] < 228
        is_hidden_feed = case == "filter-backup" and not is_target and not is_visible_header
        is_missing_art = any(
            b["x"] >= rect["rect"][0] and b["y"] >= rect["rect"][1]
            and b["x"] + b["width"] <= rect["rect"][0] + rect["rect"][2]
            and b["y"] + b["height"] <= rect["rect"][1] + rect["rect"][3]
            for rect in masks
        )

        if is_hidden_feed:
            contract["coverage"][node_id] = {
                "status": "excluded", "checks": [], "reason": hidden_reason,
            }
            continue
        if is_missing_art and not node.get("text"):
            contract["coverage"][node_id] = {
                "status": "excluded", "checks": [],
                "reason": "原稿未提供可复用素材；实现保留源画框占位，像素内部精确排除",
            }
            continue
        if case == "voice-calling-backup-2" and node_id == "6E6F2830-CE0E-418D-AF3C-360C264577C1":
            contract["coverage"][node_id] = {
                "status": "excluded", "checks": [],
                "reason": "MCP 资源是 56×56，但父组 bounds 错报为 231×501；可见 14×14 子节点另行覆盖",
            }
            continue
        if case == "voice-calling-backup-2" and node_id == "4A941CF3-51F0-4337-A999-F25ECA160903":
            contract["coverage"][node_id] = {
                "status": "excluded", "checks": [],
                "reason": "该导出组同时包含缺失头像内容与金色边框；头像内部已精确遮罩，边框由区域和颜色采样覆盖",
            }
            continue

        if node.get("text"):
            fid = f"text_{node_id[:8].lower()}"
            feature_by_node[node_id] = add_feature(contract, node, fid,
                                                   padding=(2, 2, 2, 2))
            family = ((node.get("raw_style") or {}).get("font") or {}).get("font", "")
            key = "Semibold" if "Semibold" in family else ("Medium" if "Medium" in family else "Regular")
            font_nodes[key].append(node_id)
        elif node_id in key_assets or node.get("asset_ids"):
            fid = f"asset_{node_id[:8].lower()}"
            feature_by_node[node_id] = add_feature(contract, node, fid,
                                                   small=b["width"] <= 24 and b["height"] <= 24,
                                                   padding=(2, 2, 2, 2))
        elif node_id in key_small:
            fid = f"small_{node_id[:8].lower()}"
            feature_by_node[node_id] = add_feature(contract, node, fid, small=True,
                                                   padding=(2, 2, 2, 2))
        else:
            contract["regions"][default_region]["node_ids"].append(node_id)
            contract["coverage"][node_id] = {
                "status": "covered", "checks": [f"regions.{default_region}"], "reason": "",
            }

    for relation_id, first_node, second_node, metric in relations:
        if first_node not in feature_by_node or second_node not in feature_by_node:
            continue
        contract["relations"][relation_id] = {
            "label": relation_id.replace("_", " "),
            "features": [feature_by_node[first_node], feature_by_node[second_node]],
            "metric": metric,
            "max_delta": 1.0,
        }

    # Region coverage references node IDs, so keep the separate geometric
    # regions rect-based and let the whole-page region own the shape inventory.
    if not contract["relations"]:
        contract["not_applicable"]["relations"] = "该页面无适合自动分割的跨特征关系"

    rel_asset_dir = Path("../../flutter_ui_components") / asset_dir
    asset_paths = sorted((rel_asset_dir / p.name).as_posix()
                         for p in (ROOT / "flutter_ui_components" / asset_dir).glob("*.png"))
    font_paths = [f"../../flutter_ui_components/assets/fonts/PingFangSC-{weight}.otf" for weight in ("Regular", "Medium", "Semibold")]
    contract["assets"] = asset_paths
    contract["fonts"] = [
        {"path": f"../../flutter_ui_components/assets/fonts/PingFangSC-{weight}.otf",
         "node_ids": font_nodes[weight]}
        for weight in ("Regular", "Medium", "Semibold") if font_nodes[weight]
    ]
    contract["implementation_inputs"] = [
        f"../../flutter_ui_components/{page_file}",
        f"../../flutter_ui_components/{test_file}",
        "../../flutter_ui_components/pubspec.yaml",
        "../../flutter_ui_components/pubspec.lock",
    ]
    pinned = {}
    for rel in [contract["reference"], *contract["source_documents"], *contract["assets"], *font_paths]:
        pinned[rel] = sha(base / rel)
    contract["pinned_files"] = pinned
    draft_path.write_text(json.dumps(contract, ensure_ascii=False, indent=2) + "\n")


build(
    "filter-backup",
    target_order=163,
    masks=[
        {"rect": [8, 99, 177, 236], "reason": "发现页照片 1 未提供切图"},
        {"rect": [190, 99, 177, 236], "reason": "发现页照片 2 未提供切图"},
        {"rect": [41, 488, 33, 33], "reason": "待配置任务图标 1 未提供切图"},
        {"rect": [41, 541, 33, 33], "reason": "待配置任务图标 2 未提供切图"},
        {"rect": [41, 598, 33, 33], "reason": "待配置任务图标 3 未提供切图"},
        {"rect": [41, 653, 33, 33], "reason": "待配置任务图标 4 未提供切图"},
    ],
    max_excluded_fraction=.30,
    regions={
        "whole": {"label": "完整页面与模态结构", "rect": [0, 0, 375, 812], "max_mae": 8, "max_p95": 32},
        "header": {"label": "发现页头部", "rect": [0, 0, 375, 99], "max_mae": 8, "max_p95": 32},
        "sheet": {"label": "任务配置弹层", "rect": [0, 228, 375, 584], "max_mae": 8, "max_p95": 32},
        "enabled": {"label": "已开启任务卡", "rect": [23, 327, 329, 107], "max_mae": 6, "max_p95": 28},
        "pending": {"label": "待配置任务卡", "rect": [23, 476, 329, 223], "max_mae": 8, "max_p95": 40},
        "cta": {"label": "底部配置按钮", "rect": [28, 727, 320, 50], "max_mae": 6, "max_p95": 28},
    },
    key_small={"22438CCE-EE42-46D8-AA24-84E67BC616B5", "1F31BB7E-DC49-4DC0-B4D8-847D9A7D1DB5",
               "4D1D7632-99B0-4D09-9D04-48B9F9D8A5E8", "BEA17D4C-7C03-4971-B8C0-4EB7EC40DF52",
               "1787F90C-3062-4B67-B44E-AF4F63A3DC78"},
    key_assets={"EC741E48-B99B-4FDE-AC53-6D25014604EE", "D8100ECE-DEBC-4A99-A7E6-85F223476F24",
                "4D57E0F4-80B9-4090-BF77-DC5811FC8978", "72295535-D486-4329-9239-2DE5B4D95F7E",
                "BFD28ECB-F3CC-4BFF-99F0-1449715FBCDB", "324B46DA-9403-48D1-BEE5-30A9DD42C03D",
                "CD2154E5-F768-4E1E-AF15-C8537ED0E763"},
    relations=[
        ("enabled_video_label_center", "13DB3947-C4E9-4177-BAB1-A654EF02ED02", "D8100ECE-DEBC-4A99-A7E6-85F223476F24", "center_x"),
        ("enabled_voice_label_center", "EDC9B047-AAAC-4E24-8407-350E465E9CC3", "4D57E0F4-80B9-4090-BF77-DC5811FC8978", "center_x"),
        ("enabled_message_label_center", "BA001932-8CF2-4C39-ABE3-8648C9D2A532", "72295535-D486-4329-9239-2DE5B4D95F7E", "center_x"),
        ("row2_title_left", "41FCD954-872E-47D2-8A5F-F15299BCF22C", "8BE4E858-D40F-4166-BDBD-1D394A5264AD", "left"),
        ("row3_title_left", "16C55B4B-206C-4526-A5FC-5DB3664ECC65", "A73089C2-FA84-4559-B937-4A75E3CFE9D5", "left"),
        ("row4_title_left", "234E4AB7-62A9-41D3-8956-D3E030F0602E", "B98B2E8C-8B9D-41FF-9441-1AAC6DE65334", "left"),
    ],
    colors={
        "sheet_top": {"label": "弹层顶部暖白", "rect": [8, 232, 8, 8], "max_channel_delta": 8},
        "enabled_surface": {"label": "已开启卡底色", "rect": [30, 330, 8, 8], "max_channel_delta": 8},
        "pending_surface": {"label": "待配置卡底色", "rect": [30, 480, 8, 8], "max_channel_delta": 8},
        "cta_surface": {"label": "CTA 深色渐变", "rect": [48, 748, 8, 8], "max_channel_delta": 8},
    },
    asset_dir="assets/lanhu/filter_backup/assets",
    page_file="lib/experiments/filter_backup_page.dart",
    test_file="test/filter_backup_render_test.dart",
    hidden_reason="该节点属于弹层下方的发现页信息流，在目标状态被不透明任务弹层遮挡",
)

build(
    "voice-calling-backup-2",
    target_order=0,
    masks=[{"rect": [148, 178, 80, 80], "reason": "通话头像原图未提供切图；圆形占位另由 Widget 测试验证"}],
    max_excluded_fraction=.05,
    regions={
        "whole": {"label": "完整语音通话页", "rect": [0, 0, 375, 812], "max_mae": 8, "max_p95": 32},
        "top": {"label": "顶部状态与控制", "rect": [0, 0, 375, 168], "max_mae": 8, "max_p95": 32},
        "hero": {"label": "头像、波形与关系区", "rect": [34, 155, 308, 225], "max_mae": 8, "max_p95": 36},
        "safety": {"label": "安全提示", "rect": [14, 611, 278, 45], "max_mae": 8, "max_p95": 36},
        "dialogue": {"label": "通话字幕", "rect": [14, 664, 241, 56], "max_mae": 8, "max_p95": 44},
        "actions": {"label": "底部操作", "rect": [14, 731, 289, 41], "max_mae": 8, "max_p95": 44},
    },
    key_small={"49007501-5875-43D5-B501-FF8BD569F85C", "AB224340-CB06-499F-86A5-0B34DF69E08C",
               "B87B8D16-E2EA-4F14-AFF2-2379FBAC6716", "6528939A-60B3-46AB-92F8-0DFD6991322D",
               "653A1AED-2B33-425A-A355-C2388B000FC2", "87A6694E-321D-4E74-BF33-41EE03CD5F60",
               "10A8C121-166C-4CEA-8670-781AB8E77566", "0BB692BF-25E7-47B8-BB07-5599C1D20E52",
               "5EDE0259-DDD6-4662-A4C8-754A77B26329", "1FCAD52F-1878-4CC3-A9A0-9F46BD57F284"},
    key_assets={"4A941CF3-51F0-4337-A999-F25ECA160903", "E0530DED-3970-49D8-AA0F-6FBD35E284E0",
                "43EB1873-0E87-45E1-B98A-E10EC077CEAA"},
    relations=[
        ("title_status_center", "083E2038-71D8-437E-864B-FD35A0C40881", "18247A44-B395-4F81-B549-4B9981091C6C", "center_x"),
        ("avatar_name_center", "4A941CF3-51F0-4337-A999-F25ECA160903", "1B407962-7657-4887-A5E5-49EFC08E0A0C", "center_x"),
        ("relationship_arrow_center", "AC5C9681-EAF5-4936-ADA2-69E6050A5B80", "5EDE0259-DDD6-4662-A4C8-754A77B26329", "center_y"),
        ("safety_icon_text_top", "E0530DED-3970-49D8-AA0F-6FBD35E284E0", "992FAFBD-F482-486B-BF93-C26A07ED8485", "top"),
    ],
    colors={
        "background_top": {"label": "顶部背景", "rect": [8, 96, 8, 8], "max_channel_delta": 8},
        "background_hero": {"label": "主视觉光场", "rect": [185, 340, 8, 8], "max_channel_delta": 8},
        "background_lower": {"label": "下部暖色光场", "rect": [330, 640, 8, 8], "max_channel_delta": 8},
        "avatar_ring_edge": {"label": "头像金色外环", "rect": [138, 216, 3, 4], "max_channel_delta": 8},
        "message_glass": {"label": "消息按钮玻璃材质", "rect": [22, 737, 8, 8], "max_channel_delta": 8},
    },
    asset_dir="assets/lanhu/voice_calling_backup_2/assets",
    page_file="lib/experiments/voice_calling_backup_2_page.dart",
    test_file="test/voice_calling_backup_2_render_test.dart",
    hidden_reason="不适用",
)

