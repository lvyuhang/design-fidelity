"""Source-backed visual fidelity gate for design-to-code renders.

The gate reads element bounds from saved MCP node evidence, segments visible ink
inside each element, and compares geometry and relationships with the reference.
It also keeps regional pixel metrics as a coarse regression signal.  A blocking
failure exits with status 1 so the same command can be used locally and in CI.
"""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
import math

from fidelity_contract import (read_json, validate_contract, verify_files,
    verify_fonts, verify_receipt, sha256)
from pathlib import Path
from typing import Any

from exclusion_masks import build_keep_mask
from geometry_probe import DEFAULT_BLOCKING, compare_geometry, geometry_path, responsive_report

import numpy as np
from PIL import Image, ImageDraw, ImageFilter


def _load_nodes(paths: list[Path]) -> dict[str, dict[str, Any]]:
    nodes: dict[str, dict[str, Any]] = {}
    for path in paths:
        data = read_json(path)
        for node in [*data.get("ancestors", []), *data.get("nodes", [])]:
            node_id = node.get("node_id")
            if node_id:
                if node_id in nodes and nodes[node_id].get("bounds") != node.get("bounds"):
                    raise ValueError(f"Conflicting bounds for source node {node_id}")
                nodes[node_id] = {**nodes.get(node_id, {}), **node}
    return nodes


def _validate_evidence(paths: list[Path], contract: dict[str, Any]) -> None:
    documents = [read_json(path) for path in paths]
    snapshots = {item.get("snapshot_id") for item in documents}
    versions = {item.get("resolved_version") for item in documents}
    canvases = {
        (item.get("canvas", {}).get("width"), item.get("canvas", {}).get("height"))
        for item in documents
    }
    if len(snapshots) != 1 or None in snapshots:
        raise ValueError(f"MCP evidence mixes or omits snapshot_id: {snapshots}")
    if len(versions) != 1 or None in versions:
        raise ValueError(f"MCP evidence mixes or omits resolved_version: {versions}")
    if len(canvases) != 1 or None in next(iter(canvases)):
        raise ValueError(f"MCP evidence mixes or omits canvas: {canvases}")
    for path, item in zip(paths, documents):
        mapping = item.get("coordinate_mapping", {})
        if item.get("coordinate_space") != "source_canvas" or not mapping.get("verified"):
            raise ValueError(f"Unverified source_canvas mapping in {path}")
    if contract.get("source_snapshot") not in (None, next(iter(snapshots))):
        raise ValueError("Contract source_snapshot does not match MCP evidence")
    if contract.get("source_version") not in (None, next(iter(versions))):
        raise ValueError("Contract source_version does not match MCP evidence")
    scope = contract.get("source_scope", {})
    counts = {d["total_nodes"] for d in documents if d.get("total_nodes")}
    if scope.get("kind") == "page" and counts and counts != {scope.get("expected_node_count")}:
        raise ValueError("Declared node count differs from MCP evidence")
    if tuple(contract["canvas"]) != next(iter(canvases)):
        raise ValueError("Contract canvas does not match MCP evidence")


def _union_bounds(node_ids: list[str], nodes: dict[str, dict[str, Any]]) -> list[float]:
    missing = [node_id for node_id in node_ids if node_id not in nodes]
    if missing:
        raise ValueError(f"MCP evidence is missing node IDs: {', '.join(missing)}")
    bounds = [nodes[node_id]["bounds"] for node_id in node_ids]
    left = min(item["x"] for item in bounds)
    top = min(item["y"] for item in bounds)
    right = max(item["x"] + item["width"] for item in bounds)
    bottom = max(item["y"] + item["height"] for item in bounds)
    return [left, top, right - left, bottom - top]


def _padded_roi(bounds: list[float], padding: list[float]) -> list[float]:
    left, top, width, height = bounds
    pad_left, pad_top, pad_right, pad_bottom = padding
    return [
        left - pad_left,
        top - pad_top,
        width + pad_left + pad_right,
        height + pad_top + pad_bottom,
    ]


def _pixels(image: np.ndarray, roi: list[float], scale: float) -> tuple[np.ndarray, int, int]:
    left, top, width, height = roi
    x1 = max(0, round(left * scale))
    y1 = max(0, round(top * scale))
    x2 = min(image.shape[1], round((left + width) * scale))
    y2 = min(image.shape[0], round((top + height) * scale))
    if width <= 0 or height <= 0 or x2 <= x1 or y2 <= y1:
        raise ValueError(f"Empty/out-of-canvas ROI: {roi}")
    return image[y1:y2, x1:x2], x1, y1


