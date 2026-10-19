"""Measure two frozen first-pass full-page implementations against Lanhu."""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "design_evidence/full-page-models"
PROJECT = ROOT / "flutter_ui_components"
ASSETS = PROJECT / "assets/lanhu/full_page"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


sources = {
    "sol56": PROJECT / "lib/experiments/full_page_sol56.dart",
    "gpt6": PROJECT / "lib/experiments/full_page_gpt6.dart",
    "sol56_r1": PROJECT / "lib/experiments/full_page_sol56_r1.dart",
    "gpt6_r1": PROJECT / "lib/experiments/full_page_gpt6_r1.dart",
    "sol56_r2": PROJECT / "lib/experiments/full_page_sol56_r2.dart",
    "gpt6_r2": PROJECT / "lib/experiments/full_page_gpt6_r2.dart",
}
frozen = {
    "sol56": OUT / "sol56-frozen.dart",
    "gpt6": OUT / "gpt6-frozen.dart",
    "sol56_r1": OUT / "sol56-r1-frozen.dart",
    "gpt6_r1": OUT / "gpt6-r1-frozen.dart",
    "sol56_r2": OUT / "sol56-r2-frozen.dart",
    "gpt6_r2": OUT / "gpt6-r2-frozen.dart",
}
for model in sources:
    assert sha(sources[model]) == sha(frozen[model]), f"{model} changed after freeze"

reference = Image.open(OUT / "reference-4x.png").convert("RGB")
render_files = {
    "sol56": "sol56-4x.png",
    "gpt6": "gpt6-4x.png",
    "sol56_r1": "sol56-r1-4x.png",
    "gpt6_r1": "gpt6-r1-4x.png",
    "sol56_r2": "sol56-r2-4x.png",
    "gpt6_r2": "gpt6-r2-4x.png",
}
renders = {
    model: Image.open(OUT / render_files[model]).convert("RGB")
    for model in sources
}
assert reference.size == (1500, 3248)
assert all(image.size == reference.size for image in renders.values())

asset_rects = [
    (0, 0, 375, 229),
    (19, 57.183, 205, 118.817),
    (26, 218, 34, 34),
    (36, 281, 30, 30),
    (199, 281, 30, 30),
    (36, 355, 30, 30),
    (199, 355, 30, 30),
    (26, 433, 34, 34),
    (35, 486, 43, 43),
    (35, 558, 43, 43),
    (35, 625, 43, 43),
]

regions = {
    "whole": {"label": "完整页面", "rect": (0, 0, 375, 812), "mask_assets": False},
    "native": {"label": "排除原始切图后的原生结构", "rect": (0, 0, 375, 812), "mask_assets": True},
    "hero": {"label": "状态栏与首屏视觉", "rect": (0, 0, 375, 208), "mask_assets": False},
    "capabilities": {"label": "平台能力", "rect": (15, 208, 343, 208), "mask_assets": False},
    "benefits": {"label": "创作者收益", "rect": (16, 424, 343, 266), "mask_assets": False},
    "cta": {"label": "底部按钮", "rect": (16, 714, 343, 50), "mask_assets": False},
}

source_array = np.asarray(reference, dtype=np.float64)
native_mask = np.ones(source_array.shape[:2], dtype=bool)
for x, y, width, height in asset_rects:
    x1, y1 = round(x * 4), round(y * 4)
    x2, y2 = round((x + width) * 4), round((y + height) * 4)
    native_mask[y1:y2, x1:x2] = False


def metric(delta: np.ndarray, mask: np.ndarray) -> dict[str, float | int]:
    values = delta[mask]
    max_channel = values.max(axis=-1)
    return {
        "pixels": int(max_channel.size),
        "mean_abs_rgb_0_255": round(float(values.mean()), 4),
        "p95_max_channel_abs": round(float(np.percentile(max_channel, 95)), 4),
    }


