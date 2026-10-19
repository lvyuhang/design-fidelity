"""Pin the Lanhu caller-relationship design and install its verified assets."""

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
sys.path.insert(0, str(SERVER_ROOT))

from lanhu_design.install import install_bundle  # noqa: E402


PROJECT_URL = (
    "https://lanhuapp.com/web/#/item/project/stage?"
    "tid=8d03f00f-c4fc-4fe6-ba4a-e5f7ab5f48b8&"
    "pid=3be04117-73d6-43db-955e-528423563e93"
)
DESIGN_ID = "9f70e167-fbe4-4116-8b6c-143b6cd584a3"
RESOLVED_VERSION = "be8e6f39-d73f-4525-9694-055fc4498343"
EVIDENCE_DIR = ROOT / "design_evidence" / "caller-relationship"
SOURCE_DIR = EVIDENCE_DIR / "source"
ASSET_DIR = ROOT / "flutter_ui_components" / "assets" / "lanhu" / "caller_relationship"
REFERENCE_PATH = EVIDENCE_DIR / "reference.png"
APP_REFERENCE_PATH = (
    ROOT / "flutter_ui_components" / "assets" / "reference" / "caller_relationship.png"
)


def parse_tool_text(result) -> dict:
    for block in result.content:
        if getattr(block, "type", None) == "text":
            return json.loads(block.text)
    raise RuntimeError("Lanhu tool result did not contain JSON text")


def save_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


async def main() -> None:
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    SOURCE_DIR.mkdir(parents=True, exist_ok=True)
    APP_REFERENCE_PATH.parent.mkdir(parents=True, exist_ok=True)

    stderr_path = EVIDENCE_DIR / "resource-client.log"
    with stderr_path.open("w") as errors:
        params = StdioServerParameters(
            command="/bin/bash", args=[str(SERVER_ROOT / "run-local-mcp.sh")]
        )
        async with stdio_client(params, errlog=errors) as (reader, writer):
            async with ClientSession(reader, writer) as session:
                await session.initialize()

                overview_result = await session.call_tool(
                    "lanhu_get_design_overview",
                    {
                        "url": PROJECT_URL,
                        "design_id": DESIGN_ID,
                        "annotate": True,
                        "offset": 0,
                        "limit": 60,
                    },
                )
                overview = parse_tool_text(overview_result)
                if overview.get("status") != "complete":
                    raise RuntimeError(f"overview failed: {overview}")
                if overview.get("resolved_version") != RESOLVED_VERSION:
                    raise RuntimeError("Lanhu resolved version changed while pinning evidence")
                if overview.get("canvas") != {"width": 375, "height": 812}:
                    raise RuntimeError(f"unexpected canvas: {overview.get('canvas')}")
                save_json(SOURCE_DIR / "overview.json", overview)

                snapshot_id = overview["snapshot_id"]
                offset = 0
                page = 1
                total_nodes = 0
                reference_uri = None
                while True:
                    region_result = await session.call_tool(
                        "lanhu_inspect_design_region",
                        {
                            "snapshot_id": snapshot_id,
                            "region": {"x": 0, "y": 0, "width": 375, "height": 812},
                            "annotate": page == 1,
                            "include_hidden": False,
                            "offset": offset,
                            "limit": 60,
                        },
                    )
                    region = parse_tool_text(region_result)
                    if region.get("status") != "complete":
                        raise RuntimeError(f"region page {page} failed: {region}")
                    save_json(SOURCE_DIR / f"source-{page:02d}.json", region)
                    total_nodes += len(region.get("nodes", []))
                    reference_uri = reference_uri or region.get("reference_crop_resource")
                    next_offset = region.get("next_offset")
                    if next_offset is None:
                        break
                    offset = next_offset
                    page += 1

                if total_nodes != overview.get("total_nodes"):
                    raise RuntimeError(
                        f"node coverage mismatch: {total_nodes}/{overview.get('total_nodes')}"
                    )
                if not reference_uri:
                    raise RuntimeError("Lanhu did not provide a reference resource")

                reference_result = await session.read_resource(reference_uri)
                reference_bytes = base64.b64decode(
                    reference_result.contents[0].blob, validate=True
                )
                REFERENCE_PATH.write_bytes(reference_bytes)
                shutil.copyfile(REFERENCE_PATH, APP_REFERENCE_PATH)
                with Image.open(REFERENCE_PATH) as reference_image:
                    if reference_image.size != (750, 1624):
                        raise RuntimeError(
                            f"unexpected reference size: {reference_image.size}"
                        )

                export_result = await session.call_tool(
                    "lanhu_export_design_assets",
                    {
                        "snapshot_id": snapshot_id,
                        "kind": "all",
                        "format_preference": "original",
                        "target_dpr": 2,
                    },
                )
                export_data = parse_tool_text(export_result)
                if export_data.get("status") != "complete":
                    raise RuntimeError(f"asset export failed: {export_data}")
                save_json(EVIDENCE_DIR / "asset-export.json", export_data)

                bundle_result = await session.read_resource(export_data["bundle_resource"])
                bundle_bytes = base64.b64decode(
                    bundle_result.contents[0].blob, validate=True
                )
                bundle_path = EVIDENCE_DIR / "source-assets.zip"
                bundle_path.write_bytes(bundle_bytes)
                install_bundle(bundle_bytes, ASSET_DIR)

                print(
                    json.dumps(
                        {
                            "snapshot_id": snapshot_id,
                            "resolved_version": RESOLVED_VERSION,
                            "nodes": total_nodes,
                            "reference": str(REFERENCE_PATH),
                            "assets": export_data.get("counts"),
                            "asset_dir": str(ASSET_DIR),
                        },
                        ensure_ascii=False,
                    )
                )


if __name__ == "__main__":
    asyncio.run(main())
