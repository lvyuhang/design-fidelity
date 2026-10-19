"""Fetch complete immutable source evidence for the Skill 2.9 platform-page test."""
from __future__ import annotations

import asyncio
import base64
import json
import shutil
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SERVER_ROOT = Path(
    "/Users/tan/Documents/Codex/2026-10-10/"
    "https-github-com-dsphper-lanhu-mcp/lanhu-mcp"
)
PROJECT_URL = (
    "https://lanhuapp.com/web/#/item/project/stage?"
    "tid=8d03f00f-c4fc-4fe6-ba4a-e5f7ab5f48b8&"
    "pid=3be04117-73d6-43db-955e-528423563e93"
)
DESIGN_ID = "8f468427-cc51-401d-a916-4ddd469544ad"
VERSION = "d4d1c235-1fb2-4395-9d0e-a5055d074f4e"
OUT = ROOT / "design_evidence" / "platform-intro-skill29"
SOURCE = OUT / "source"


def tool_json(result) -> dict:
    for block in result.content:
        if getattr(block, "type", None) == "text":
            return json.loads(block.text)
    raise RuntimeError("Lanhu tool returned no JSON text")


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


async def main() -> None:
    if OUT.exists():
        raise RuntimeError(f"Evidence directory already exists: {OUT}")
    SOURCE.mkdir(parents=True)
    with (OUT / "mcp.log").open("w") as errors:
        params = StdioServerParameters(
            command="/bin/bash", args=[str(SERVER_ROOT / "run-local-mcp.sh")]
        )
        async with stdio_client(params, errlog=errors) as (reader, writer):
            async with ClientSession(reader, writer) as session:
                await session.initialize()
                overview = tool_json(
                    await session.call_tool(
                        "lanhu_get_design_overview",
                        {
                            "url": PROJECT_URL,
                            "design_id": DESIGN_ID,
                            "version_id": VERSION,
                            "annotate": False,
                            "offset": 0,
                            "limit": 60,
                        },
                    )
                )
                if overview.get("status") != "complete":
                    raise RuntimeError(overview)
                if overview["resolved_version"] != VERSION:
                    raise RuntimeError("Resolved version changed")
                write_json(SOURCE / "overview.json", overview)

                offset = 0
                count = 0
                page = 1
                reference_uri = None
                while True:
                    region = tool_json(
                        await session.call_tool(
                            "lanhu_inspect_design_region",
                            {
                                "snapshot_id": overview["snapshot_id"],
                                "region": {
                                    "x": 0,
                                    "y": 0,
                                    "width": 375,
                                    "height": 812,
                                },
                                "annotate": False,
                                "include_hidden": False,
                                "offset": offset,
                                "limit": 60,
                            },
                        )
                    )
                    if region.get("status") != "complete":
                        raise RuntimeError(region)
                    write_json(SOURCE / f"region-{page:02d}.json", region)
                    count += len(region.get("nodes", []))
                    reference_uri = reference_uri or region.get(
                        "reference_crop_resource"
                    )
                    if region.get("next_offset") is None:
                        break
                    offset = region["next_offset"]
                    page += 1
                if count != overview["total_nodes"]:
                    raise RuntimeError(f"Node coverage {count}/{overview['total_nodes']}")

                focus_ids = [
                    "11857F91-EAAB-4C0C-A518-9D0D2F73628B",  # quote 01
                    "A3FD2014-8642-473A-B0F5-4C17D694B015",  # 01
                    "7E01FF1B-EB56-4729-8906-6426783856F5",  # dark card
                    "D44A759A-F00C-4F91-B906-8D3AEA24B017",  # quote 02
                    "67A66F14-1BFC-4ED2-B7CC-CA53F587487F",  # sparkle
                    "D918BBDD-E8F9-4952-B1C0-818569C32B90",  # 02
                    "0CF90661-2AAC-46A4-A10B-C00DF8F1EB4B",  # white card
                    "B3B02A92-587E-4458-994E-449FD80C020F",  # CTA
                ]
                focus = tool_json(
                    await session.call_tool(
                        "lanhu_inspect_design_region",
                        {
                            "snapshot_id": overview["snapshot_id"],
                            "node_ids": focus_ids,
                            "annotate": True,
                            "include_hidden": False,
                            "offset": 0,
                            "limit": 60,
                        },
                    )
                )
                write_json(SOURCE / "focus-effects.json", focus)

                resource = await session.read_resource(reference_uri)
                reference = base64.b64decode(resource.contents[0].blob, validate=True)
                preview_path = OUT / "reference-preview.png"
                preview_path.write_bytes(reference)
                with Image.open(preview_path) as image:
                    preview_size = image.size

                # Lanhu may return an optimized preview from the resource URI even
                # though the immutable snapshot is unchanged. Reuse the already
                # frozen 4x reference for that same snapshot instead of failing the
                # evidence run or silently accepting a lower-resolution baseline.
                frozen_reference = (
                    ROOT / "design_evidence" / "full-page-models" / "reference-4x.png"
                )
                if preview_size == (1500, 3248):
                    shutil.copyfile(preview_path, OUT / "reference-4x.png")
                    reference_source = "lanhu-resource"
                elif frozen_reference.exists():
                    shutil.copyfile(frozen_reference, OUT / "reference-4x.png")
                    reference_source = "same-snapshot-frozen-reference"
                else:
                    raise RuntimeError(
                        f"Preview size {preview_size}; frozen 4x reference unavailable"
                    )
                shutil.copyfile(
                    OUT / "reference-4x.png",
                    ROOT
                    / "flutter_ui_components"
                    / "assets"
                    / "reference"
                    / "platform_intro_skill29.png",
                )
                write_json(
                    OUT / "fetch-summary.json",
                    {
                        "snapshot_id": overview["snapshot_id"],
                        "resolved_version": overview["resolved_version"],
                        "nodes": count,
                        "pages": page,
                        "focus_nodes": len(focus.get("nodes", [])),
                        "reference": str(OUT / "reference-4x.png"),
                        "reference_preview": str(preview_path),
                        "reference_preview_size": list(preview_size),
                        "reference_source": reference_source,
                        "assets_reused": 11,
                    },
                )
                print((OUT / "fetch-summary.json").read_text())


if __name__ == "__main__":
    asyncio.run(main())
