"""Fetch immutable Lanhu evidence for the `1备份 20` fidelity test."""
from __future__ import annotations

import asyncio
import base64
import io
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
sys.path.insert(0, str(SERVER_ROOT))

from lanhu_design.install import install_bundle  # noqa: E402

PROJECT_URL = (
    "https://lanhuapp.com/web/#/item/project/stage?"
    "pid=f97b6623-3f77-4d06-87af-dd1d2649d267&"
    "teamId=8d03f00f-c4fc-4fe6-ba4a-e5f7ab5f48b8"
)
DESIGN_ID = "d5656e3e-51ce-4701-8c18-27d5bd7faa17"
VERSION = "145990dc-069f-4539-9771-3c8dd44ba60c"
OUT = ROOT / "design_evidence" / "backup-20-skill211"
SOURCE = OUT / "source"
ASSET_DIR = ROOT / "flutter_ui_components" / "assets" / "lanhu" / "backup_20"
APP_REFERENCE = ROOT / "flutter_ui_components" / "assets" / "reference" / "backup_20.png"


def tool_json(result) -> dict:
    if result.structuredContent:
        return result.structuredContent
    for block in result.content:
        if getattr(block, "type", None) == "text":
            return json.loads(block.text)
    raise RuntimeError("Lanhu tool returned no JSON")


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


async def read_bytes(session: ClientSession, uri: str) -> bytes:
    resource = await session.read_resource(uri)
    return base64.b64decode(resource.contents[0].blob, validate=True)


async def main() -> None:
    SOURCE.mkdir(parents=True, exist_ok=True)
    APP_REFERENCE.parent.mkdir(parents=True, exist_ok=True)
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
                if overview.get("resolved_version") != VERSION:
                    raise RuntimeError("Lanhu version changed while evidence was pinned")
                if overview.get("canvas") != {"width": 375, "height": 812}:
                    raise RuntimeError(f"Unexpected canvas: {overview.get('canvas')}")
                write_json(SOURCE / "overview.json", overview)

                snapshot_id = overview["snapshot_id"]
                offset = 0
                page = 1
                node_count = 0
                asset_ids: set[str] = set()
                while True:
                    region = tool_json(
                        await session.call_tool(
                            "lanhu_inspect_design_region",
                            {
                                "snapshot_id": snapshot_id,
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
                    node_count += len(region.get("nodes", []))
                    asset_ids.update(
                        asset["asset_id"]
                        for asset in region.get("assets", [])
                        if asset.get("asset_id")
                    )
                    if region.get("next_offset") is None:
                        break
                    offset = region["next_offset"]
                    page += 1
                if node_count != overview["total_nodes"]:
                    raise RuntimeError(
                        f"Node coverage {node_count}/{overview['total_nodes']}"
                    )

                native = overview["original_reference_size"]
                canvas = overview["canvas"]
                width, height = int(native["width"]), int(native["height"])
                scale_x = width / canvas["width"]
                scale_y = height / canvas["height"]
                if abs(scale_x - scale_y) >= 0.01:
                    raise RuntimeError("Reference and canvas scale do not match")
                reference = Image.new("RGBA", (width, height))
                tile_index = 0
                for y in range(0, height, 1100):
                    for x in range(0, width, 1100):
                        tile_index += 1
                        tile_width = min(1100, width - x)
                        tile_height = min(1100, height - y)
                        tile = tool_json(
                            await session.call_tool(
                                "lanhu_inspect_design_region",
                                {
                                    "snapshot_id": snapshot_id,
                                    "region": {
                                        "x": x / scale_x,
                                        "y": y / scale_y,
                                        "width": tile_width / scale_x,
                                        "height": tile_height / scale_y,
                                    },
                                    "annotate": False,
                                    "offset": 0,
                                    "limit": 1,
                                },
                            )
                        )
                        image = Image.open(
                            io.BytesIO(
                                await read_bytes(session, tile["reference_crop_resource"])
                            )
                        ).convert("RGBA")
                        if image.size != (tile_width, tile_height):
                            raise RuntimeError(
                                f"Unexpected tile {tile_index} size: {image.size}"
                            )
                        reference.paste(image, (x, y))
                reference_path = OUT / "reference-4x.png"
                reference.save(reference_path)
                shutil.copyfile(reference_path, APP_REFERENCE)

                export = tool_json(
                    await session.call_tool(
                        "lanhu_export_design_assets",
                        {
                            "snapshot_id": snapshot_id,
                            "asset_ids": sorted(asset_ids),
                            "kind": "all",
                            "format_preference": "original",
                            "target_dpr": 4,
                        },
                    )
                )
                if export.get("status") != "complete":
                    raise RuntimeError(export)
                write_json(OUT / "asset-export.json", export)
                bundle_bytes = await read_bytes(session, export["bundle_resource"])
                (OUT / "source-assets.zip").write_bytes(bundle_bytes)
                install_bundle(bundle_bytes, ASSET_DIR)

                summary = {
                    "snapshot_id": snapshot_id,
                    "resolved_version": VERSION,
                    "canvas": canvas,
                    "reference_size": [width, height],
                    "nodes": node_count,
                    "node_pages": page,
                    "selected_asset_ids": len(asset_ids),
                    "asset_export": export.get("counts"),
                    "reference": str(reference_path),
                    "asset_dir": str(ASSET_DIR),
                }
                write_json(OUT / "fetch-summary.json", summary)
                print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    asyncio.run(main())