report = {
    "method": (
        "Source-aligned 4x RGB absolute error without alignment or resizing. Both "
        "R0 implementations were isolated and frozen before first render. Each R1 "
        "implementation received exactly one visual correction round using only its "
        "own R0 render, heatmap and the Lanhu source, then was frozen before R1 render. "
        "R2 applies the shared source-node visual contract, restores verified font coverage, "
        "and calibrates visible-pixel geometry before its final freeze. "
        "Native masks the bounding rectangles of all shared "
        "Lanhu raster assets. MAE is a 0-255 error value, not a fidelity percentage."
    ),
    "snapshot_id": "da6dd92db9b6df7fc3fc4d2bc873e0ee",
    "resolved_version": "d4d1c235-1fb2-4395-9d0e-a5055d074f4e",
    "models": {
        "sol56": {"model": "gpt-5.6-sol", "reasoning_effort": "high", "visual_revision_count": 0},
        "gpt6": {"model": "gpt-6-sol", "reasoning_effort": "high", "visual_revision_count": 0},
        "sol56_r1": {"model": "gpt-5.6-sol", "reasoning_effort": "high", "visual_revision_count": 1},
        "gpt6_r1": {"model": "gpt-6-sol", "reasoning_effort": "high", "visual_revision_count": 1},
        "sol56_r2": {"model": "gpt-5.6-sol", "reasoning_effort": "high", "visual_revision_count": 2},
        "gpt6_r2": {"model": "gpt-6-sol", "reasoning_effort": "high", "visual_revision_count": 2},
    },
    "source_sha256": sha(OUT / "reference-4x.png"),
    "code_sha256": {model: sha(path) for model, path in sources.items()},
    "render_sha256": {model: sha(OUT / render_files[model]) for model in sources},
    "asset_exclusion_rects": asset_rects,
    "regions": {},
}

for key, spec in regions.items():
    x, y, width, height = spec["rect"]
    x1, y1 = round(x * 4), round(y * 4)
    x2, y2 = round((x + width) * 4), round((y + height) * 4)
    mask = (
        native_mask[y1:y2, x1:x2]
        if spec["mask_assets"]
        else np.ones((y2 - y1, x2 - x1), dtype=bool)
    )
    item = {"label": spec["label"], "rect": [x, y, width, height]}
    for model, image in renders.items():
        delta = np.abs(source_array[y1:y2, x1:x2] - np.asarray(image, dtype=np.float64)[y1:y2, x1:x2])
        item[model] = metric(delta, mask)
    report["regions"][key] = item

for model, image in renders.items():
    delta = np.abs(source_array - np.asarray(image, dtype=np.float64))
    heat = np.zeros(source_array.shape, dtype=np.uint8)
    heat[:, :, 0] = np.clip(delta.max(axis=2) * 4, 0, 255).astype(np.uint8)
    Image.fromarray(heat).save(OUT / render_files[model].replace("-4x.png", "-heat-4x.png"))

report["round_improvement"] = {}
for model in ("sol56", "gpt6"):
    revised = f"{model}_r2"
    report["round_improvement"][model] = {
        region: round(
            report["regions"][region][revised]["mean_abs_rgb_0_255"]
            - report["regions"][region][model]["mean_abs_rgb_0_255"],
            4,
        )
        for region in regions
    }


def contact_sheet(columns: list[tuple[str, Image.Image]], filename: str) -> None:
    panel = Image.new("RGB", (len(columns) * 391 - 16, 846), "#F2F3F5")
    draw = ImageDraw.Draw(panel)
    for index, (label, image) in enumerate(columns):
        x = index * 391
        draw.text((x + 8, 8), label, fill="#22242A")
        panel.paste(image.resize((375, 812), Image.Resampling.LANCZOS), (x, 34))
    panel.save(OUT / filename)


contact_sheet(
    [
        ("LANHU SOURCE", reference),
        ("GPT-5.6 SOL R1", renders["sol56_r1"]),
        ("GPT-6 R1", renders["gpt6_r1"]),
    ],
    "source-sol56-r1-gpt6-r1.png",
)
contact_sheet(
    [
        ("LANHU SOURCE", reference),
        ("GPT-5.6 SOL R0", renders["sol56"]),
        ("GPT-5.6 SOL R1", renders["sol56_r1"]),
        ("GPT-6 R0", renders["gpt6"]),
        ("GPT-6 R1", renders["gpt6_r1"]),
    ],
    "source-all-rounds.png",
)
contact_sheet(
    [
        ("LANHU SOURCE", reference),
        ("GPT-5.6 SOL R2", renders["sol56_r2"]),
        ("GPT-6 R2", renders["gpt6_r2"]),
    ],
    "source-sol56-r2-gpt6-r2.png",
)

(OUT / "evaluation.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
shutil.copy2(OUT / "evaluation.json", ASSETS / "evaluation.json")
print(json.dumps(report, ensure_ascii=False, indent=2))
