"""Fetch a complete, pinned Lanhu page evidence bundle.

The command is page-agnostic so repeated fidelity tests do not require editing a
Python fetcher for every artboard.
"""
from __future__ import annotations

import argparse
import asyncio
import base64
import io
import json
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SERVER_ROOT = Path(
    "/Users/tan/Documents/Codex/2026-10-10/"
    "https-github-com-dsphper-lanhu-mcp/lanhu-mcp"
)


def arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", required=True)
    parser.add_argument("--design-id", required=True)
    parser.add_argument("--version", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--expected-width", type=int, default=375)
    parser.add_argument("--expected-height", type=int, default=812)
    parser.add_argument("--tile-size", type=int, default=1100)
    return parser.parse_args()


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


async def fetch(args: argparse.Namespace) -> dict:
    output = args.output.resolve()
    source = output / "source"
    bundle_dir = output / "source-bundle"
    source.mkdir(parents=True, exist_ok=True)
    with (output / "mcp.log").open("w") as errors:
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
                            "url": args.url,
                            "design_id": args.design_id,
                            "version_id": args.version,
                            "annotate": False,
                            "offset": 0,
                            "limit": 60,
                        },
                    )
                )
                if overview.get("status") != "complete":
                    raise RuntimeError(overview)
                if overview.get("resolved_version") != args.version:
                    raise RuntimeError("Lanhu version changed while evidence was pinned")
                expected = {"width": args.expected_width, "height": args.expected_height}
                if overview.get("canvas") != expected:
                    raise RuntimeError(f"Unexpected canvas: {overview.get('canvas')}")
                write_json(source / "overview.json", overview)

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
                                "region": {"x": 0, "y": 0, **expected},
                                "annotate": False,
                                "include_hidden": False,
                                "offset": offset,
                                "limit": 60,
                            },
                        )
                    )
                    if region.get("status") != "complete":
                        raise RuntimeError(region)
                    write_json(source / f"region-{page:02d}.json", region)
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
                    raise RuntimeError(f"Node coverage {node_count}/{overview['total_nodes']}")

                native = overview["original_reference_size"]
                width, height = int(native["width"]), int(native["height"])
                scale_x = width / args.expected_width
                scale_y = height / args.expected_height
                if abs(scale_x - scale_y) >= 0.01:
                    raise RuntimeError("Reference and canvas scale do not match")
                reference = Image.new("RGBA", (width, height))
                for y in range(0, height, args.tile_size):
                    for x in range(0, width, args.tile_size):
                        tile_width = min(args.tile_size, width - x)
                        tile_height = min(args.tile_size, height - y)
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
                            io.BytesIO(await read_bytes(session, tile["reference_crop_resource"]))
                        ).convert("RGBA")
                        if image.size != (tile_width, tile_height):
                            raise RuntimeError(f"Unexpected reference tile size: {image.size}")
                        reference.paste(image, (x, y))
                reference_path = output / "reference-4x.png"
                reference.save(reference_path)

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
                write_json(output / "asset-export.json", export)
                bundle_bytes = await read_bytes(session, export["bundle_resource"])
                (output / "source-assets.zip").write_bytes(bundle_bytes)

                # Import lazily so --help remains usable even if the local MCP
                # checkout is temporarily unavailable.
                import sys

                sys.path.insert(0, str(SERVER_ROOT))
                from lanhu_design.install import install_bundle

                install_bundle(bundle_bytes, bundle_dir)
                summary = {
                    "snapshot_id": snapshot_id,
                    "resolved_version": args.version,
                    "canvas": expected,
                    "reference_size": [width, height],
                    "nodes": node_count,
                    "node_pages": page,
                    "selected_asset_ids": len(asset_ids),
                    "asset_export": export.get("counts"),
                    "reference": str(reference_path),
                    "bundle": str(bundle_dir),
                }
                write_json(output / "fetch-summary.json", summary)
                return summary


async def main() -> None:
    print(json.dumps(await fetch(arguments()), ensure_ascii=False))


if __name__ == "__main__":
    asyncio.run(main())
