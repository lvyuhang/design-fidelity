"""Fetch immutable references and install verified source assets via MCP."""
import asyncio, base64, io, json, sys
from pathlib import Path
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from PIL import Image
ROOT = Path(__file__).resolve().parents[1]
SERVER_ROOT = Path('/Users/tan/Documents/Codex/2026-10-10/https-github-com-dsphper-lanhu-mcp/lanhu-mcp')
sys.path.insert(0, str(SERVER_ROOT))
from lanhu_design.install import install_bundle

async def main():
    spec = json.loads((ROOT/'design_evidence/requested-resources.json').read_text())
    with (ROOT/'design_evidence/resource-client.log').open('w') as errors:
        async with stdio_client(StdioServerParameters(command='/bin/bash', args=[str(SERVER_ROOT/'run-local-mcp.sh')]), errlog=errors) as (r,w):
            async with ClientSession(r,w) as session:
                await session.initialize()
                async def fetch(uri):
                    result = await session.read_resource(uri)
                    return base64.b64decode(result.contents[0].blob, validate=True)
                for name in ['feed','gender_none','gender_female','comments']:
                    item = spec[name]
                    canvas = Image.new('RGB',(item['region']['width']*4,item['region']['height']*4))
                    for tile in item['tiles']:
                        image = Image.open(io.BytesIO(await fetch(tile['resource']))).convert('RGB')
                        assert image.size == (tile['width']*4, tile['height']*4)
                        canvas.paste(image,(tile['x']*4,tile['y']*4))
                    canvas.save(ROOT/f'design_evidence/reference-{name}-4x.png')
                    canvas.save(ROOT/f'flutter_ui_components/assets/reference/{name}.png')
                    print(name, canvas.size)
                for name,uri in spec['bundles'].items():
                    data = await fetch(uri)
                    (ROOT/f'design_evidence/{name}-assets.zip').write_bytes(data)
                    receipt = install_bundle(data,ROOT/f'flutter_ui_components/assets/lanhu/{name}')
                    print(name, 'bundle installed')

asyncio.run(main())
