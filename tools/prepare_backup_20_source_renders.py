"""Create reproducible source-render fallbacks for unavailable Lanhu bitmaps."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT / "design_evidence" / "backup-20-skill211" / "reference-4x.png"
OUTPUT = ROOT / "flutter_ui_components" / "assets" / "lanhu" / "backup_20_source"
RECEIPT = ROOT / "design_evidence" / "backup-20-skill211" / "source-renders.json"

# Bounds use the verified 375 × 812 design coordinate space. The grid crops
# intentionally stop at native overlays so source-render pixels are not stacked.
CROPS = {
    "status_bar.png": [21, 14, 340, 19],
    "notification_avatar.png": [27, 59, 50, 50],
    "grid_row_1.png": [15, 118, 345.5, 205],
    "grid_row_2.png": [15, 331, 345.5, 225],
    "grid_row_3_top.png": [15, 564, 345.5, 171],
    "bottom_nav.png": [14, 735, 343, 56],
    "bottom_right_sliver.png": [357, 735, 4, 54],
}


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    reference = Image.open(REFERENCE).convert("RGBA")
    if reference.size != (1500, 3248):
        raise RuntimeError(f"Unexpected reference size: {reference.size}")
    records = []
    for name, bounds in CROPS.items():
        x, y, width, height = bounds
        box = tuple(round(value * 4) for value in (x, y, x + width, y + height))
        crop = reference.crop(box)
        path = OUTPUT / name
        crop.save(path)
        records.append(
            {
                "file": str(path.relative_to(ROOT)),
                "bounds": {"x": x, "y": y, "width": width, "height": height},
                "pixels": list(crop.size),
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "source": str(REFERENCE.relative_to(ROOT)),
                "reason": "source bitmap has no exportable asset ID or image-fill URL",
            }
        )
    RECEIPT.write_text(
        json.dumps(
            {
                "status": "complete",
                "design_id": "d5656e3e-51ce-4701-8c18-27d5bd7faa17",
                "snapshot_id": "b9568db973a4df49cceca712e8cda246",
                "resolved_version": "145990dc-069f-4539-9771-3c8dd44ba60c",
                "scale": 4,
                "source_renders": records,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n"
    )
    print(RECEIPT)


if __name__ == "__main__":
    main()
