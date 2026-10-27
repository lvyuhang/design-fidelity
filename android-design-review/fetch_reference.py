"""Read the already-pinned clean MCP tiles; never use the scaled overview preview."""
import os
import asyncio
import base64
import hashlib
import io
import json
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from PIL import Image

ROOT = Path(__file__).resolve().parent / 'evidence/wanqia-feed'
SERVER = os.environ.get('LANHU_MCP_LAUNCHER', str(Path(__file__).resolve().parents[1] / 'integrations' / 'run-lanhu-mcp.sh'))


async def main():
    pages = [json.loads((ROOT / name).read_text()) for name in
             ('overview-1.json', 'overview-2.json', 'region-top.json', 'region-bottom.json', 'region-bottom-2.json')]
    assert len({p['snapshot_id'] for p in pages}) == 1
    assert len({p['resolved_version'] for p in pages}) == 1
    nodes = {n['node_id']: n for p in pages for n in p['nodes']}
    assert len(nodes) == pages[0]['total_nodes'] == 90
    with (ROOT/'resource-client.log').open('w') as log:
        async with stdio_client(StdioServerParameters(command='/bin/bash', args=[SERVER]), errlog=log) as (r, w):
            async with ClientSession(r, w) as session:
                await session.initialize()
                full = Image.new('RGB', (750, 1624))
                for index, page in enumerate(pages[2:4]):
                    result = await session.read_resource(page['reference_crop_resource'])
                    data = base64.b64decode(result.contents[0].blob, validate=True)
                    (ROOT/f'tile-{index}.png').write_bytes(data)
                    image = Image.open(io.BytesIO(data)).convert('RGB')
                    assert image.size == (750, 812)
                    full.paste(image, (0, index*812))
                full.save(ROOT/'reference.png')
    snapshot = {k: pages[0][k] for k in ('snapshot_id','design_id','design_name','resolved_version','canvas',
               'coordinate_space','coordinate_mapping','reference_size','font_requirements','total_nodes','gaps')}
    snapshot['nodes'] = list(nodes.values())
    snapshot['project_name'] = 'v1.6-添加好友'
    snapshot['source_url'] = 'https://lanhuapp.com/web/#/item/project/stage?tid=8d03f00f-c4fc-4fe6-ba4a-e5f7ab5f48b8&pid=42c284fa-dba5-4d44-af54-f22ffc9b9805'
    snapshot['reference_sha256'] = hashlib.sha256((ROOT/'reference.png').read_bytes()).hexdigest()
    (ROOT/'snapshot.json').write_text(json.dumps(snapshot, ensure_ascii=False, indent=2))
    print('Pinned design:', snapshot['design_name'], '90 nodes; original 750 x 1624 reference')


if __name__ == '__main__':
    asyncio.run(main())
