"""Evaluate frozen GPT-5.6 Sol first renders against source and prior GPT-6 work."""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "design_evidence"
OUT = EVIDENCE / "components-sol56"
ASSETS = ROOT / "flutter_ui_components/assets/experiments/components-sol56"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


FREEZES = {
    "social": (
        ROOT / "flutter_ui_components/lib/experiments/social_sol56.dart",
        OUT / "social_sol56.frozen.dart",
        OUT / "social-freeze.json",
    ),
    "utility": (
        ROOT / "flutter_ui_components/lib/experiments/utility_sol56.dart",
        OUT / "utility_sol56.frozen.dart",
        OUT / "utility-freeze.json",
    ),
    "login": (
        ROOT / "flutter_ui_components/lib/experiments/login_sol56.dart",
        OUT / "login_sol56.frozen.dart",
        OUT / "login-freeze.json",
    ),
}

for name, (source, frozen, manifest_path) in FREEZES.items():
    manifest = json.loads(manifest_path.read_text())
    implementation_entry = manifest.get("implementation")
    source_entry = manifest.get("source")
    expected = (
        (implementation_entry.get("sha256") if isinstance(implementation_entry, dict) else None)
        or (source_entry.get("sha256") if isinstance(source_entry, dict) else None)
        or manifest.get("source_sha256")
    )
    assert sha(source) == expected, f"{name} implementation changed after freeze"
    assert sha(frozen) == expected, f"{name} frozen copy differs"

SAMPLES = {
    "feed": {
        "reference": EVIDENCE / "reference-feed-stage-4x.png",
        "size": (375, 342),
        "exclusions": [(96.75, 12, 181.5, 242), (103.75, 305, 15, 15)],
        "regions": {
            "independent": (0, 0, 375, 342),
            "caption": (104.75, 260, 165.5, 36),
            "footer": (104, 303, 173, 20),
        },
        "resource_gap": "照片和头像来自同一份蓝湖预览裁切；independent 指标排除这些区域。",
    },
    "comments": {
        "reference": EVIDENCE / "reference-comments-4x.png",
        "size": (375, 374),
        "exclusions": [(16, 47, 30, 30), (16, 147, 30, 30), (53, 232, 24, 24)],
        "regions": {
            "independent": (0, 0, 375, 374),
            "title": (17, 9, 100, 22),
            "first_comment": (52, 47, 230, 70),
            "nested_reply": (85, 233, 240, 86),
        },
        "resource_gap": "三个头像来自同一份蓝湖预览裁切；independent 指标排除这些区域。",
    },
    "modal": {
        "reference": EVIDENCE / "reference-modal-4x.png",
        "size": (375, 280),
        "exclusions": [],
        "regions": {
            "whole": (0, 0, 375, 280),
            "dialog": (23, 22, 330, 228),
            "buttons": (42, 178, 291, 47),
        },
    },
    "nav": {
        "reference": EVIDENCE / "reference-nav-4x.png",
        "size": (375, 98),
        "exclusions": [],
        "regions": {
            "whole": (0, 0, 375, 98),
            "bar": (14, 21, 347, 56),
            "icons_labels": (25, 28, 320, 43),
        },
        "resource_gap": "消息图标缺少原始路径，5.6 与此前 GPT-6 均为近似绘制。",
    },
    "appeal": {
        "reference": EVIDENCE / "reference-appeal-4x.png",
        "size": (375, 125),
        "exclusions": [],
        "regions": {
            "whole": (0, 0, 375, 125),
            "card": (16, 4, 343, 116),
            "button": (287, 78, 56, 28),
        },
    },
    "login": {
        "reference": EVIDENCE / "reference-region.png",
        "size": (375, 395),
        "exclusions": [],
        "regions": {
            "whole": (0, 0, 375, 395),
            "buttons": (24, 4, 327, 278),
            "agreement": (20, 340, 335, 52),
        },
        "reference_note": "蓝湖区域导出为 1329×1400；仅为对齐 375×395 逻辑网格重采样到 1500×1580。",
    },
}


def rect4(rect: tuple[float, float, float, float]) -> tuple[int, int, int, int]:
    x, y, width, height = rect
    return tuple(round(value * 4) for value in (x, y, x + width, y + height))