def _mask(pixels: np.ndarray, detector: dict[str, Any]) -> np.ndarray:
    values = pixels.astype(np.float64)
    red, green, blue = values[:, :, 0], values[:, :, 1], values[:, :, 2]
    kind = detector["kind"]
    if kind == "enclosed_container":
        # Fill only enclosed holes; exterior-connected background stays exterior.
        from PIL import ImageDraw
        base = detector['foreground']
        if base.get('kind') == 'enclosed_container':
            raise ValueError('Nested container detectors are unsupported')
        mask = _mask(pixels, base)
        padded = np.pad(mask, 1, constant_values=False)
        flood = Image.fromarray((padded * 255).astype(np.uint8)).copy()
        ImageDraw.floodfill(flood, (0, 0), 128)
        return (np.asarray(flood)[1:-1, 1:-1] != 128)
    if kind == "dark":
        return values.mean(axis=2) <= detector.get("luma_max", 165)
    if kind == "relative_dark":
        luma=values.mean(axis=2)
        background=np.percentile(luma,detector.get("percentile",80))
        return luma <= background-detector["delta"]
    if kind == "light":
        return values.mean(axis=2) >= detector.get("luma_min", 220)
    if kind == "gold":
        return (
            (red >= detector.get("red_min", 100))
            & (red - blue >= detector.get("red_blue_min", 18))
            & (green - blue >= detector.get("green_blue_min", 8))
            & (red - green >= detector.get("red_green_min", -8))
        )
    if kind == "color_distance":
        target = np.asarray(detector["rgb"], dtype=np.float64)
        distance = np.linalg.norm(values - target, axis=2)
        return distance <= detector.get("max_distance", 20)
    if kind == "channel_range":
        red_range = detector.get("red", [0, 255])
        green_range = detector.get("green", [0, 255])
        blue_range = detector.get("blue", [0, 255])
        return (
            (red >= red_range[0]) & (red <= red_range[1])
            & (green >= green_range[0]) & (green <= green_range[1])
            & (blue >= blue_range[0]) & (blue <= blue_range[1])
        )
    raise ValueError(f"Unsupported detector: {kind}")


def _measure_feature(
    image: np.ndarray,
    roi: list[float],
    scale: float,
    detector: dict[str, Any],
) -> dict[str, Any] | None:
    pixels, x1, y1 = _pixels(image, roi, scale)
    mask = _mask(pixels, detector)
    ys, xs = np.where(mask)
    if len(xs) < detector.get("min_pixels", 8):
        return None
    left = (x1 + int(xs.min())) / scale
    top = (y1 + int(ys.min())) / scale
    right = (x1 + int(xs.max()) + 1) / scale
    bottom = (y1 + int(ys.max()) + 1) / scale
    return {
        "bbox": [left, top, right - left, bottom - top],
        "center": [(x1 + float(xs.mean())) / scale, (y1 + float(ys.mean())) / scale],
        "ink_pixels": int(len(xs)),
    }


def _feature_comparison(reference: dict[str, Any], actual: dict[str, Any]) -> dict[str, float]:
    rb, ab = reference["bbox"], actual["bbox"]
    reference_edges = [rb[0], rb[1], rb[0] + rb[2], rb[1] + rb[3]]
    actual_edges = [ab[0], ab[1], ab[0] + ab[2], ab[1] + ab[3]]
    return {
        "center_x_delta": round(actual["center"][0] - reference["center"][0], 4),
        "center_y_delta": round(actual["center"][1] - reference["center"][1], 4),
        "width_delta": round(ab[2] - rb[2], 4),
        "height_delta": round(ab[3] - rb[3], 4),
        "max_edge_delta": round(max(abs(a - b) for a, b in zip(actual_edges, reference_edges)), 4),
        "ink_ratio": round(actual["ink_pixels"] / reference["ink_pixels"], 4),
    }


def _mask_iou_loss(reference, actual, roi, scale, detector):
    """Compare segmented shapes in the same source coordinates; never realign them."""
    ref = _mask(_pixels(reference, roi, scale)[0], detector)
    act = _mask(_pixels(actual, roi, scale)[0], detector)
    union = int(np.count_nonzero(ref | act))
    return 1.0 - float(np.count_nonzero(ref & act)) / union if union else 0.0


