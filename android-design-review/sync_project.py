"""Materialize this project's pinned MCP snapshots and native-resolution references.

Run with the existing Lanhu MCP Python environment (mcp + Pillow installed).
No credentials are copied; the configured stdio launcher owns authentication.
"""
import asyncio
import base64
import hashlib
import json
import os
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from PIL import Image

ROOT = Path(__file__).resolve().parent
EVIDENCE = ROOT/'evidence/project'
SERVER = os.environ.get('LANHU_MCP_LAUNCHER', '/Users/tan/Documents/Codex/2026-10-10/https-github-com-dsphper-lanhu-mcp/lanhu-mcp/run-local-mcp.sh')
URL = 'https://lanhuapp.com/web/#/item/project/stage?tid=8d03f00f-c4fc-4fe6-ba4a-e5f7ab5f48b8&pid=42c284fa-dba5-4d44-af54-f22ffc9b9805'


def save(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data,ensure_ascii=False,indent=2))


async def call(session, tool, args, path):
    if path.exists():
        return json.loads(path.read_text())
    response = await session.call_tool(tool, args)
    data = response.structuredContent or json.loads(next(c.text for c in response.content if c.type=='text'))
    save(path,data)
    return data


async def fetch_design(session, entry, project, semaphore):
    async with semaphore:
        key=entry['id'];folder=EVIDENCE/key
        # Reuse the earlier immutable snapshot, already associated with saved records.
        if key=='7ea1b1bd-25d5-4adb-86ad-df2ef6c8dc5e':
            return {**entry,'kind':'design','design_key':'wanqia-feed','evidence':'evidence/wanqia-feed'}
        first=await call(session,'lanhu_get_design_overview',{'url':URL,'design_id':key,'annotate':False,'limit':60},folder/'overview-0.json')
        if first.get('status')=='error':
            # A text-only entry is shown as source text, never synthesized into a design.
            if not entry.get('url') and first.get('code')=='SourceUnavailable':
                return {**entry,'kind':'note','design_key':'note-'+key,'body':entry['name'],'source_error':first}
            raise ValueError(entry['name']+': '+first.get('message','MCP source unavailable'))
        sid,version=first['snapshot_id'],first['resolved_version']
        nodes={n['node_id']:n for n in first['nodes']};offset=first.get('next_offset')
        while offset is not None:
            page=await call(session,'lanhu_get_design_overview',{'url':URL,'design_id':key,'version_id':version,'annotate':False,'limit':60,'offset':offset},folder/f'overview-{offset}.json')
            assert page['snapshot_id']==sid and page['resolved_version']==version
            nodes.update((n['node_id'],n) for n in page['nodes'])
            next_offset=page.get('next_offset')
            if next_offset is not None and next_offset<=offset:raise ValueError('Non-advancing node pagination')
            offset=next_offset
        assert len(nodes)==first['total_nodes'], 'Incomplete node coverage'
        canvas=first['canvas'];native=first['original_reference_size']
        width,height=int(native['width']),int(native['height'])
        sx,sy=width/canvas['width'],height/canvas['height']
        assert abs(sx-sy)<.01 and first['coordinate_mapping']['verified']
        reference=Image.new('RGBA',(width,height))
        for y in range(0,height,1100):
            for x in range(0,width,1100):
                tw,th=min(1100,width-x),min(1100,height-y)
                region={'x':x/sx,'y':y/sy,'width':tw/sx,'height':th/sy}
                tile=await call(session,'lanhu_inspect_design_region',{'snapshot_id':sid,'region':region,'annotate':False,'limit':1},folder/f'tile-{x}-{y}.json')
                assert tile['snapshot_id']==sid and tile['resolved_version']==version
                path=folder/f'tile-{x}-{y}.png'
                if not path.exists():
                    result=await session.read_resource(tile['reference_crop_resource'])
                    path.write_bytes(base64.b64decode(result.contents[0].blob,validate=True))
                image=Image.open(path).convert('RGBA')
                assert image.size==(tw,th), f'Unexpected crop size: {image.size} vs {(tw,th)}'
                reference.paste(image,(x,y))
        reference.save(folder/'reference.png')
        snapshot={k:first[k] for k in ('snapshot_id','design_id','design_name','resolved_version','canvas','coordinate_space','coordinate_mapping','reference_size','font_requirements','total_nodes','gaps')}
        snapshot.update({'nodes':list(nodes.values()),'project_name':project['project_name'],'source_url':URL,
                         'reference_sha256':hashlib.sha256((folder/'reference.png').read_bytes()).hexdigest()})
        save(folder/'snapshot.json',snapshot)
        print(json.dumps({'name':entry['name'],'nodes':len(nodes),'reference':[width,height]},ensure_ascii=False),flush=True)
        return {**entry,'kind':'design','design_key':'lanhu-'+key,'evidence':str(folder.relative_to(ROOT))}


async def main():
    project=json.loads((EVIDENCE/'designs.json').read_text())
    with (EVIDENCE/'sync.log').open('w') as log:
        async with stdio_client(StdioServerParameters(command='/bin/bash',args=[SERVER]),errlog=log) as (reader,writer):
            async with ClientSession(reader,writer) as session:
                await session.initialize()
                semaphore=asyncio.Semaphore(3)
                results=await asyncio.gather(*(fetch_design(session,entry,project,semaphore) for entry in project['designs']),return_exceptions=True)
    items=[]
    for entry,result in zip(project['designs'],results):
        if isinstance(result,Exception):
            print('FAILED '+entry['name']+': '+str(result),flush=True)
            items.append({**entry,'kind':'unavailable','design_key':'unavailable-'+entry['id'],'error':str(result)})
        else:items.append(result)
    save(EVIDENCE/'catalog.json',{'project_name':project['project_name'],'source_url':URL,'total_designs':project['total_designs'],'items':items})
    print('Catalog complete:',len(items),'items;',sum(x['kind']=='unavailable' for x in items),'failures',flush=True)


if __name__=='__main__':asyncio.run(main())