def metric(a: np.ndarray, b: np.ndarray, mask: np.ndarray | None = None) -> dict:
    delta = np.abs(a.astype(np.float64) - b.astype(np.float64))
    values = delta if mask is None else delta[mask]
    max_channel = values.max(axis=-1)
    return {
        "pixels": int(max_channel.size),
        "mean_abs_rgb_0_255": round(float(values.mean()), 4),
        "p95_max_channel_abs": round(float(np.percentile(max_channel, 95)), 4),
    }


def open_on_white(path: Path) -> Image.Image:
    image = Image.open(path).convert("RGBA")
    background = Image.new("RGBA", image.size, "white")
    return Image.alpha_composite(background, image).convert("RGB")


ASSETS.mkdir(parents=True, exist_ok=True)
report = {
    "method": (
        "Source-aligned 4× RGB absolute error. GPT-5.6 Sol files were isolated, "
        "frozen before first render, and received zero visual correction. The GPT-6 "
        "column is the previously reviewed/current implementation, so this is an "
        "implementation comparison rather than a controlled model leaderboard. "
        "Flutter debug overflow indicators produced by undersized fixed text boxes "
        "remain in the 4x raster and are intentionally counted; Web release hides "
        "the diagnostic stripes but retains the underlying constraint risk."
    ),
    "models": {
        "sol56": {
            "model": "gpt-5.6-sol",
            "reasoning_effort": "high",
            "visual_revision_count": 0,
        },
        "gpt6": {"label": "此前 GPT-6 已核对实现"},
    },
    "freeze_sha256": {
        name: sha(paths[0]) for name, paths in FREEZES.items()
    },
    "samples": {},
}

contact_rows: list[Image.Image] = []
for sample, spec in SAMPLES.items():
    expected_size = (spec["size"][0] * 4, spec["size"][1] * 4)
    reference = open_on_white(spec["reference"])
    if reference.size != expected_size:
        reference = reference.resize(expected_size, Image.Resampling.LANCZOS)
    variants = {
        "sol56": open_on_white(OUT / f"{sample}-sol56-4x.png"),
        "gpt6": open_on_white(OUT / f"{sample}-gpt6-4x.png"),
    }
    assert all(image.size == expected_size for image in variants.values())
    source_array = np.array(reference)
    independent_mask = np.ones(source_array.shape[:2], dtype=bool)
    for exclusion in spec["exclusions"]:
        x1, y1, x2, y2 = rect4(exclusion)
        independent_mask[y1:y2, x1:x2] = False

    sample_report = {
        "logical_size": list(spec["size"]),
        "reference_sha256": sha(spec["reference"]),
        "exclusions": spec["exclusions"],
        "regions": {},
    }
    for optional in ("resource_gap", "reference_note"):
        if optional in spec:
            sample_report[optional] = spec[optional]

    for region_name, region in spec["regions"].items():
        x1, y1, x2, y2 = rect4(region)
        region_mask = independent_mask[y1:y2, x1:x2]
        sample_report["regions"][region_name] = {
            variant: metric(
                source_array[y1:y2, x1:x2],
                np.array(image)[y1:y2, x1:x2],
                region_mask,
            )
            for variant, image in variants.items()
        }
        sample_report["regions"][region_name]["rect"] = list(region)
    report["samples"][sample] = sample_report

    asset_reference = ASSETS / f"{sample}-reference.png"
    reference.save(asset_reference)
    for variant, image in variants.items():
        image.save(ASSETS / f"{sample}-{variant}.png")

    logical_height = spec["size"][1]
    row = Image.new("RGB", (1157, logical_height + 34), "#F2F3F5")
    draw = ImageDraw.Draw(row)
    for index, (label, image) in enumerate(
        [("LANHU SOURCE", reference), ("GPT-5.6 SOL HIGH", variants["sol56"]), ("PREVIOUS GPT-6", variants["gpt6"])]
    ):
        x = index * 391
        draw.text((x + 8, 9), f"{sample.upper()} / {label}", fill="#22242A")
        row.paste(image.resize(spec["size"], Image.Resampling.LANCZOS), (x, 34))
    contact_rows.append(row)

(OUT / "evaluation.json").write_text(
    json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
)
shutil.copy2(OUT / "evaluation.json", ASSETS / "evaluation.json")

sheet = Image.new(
    "RGB",
    (1157, sum(row.height for row in contact_rows)),
    "#F2F3F5",
)
y = 0
for row in contact_rows:
    sheet.paste(row, (0, y))
    y += row.height
sheet.save(OUT / "source-sol56-gpt6.png")

print(json.dumps(report, ensure_ascii=False, indent=2))