def _check_feature(metrics: dict[str, float], limits: dict[str, float]) -> list[str]:
    failures: list[str] = []
    center_limit = limits.get("max_center_delta")
    if center_limit is not None:
        for axis in ("center_x_delta", "center_y_delta"):
            if abs(metrics[axis]) > center_limit:
                failures.append(f"{axis}={metrics[axis]:.2f}px > {center_limit:.2f}px")
    size_limit = limits.get("max_size_delta")
    if size_limit is not None:
        for axis in ("width_delta", "height_delta"):
            if abs(metrics[axis]) > size_limit:
                failures.append(f"{axis}={metrics[axis]:.2f}px > {size_limit:.2f}px")
    edge_limit = limits.get("max_edge_delta")
    if edge_limit is not None and metrics["max_edge_delta"] > edge_limit:
        failures.append(
            f"max_edge_delta={metrics['max_edge_delta']:.2f}px > {edge_limit:.2f}px"
        )
    ink_limit = limits.get("max_ink_ratio_delta")
    if ink_limit is not None and abs(metrics["ink_ratio"] - 1) > ink_limit:
        failures.append(
            f"ink_ratio={metrics['ink_ratio']:.3f}; |ratio-1| > {ink_limit:.3f}"
        )
    shape_limit = limits.get('max_mask_iou_loss')
    if shape_limit is not None and metrics['mask_iou_loss'] > shape_limit:
        failures.append(f"mask_iou_loss={metrics['mask_iou_loss']:.4f} > {shape_limit:.4f}")
    return failures


def _region_metric(reference: np.ndarray, actual: np.ndarray, rect: list[float], scale: float, keep=None) -> dict[str, float]:
    ref_pixels, _, _ = _pixels(reference, rect, scale)
    actual_pixels, _, _ = _pixels(actual, rect, scale)
    delta = np.abs(ref_pixels.astype(np.float64) - actual_pixels.astype(np.float64))
    total_pixels = delta.shape[0] * delta.shape[1]
    if keep is not None:
        selected, _, _ = _pixels(keep, rect, scale)
        delta = delta[selected]
        if not len(delta):
            raise ValueError("Region completely excluded by masks")
    return {
        "compared_pixels": int(delta.size // 3),
        "total_pixels": total_pixels,
        "mae": round(float(delta.mean()), 4),
        "p95_max_channel": round(float(np.percentile(delta.max(axis=-1), 95)), 4),
    }


def _vector_effect_metric(reference: np.ndarray, actual: np.ndarray,
                          rect: list[float], scale: float, keep=None) -> dict[str, float]:
    """Compare a source border at its final logical display scale.

    Four-times screenshots expose rasterizer-specific subpixel antialiasing and
    dash phase that users do not see at the target 1x viewport.  Downsampling
    and a sub-logical-pixel low-pass preserve missing, shifted, thin, thick or
    malformed borders while avoiding false failures from equivalent vectors.
    """
    ref_pixels, _, _ = _pixels(reference, rect, scale)
    actual_pixels, _, _ = _pixels(actual, rect, scale)
    width = max(1, round(rect[2]))
    height = max(1, round(rect[3]))

    def perceptual(values: np.ndarray) -> np.ndarray:
        return np.asarray(
            Image.fromarray(values.astype(np.uint8))
            .resize((width, height), Image.Resampling.LANCZOS)
            # 0.75 suppresses a one-physical-pixel 4x AA/dash-phase change,
            # while retaining a one-logical-pixel shift and stroke-width loss.
            .filter(ImageFilter.GaussianBlur(0.75)),
            dtype=np.float64,
        )

    delta = np.abs(perceptual(ref_pixels) - perceptual(actual_pixels))
    total_pixels = delta.shape[0] * delta.shape[1]
    if keep is not None:
        selected, _, _ = _pixels(keep, rect, scale)
        selected = np.asarray(
            Image.fromarray((selected.astype(np.uint8) * 255), 'L')
            .resize((width, height), Image.Resampling.NEAREST)
        ) > 0
        delta = delta[selected]
    if delta.size == 0:
        raise ValueError('Region completely excluded by masks')
    per_pixel = delta.max(axis=-1) if delta.ndim == 3 else delta
    return {
        'compared_pixels': int(delta.shape[0] if delta.ndim == 2 else delta.shape[0] * delta.shape[1]),
        'total_pixels': int(total_pixels),
        'mae': round(float(delta.mean()), 4),
        'p95_max_channel': round(float(np.percentile(per_pixel, 95)), 4),
    }


def _color_sample_rect(spec: dict[str, Any], nodes: dict[str, dict[str, Any]]) -> list[float]:
    if "rect" in spec:
        return spec["rect"]
    bounds = _union_bounds(spec["node_ids"], nodes)
    anchor_x, anchor_y = spec.get("anchor", [0.5, 0.5])
    width, height = spec.get("size", [4, 4])
    center_x = bounds[0] + bounds[2] * anchor_x
    center_y = bounds[1] + bounds[3] * anchor_y
    return [center_x - width / 2, center_y - height / 2, width, height]


def _mean_rgb(image: np.ndarray, rect: list[float], scale: float) -> list[float]:
    pixels, _, _ = _pixels(image, rect, scale)
    return [round(float(value), 2) for value in pixels.reshape(-1, 3).mean(axis=0)]


def _metric_value(feature: dict[str, Any], key: str) -> float:
    if key == "center_x":
        return float(feature["center"][0])
    if key == "center_y":
        return float(feature["center"][1])
    bbox = feature["bbox"]
    return {
        "left": bbox[0],
        "top": bbox[1],
        "right": bbox[0] + bbox[2],
        "bottom": bbox[1] + bbox[3],
    }[key]


def _draw_overlay(
    candidate_image: Image.Image,
    reference_features: dict[str, dict[str, Any]],
    actual_features: dict[str, dict[str, Any]],
    scale: float,
    output: Path,
) -> None:
    overlay = candidate_image.convert("RGB").copy()
    draw = ImageDraw.Draw(overlay)
    for feature_id, reference in reference_features.items():
        actual = actual_features.get(feature_id)
        for measured, color in ((reference, "#15A46B"), (actual, "#E13D8C")):
            if measured is None:
                continue
            left, top, width, height = measured["bbox"]
            rect = tuple(round(value * scale) for value in (left, top, left + width, top + height))
            draw.rectangle(rect, outline=color, width=max(2, round(scale)))
            center_y = round(measured["center"][1] * scale)
            draw.line((rect[0], center_y, rect[2], center_y), fill=color, width=max(1, round(scale / 2)))
    overlay.save(output)


def _status_cell(passed: bool) -> str:
    label, color = ("PASS", "#137A52") if passed else ("FAIL", "#C6293E")
    return f'<strong style="color:{color}">{label}</strong>'


def _verify_sidecar(path: Path, receipt_path: Path | None, diagnostic: bool) -> None:
    """A geometry sidecar counts only if the receipt recorded these exact bytes."""
    if diagnostic or receipt_path is None or not path.is_file():
        return
    recorded = read_json(receipt_path).get('sidecars', {})
    if recorded.get(path.name) != sha256(path):
        raise ValueError(f'{path.name} is not bound to the render receipt; re-render')


def _geometry_html(candidate: dict[str, Any]) -> str:
    parts = []
    probe = candidate.get("geometry")
    if probe:
        rows = "".join(
            f"<tr><td>{html.escape(item['label'])}</td><td>{html.escape(', '.join(item['failures']))}</td></tr>"
            for item in probe["failures"])
        parts.append(f"<h3>节点几何门禁（{probe['checked']} 个节点）· {_status_cell(probe['passed'])}</h3>"
                     f"<table><tr><th>节点</th><th>偏差</th></tr>{rows}</table>")
    responsive = candidate.get("responsive")
    if responsive:
        rows = "".join(
            f"<tr><td>{html.escape(str(item.get('variant', '')))}</td><td>{html.escape(item['kind'])}</td>"
            f"<td>{html.escape(item['message'])}</td></tr>" for item in responsive["findings"][:60])
        parts.append(f"<h3>多尺寸/字体缩放 · {_status_cell(responsive['passed'])}</h3>"
                     f"<table><tr><th>变体</th><th>类型</th><th>说明</th></tr>{rows}</table>")
    return "".join(parts)


def _write_html(report: dict[str, Any], output: Path) -> None:
    candidates = []
    for candidate_id, candidate in report["candidates"].items():
        region_rows = "".join(
            f"<tr><td>{html.escape(region['label'])}</td><td>{region['metrics']['mae']:.4f}</td>"
            f"<td>{region['metrics']['p95_max_channel']:.2f}</td><td>{_status_cell(region['passed'])}</td>"
            f"<td>{html.escape('; '.join(region['failures']))}</td></tr>"
            for region in candidate["regions"].values()
        )
        feature_rows = "".join(
            f"<tr><td>{html.escape(feature['label'])}</td><td>{feature['metrics'].get('center_x_delta', 0):.2f}</td>"
            f"<td>{feature['metrics'].get('center_y_delta', 0):.2f}</td>"
            f"<td>{feature['metrics'].get('width_delta', 0):.2f}</td>"
            f"<td>{feature['metrics'].get('height_delta', 0):.2f}</td>"
            f"<td>{_status_cell(feature['passed'])}</td><td>{html.escape('; '.join(feature['failures']))}</td></tr>"
            for feature in candidate["features"].values()
        )
        relation_rows = "".join(
            f"<tr><td>{html.escape(relation['label'])}</td><td>{relation['reference_delta'] if relation['reference_delta'] is not None else '—'}</td>"
            f"<td>{relation['actual_delta'] if relation['actual_delta'] is not None else '—'}</td><td>{relation['error'] if relation['error'] is not None else '—'}</td>"
            f"<td>{_status_cell(relation['passed'])}</td></tr>"
            for relation in candidate["relations"].values()
        )
        color_rows = "".join(
            f"<tr><td>{html.escape(sample['label'])}</td>"
            f"<td>{html.escape(str(sample['reference_rgb']))}</td>"
            f"<td>{html.escape(str(sample['actual_rgb']))}</td>"
            f"<td>{sample['max_channel_delta']:.2f}</td><td>{_status_cell(sample['passed'])}</td></tr>"
            for sample in candidate["colors"].values()
        )
        candidates.append(
            f"<section><h2>{html.escape(candidate_id)} · {_status_cell(candidate['passed'])}</h2>"
            "<div class=\"shots\">"
            f"<figure><img src=\"{html.escape(report['reference_preview'])}\" alt=\"reference\"><figcaption>蓝湖原稿</figcaption></figure>"
            f"<figure><img src=\"{html.escape(candidate['preview'])}\" alt=\"candidate\"><figcaption>候选实现</figcaption></figure>"
            f"<figure><img src=\"{html.escape(candidate['overlay'])}\" alt=\"alignment overlay\"><figcaption>可见像素对齐</figcaption></figure>"
            "</div>"
            "<p class=\"legend\"><span class=\"ref\">原稿可见边界</span> · "
            "<span class=\"actual\">实现可见边界</span></p>"
            "<h3>区域像素门禁</h3><table><tr><th>区域</th><th>MAE</th><th>P95</th><th>结果</th><th>原因</th></tr>"
            f"{region_rows}</table><h3>元素几何门禁</h3>"
            "<table><tr><th>元素</th><th>ΔX</th><th>ΔY</th><th>Δ宽</th><th>Δ高</th><th>结果</th><th>原因</th></tr>"
            f"{feature_rows}</table><h3>组内关系门禁</h3>"
            "<table><tr><th>关系</th><th>原稿差值</th><th>实现差值</th><th>偏差</th><th>结果</th></tr>"
            f"{relation_rows}</table><h3>颜色采样门禁</h3>"
            "<table><tr><th>采样</th><th>原稿 RGB</th><th>实现 RGB</th><th>最大通道偏差</th><th>结果</th></tr>"
            f"{color_rows}</table>{_geometry_html(candidate)}</section>"
        )
    document = f"""<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">
<title>视觉还原门禁报告</title><style>
body{{font:14px/1.5 -apple-system,BlinkMacSystemFont,"PingFang SC",sans-serif;margin:32px;color:#20242a;background:#f5f6f8}}
main{{max-width:1180px;margin:auto}}section{{background:white;border:1px solid #e1e4e8;border-radius:14px;padding:22px;margin:20px 0;overflow:auto}}
table{{border-collapse:collapse;width:100%;min-width:800px}}th,td{{border-bottom:1px solid #eceef1;padding:8px;text-align:left}}img{{width:375px;max-width:100%;border:1px solid #ddd}}
.shots{{display:flex;gap:16px;flex-wrap:wrap}}figure{{margin:0}}figcaption{{color:#686b77;margin-top:6px}}
.ref{{color:#15a46b}}.actual{{color:#e13d8c}}code{{background:#eef0f3;padding:2px 5px;border-radius:4px}}
</style></head><body><main><h1>视觉还原自动门禁</h1>
<p>整体结果：{html.escape(report['status'])}。绿色框为蓝湖原稿可见像素，粉色框为候选渲染可见像素。</p>
<details><summary>验收范围、环境与排除项</summary><pre>{html.escape(json.dumps({key: report.get(key) for key in ('skill_version', 'coverage', 'environment', 'exclusions', 'excluded_fraction')}, ensure_ascii=False, indent=2))}</pre></details>
{''.join(candidates)}</main></body></html>"""
    output.write_text(document, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--candidate", action="append", required=True, help="NAME=PNG")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--diagnostic", action="store_true", help="Measure only; never grants acceptance (exit 2)")
    parser.add_argument("--receipt", action="append", default=[], help="NAME=render-receipt.json")
    args = parser.parse_args()

    contract_path = args.contract.resolve()
    output_root = args.output_dir.resolve()
    if contract_path == output_root or output_root in contract_path.parents:
        raise ValueError("Report directory contains protected inputs; use a separate output directory")
    contract_dir = contract_path.parent
    contract = read_json(contract_path)
    scale = float(contract["render_scale"])
    if not math.isfinite(scale) or scale <= 0:
        raise ValueError("render_scale must be positive and finite")
    reference_path = (contract_dir / contract["reference"]).resolve()
    source_paths = [(contract_dir / item).resolve() for item in contract["source_documents"]]
    _validate_evidence(source_paths, contract)
    nodes = _load_nodes(source_paths)
    coverage = None
    if not args.diagnostic:
        coverage = validate_contract(contract, nodes)
        verify_files(contract, contract_dir)
        verify_fonts(contract, nodes, contract_dir)
    reference_pil = Image.open(reference_path).convert("RGB")
    reference = np.asarray(reference_pil)
    expected_size = tuple(round(value * scale) for value in contract["canvas"])
    if reference_pil.size != expected_size:
        raise ValueError(f"Reference size {reference_pil.size} does not match {expected_size}")

    masks = contract.get("exclude_rects", []) + contract.get("exclude_shapes", [])
    protections = contract.get("protect_regions", [])
    keep = build_keep_mask(contract["canvas"], scale, masks, protections)
    excluded_fraction = 1 - float(keep.mean())
    budget = contract.get("max_excluded_fraction", 0.2)
    if not 0 <= budget < 1 or excluded_fraction > budget:
        raise ValueError("Exclusion mask exceeds declared budget")

    feature_specs: dict[str, dict[str, Any]] = contract.get("features", {})
    reference_features: dict[str, dict[str, Any]] = {}
    resolved_rois: dict[str, list[float]] = {}
    for feature_id, spec in feature_specs.items():
        bounds = _union_bounds(spec["node_ids"], nodes)
        roi = _padded_roi(bounds, spec.get("padding", [0, 0, 0, 0]))
        resolved_rois[feature_id] = roi
        measured = _measure_feature(reference, roi, scale, spec["detector"])
        if measured is None:
            raise ValueError(f"Reference detector found no ink for feature {feature_id}")
        reference_features[feature_id] = measured

    candidates: dict[str, Path] = {}
    for value in args.candidate:
        if "=" not in value:
            parser.error("--candidate must be NAME=PNG")
        name, path = value.split("=", 1)
        if not name or name in candidates:
            raise ValueError("Empty or duplicate candidate name")
        candidates[name] = Path(path).resolve()

    receipts = {}
    for value in args.receipt:
        name, separator, path = value.partition("=")
        if not separator or not name or name in receipts:
            raise ValueError("Receipts must use unique NAME=JSON")
        receipts[name] = Path(path).resolve()
    if not args.diagnostic:
        if set(receipts) != set(candidates):
            raise ValueError("Every candidate needs a matching --receipt NAME=JSON")
        for name, path in candidates.items():
            verify_receipt(receipts[name], path, contract_path, contract)
    protected = {contract_path, reference_path, *source_paths, *candidates.values(), *receipts.values()}
    protected.update((contract_dir / p).resolve() for p in contract.get("pinned_files", {}))
    protected.update((contract_dir / p).resolve() for p in contract.get("implementation_inputs", []))
    output_root = args.output_dir.resolve()
    if any(path == output_root or output_root in path.parents for path in protected):
        raise ValueError("Report directory contains protected inputs; use a separate output directory")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    reference_preview = "reference.png"
    reference_pil.save(args.output_dir / reference_preview)
    report: dict[str, Any] = {
        "contract": str(contract_path),
        "contract_sha256": sha256(contract_path),
        "skill_version": re.search(r'version:\s*"([^"]+)"',
            (Path(__file__).resolve().parents[1] / 'SKILL.md').read_text()).group(1),
        "coverage": coverage,
        "environment": contract.get("environment"),
        "exclusions": masks,
        "mask_protections": protections,
        "excluded_fraction": excluded_fraction,
        "reference": str(reference_path),
        "render_scale": scale,
        "reference_preview": reference_preview,
        "passed": True,
        "candidates": {},
    }
    for candidate_index, (candidate_id, candidate_path) in enumerate(candidates.items(), start=1):
        candidate_pil = Image.open(candidate_path).convert("RGB")
        if candidate_pil.size != reference_pil.size:
            raise ValueError(f"{candidate_id} size {candidate_pil.size} does not match reference")
        candidate = np.asarray(candidate_pil)
        safe_id = str(candidate_index) + "-" + re.sub(r"[^A-Za-z0-9._-]+", "-", candidate_id).strip("-") or f"candidate-{candidate_index}"
        preview_name = f"{safe_id}-candidate.png"
        candidate_pil.save(args.output_dir / preview_name)
        candidate_result: dict[str, Any] = {
            "path": str(candidate_path),
            "preview": preview_name,
            "passed": True,
            "regions": {},
            "features": {},
            "relations": {},
            "colors": {},
        }

        for region_id, spec in contract.get("regions", {}).items():
            # node_ids bind coverage; an explicit ROI narrows pixel measurement.
            # Ignoring rect silently diluted small border/mask errors over a card.
            rect = spec["rect"] if "rect" in spec else _union_bounds(spec["node_ids"], nodes)
            try:
                metrics = (_vector_effect_metric(reference, candidate, rect, scale, keep)
                           if spec.get('comparison_profile') == 'vector_effect'
                           else _region_metric(reference, candidate, rect, scale, keep))
            except ValueError as exc:
                if str(exc) == "Region completely excluded by masks":
                    raise ValueError(f"Region {region_id} completely excluded by masks") from exc
                raise
            failures = []
            if metrics["mae"] > spec["max_mae"]:
                failures.append(f"mae={metrics['mae']:.4f} > {spec['max_mae']:.4f}")
            if "max_p95" in spec and metrics["p95_max_channel"] > spec["max_p95"]:
                failures.append(
                    f"p95={metrics['p95_max_channel']:.2f} > {spec['max_p95']:.2f}"
                )
            passed = not failures
            candidate_result["regions"][region_id] = {
                "label": spec["label"], "rect": rect, "metrics": metrics,
                "passed": passed, "failures": failures,
            }
            if spec.get("blocking", True) and not passed:
                candidate_result["passed"] = False

        measured_features: dict[str, dict[str, Any]] = {}
        for feature_id, spec in feature_specs.items():
            measured = _measure_feature(candidate, resolved_rois[feature_id], scale, spec["detector"])
            if measured is None:
                feature_result = {
                    "label": spec["label"], "passed": False,
                    "metrics": {}, "failures": ["candidate detector found no visible ink"],
                }
            else:
                measured_features[feature_id] = measured
                metrics = _feature_comparison(reference_features[feature_id], measured)
                if 'max_mask_iou_loss' in spec['limits']:
                    metrics['mask_iou_loss'] = _mask_iou_loss(
                        reference, candidate, resolved_rois[feature_id], scale, spec['detector'])
                failures = _check_feature(metrics, spec["limits"])
                feature_result = {
                    "label": spec["label"], "passed": not failures,
                    "metrics": metrics, "failures": failures,
                    "reference": reference_features[feature_id], "actual": measured,
                }
            candidate_result["features"][feature_id] = feature_result
            if spec.get("blocking", True) and not feature_result["passed"]:
                candidate_result["passed"] = False

        for relation_id, spec in contract.get("relations", {}).items():
            first, second = spec["features"]
            if first not in measured_features or second not in measured_features:
                relation_result = {
                    "label": spec["label"], "passed": False,
                    "reference_delta": None, "actual_delta": None,
                    "error": None, "reason": "missing visible feature",
                }
            else:
                metric_key = spec["metric"]
                reference_delta = _metric_value(reference_features[first], metric_key) - _metric_value(reference_features[second], metric_key)
                actual_delta = _metric_value(measured_features[first], metric_key) - _metric_value(measured_features[second], metric_key)
                error = abs(actual_delta - reference_delta)
                relation_result = {
                    "label": spec["label"],
                    "reference_delta": round(reference_delta, 4),
                    "actual_delta": round(actual_delta, 4),
                    "error": round(error, 4),
                    "passed": error <= spec["max_delta"],
                }
            candidate_result["relations"][relation_id] = relation_result
            if spec.get("blocking", True) and not relation_result["passed"]:
                candidate_result["passed"] = False

        for sample_id, spec in contract.get("color_samples", {}).items():
            rect = _color_sample_rect(spec, nodes)
            reference_rgb = _mean_rgb(reference, rect, scale)
            actual_rgb = _mean_rgb(candidate, rect, scale)
            max_delta = max(abs(a - b) for a, b in zip(reference_rgb, actual_rgb))
            passed = max_delta <= spec["max_channel_delta"]
            candidate_result["colors"][sample_id] = {
                "label": spec["label"], "rect": rect,
                "reference_rgb": reference_rgb, "actual_rgb": actual_rgb,
                "max_channel_delta": round(max_delta, 4), "passed": passed,
            }
            if spec.get("blocking", True) and not passed:
                candidate_result["passed"] = False

        if contract.get('geometry_probe') == 'v1':
            probe_file = geometry_path(candidate_path)
            _verify_sidecar(probe_file, receipts.get(candidate_id), args.diagnostic)
            if not probe_file.is_file():
                probe = {'passed': False, 'checked': 0, 'checks': [], 'failures': [{
                    'node_id': None, 'label': 'geometry probe',
                    'failures': [f'missing {probe_file.name}: render with the fidelity harness '
                                 'and key widgets with sourceKey(node_id)']}]}
            else:
                probe = compare_geometry(nodes, contract.get('node_decisions', {}),
                                         json.loads(probe_file.read_text()))
            candidate_result['geometry'] = probe
            if not probe['passed']:
                candidate_result['passed'] = False
        responsive = contract.get('responsive_check')
        if isinstance(responsive, dict):
            variant_file = geometry_path(candidate_path, 'variants')
            _verify_sidecar(variant_file, receipts.get(candidate_id), args.diagnostic)
            if not variant_file.is_file():
                report_r = {'passed': False, 'counts': {}, 'findings': [{
                    'kind': 'missing', 'message': f'missing {variant_file.name}: call '
                    'captureResponsiveVariants in the render test'}]}
            else:
                report_r = responsive_report(
                    nodes, json.loads(variant_file.read_text()), contract['canvas'][0],
                    tuple(responsive.get('blocking', DEFAULT_BLOCKING)),
                    contract.get('node_decisions', {}), responsive.get('devices'))
            candidate_result['responsive'] = report_r
            if not report_r['passed']:
                candidate_result['passed'] = False

        overlay_name = f"{safe_id}-alignment-overlay.png"
        _draw_overlay(
            candidate_pil, reference_features, measured_features, scale,
            args.output_dir / overlay_name,
        )
        candidate_result["overlay"] = overlay_name
        report["candidates"][candidate_id] = candidate_result
        report["passed"] = report["passed"] and candidate_result["passed"]

    if args.diagnostic:
        report["metrics_passed"] = report["passed"]
        report["passed"] = False
        report["status"] = "NOT_EVALUATED"
    elif not report["passed"]:
        report["status"] = "FAIL"
    elif (coverage and coverage["exceptions"]) or masks:
        report["status"] = "PASS_WITH_EXCLUSIONS"
    else:
        report["status"] = "PASS"
    report_path = args.output_dir / "visual-gate-report.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8")
    _write_html(report, args.output_dir / "visual-gate-report.html")
    for candidate_id, result in report["candidates"].items():
        failures = sum(
            not item["passed"]
            for category in ("regions", "features", "relations", "colors")
            for item in result[category].values()
        ) + len(result.get("geometry", {}).get("failures", [])) + (
            0 if result.get("responsive", {}).get("passed", True) else 1)
        print(f"{candidate_id}: {'PASS' if result['passed'] else 'FAIL'} ({failures} failed checks)")
    print(f"JSON: {report_path}")
    print(f"HTML: {args.output_dir / 'visual-gate-report.html'}")
    print(f"Acceptance: {report['status']}")
    return 2 if args.diagnostic else (0 if report["passed"] else 1)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, KeyError, TypeError, IndexError, OSError, ImportError) as error:
        message = {"status": "NOT_EVALUATED", "passed": False, "reason": str(error)}
        if "--output-dir" in sys.argv:
            output = Path(sys.argv[sys.argv.index("--output-dir") + 1])
            if "protected inputs" in str(error):
                print(json.dumps(message, ensure_ascii=False), file=sys.stderr)
                raise SystemExit(2)
            output.mkdir(parents=True, exist_ok=True)
            (output / "visual-gate-report.json").write_text(json.dumps(message, ensure_ascii=False, indent=2))
            (output / "visual-gate-report.html").write_text("<meta charset='utf-8'><h1>NOT_EVALUATED</h1><p>" + html.escape(str(error)) + "</p>")
        print(json.dumps(message, ensure_ascii=False), file=sys.stderr)
        raise SystemExit(2)
