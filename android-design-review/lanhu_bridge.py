"""Read a Lanhu project through the configured MCP stdio server.

This process runs with the Lanhu MCP virtualenv. It writes only to the output
directory supplied by the local review server and never persists credentials.
"""
import argparse
import asyncio
import base64
import io
import json
import os
import re
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from PIL import Image
from catalog_rules import is_screen

LAUNCHER = os.environ.get(
    'LANHU_MCP_LAUNCHER',
    '/Users/tan/Documents/Codex/2026-10-10/https-github-com-dsphper-lanhu-mcp/lanhu-mcp/run-local-mcp.sh',
)


def response_data(response):
    if response.structuredContent:
        return response.structuredContent
    for content in response.content:
        if getattr(content, 'type', None) == 'text':
            return json.loads(content.text)
    raise ValueError('蓝湖 MCP 没有返回可读取的数据')


async def call(session, tool, arguments):
    result = response_data(await session.call_tool(tool, arguments))
    if isinstance(result, dict) and result.get('status') == 'error':
        raise ValueError(result.get('message') or result.get('code') or '蓝湖 MCP 请求失败')
    return result


async def resolve_url(session, url):
    if 'pid=' in url:
        return url
    resolved = await call(session, 'lanhu_resolve_invite_link', {'invite_url': url})
    for key in ('resolved_url', 'url', 'project_url'):
        value = resolved.get(key)
        if isinstance(value, str) and 'pid=' in value:
            return value
    raise ValueError('邀请链接没有解析出蓝湖项目地址')


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + '.tmp')
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False))
    temp.replace(path)


def report_progress(output, **values):
    if output:
        write_json(output / 'progress.json', values)


async def fetch_design(session, project_url, project, entry, output, progress=None):
    design_id = str(entry.get('id', ''))
    if not re.fullmatch(r'[a-zA-Z0-9_-]{1,80}', design_id):
        raise ValueError('蓝湖设计 ID 无效')
    folder = output / design_id
    cached_snapshot, cached_reference = folder / 'snapshot.json', folder / 'reference.png'
    if cached_snapshot.is_file() and cached_reference.is_file():
        cached = json.loads(cached_snapshot.read_text())
        if (cached.get('design_id') == design_id and cached.get('source_url') == project_url
                and len(cached.get('nodes', [])) == cached.get('total_nodes')):
            with Image.open(cached_reference) as image:image.verify()
            return {**entry, 'kind': 'design', 'bundle': design_id,
                    'resolved_version': cached['resolved_version'], 'snapshot_id': cached['snapshot_id']}
    if progress:progress('读取设计节点')
    try:
        first = await call(session, 'lanhu_get_design_overview', {
            'url': project_url, 'design_id': design_id, 'annotate': False, 'limit': 60,
        })
    except ValueError as error:
        if not entry.get('url'):
            return {**entry, 'kind': 'note', 'body': entry.get('name', ''), 'source_error': str(error)}
        raise

    snapshot_id, version = first['snapshot_id'], first['resolved_version']
    nodes = {node['node_id']: node for node in first.get('nodes', []) if node.get('node_id')}
    offset = first.get('next_offset')
    while offset is not None:
        page = await call(session, 'lanhu_get_design_overview', {
            'url': project_url, 'design_id': design_id, 'version_id': version,
            'annotate': False, 'limit': 60, 'offset': offset,
        })
        if page['snapshot_id'] != snapshot_id or page['resolved_version'] != version:
            raise ValueError('蓝湖设计版本在分页期间发生变化')
        nodes.update((node['node_id'], node) for node in page.get('nodes', []) if node.get('node_id'))
        next_offset = page.get('next_offset')
        if next_offset is not None and next_offset <= offset:
            raise ValueError('蓝湖节点分页没有继续前进')
        offset = next_offset
    if len(nodes) != first['total_nodes']:
        raise ValueError(f'节点未取完整：{len(nodes)} / {first["total_nodes"]}')

    canvas = first['canvas']
    native = first['original_reference_size']
    width, height = int(native['width']), int(native['height'])
    scale_x, scale_y = width / canvas['width'], height / canvas['height']
    if abs(scale_x - scale_y) >= .01 or not first.get('coordinate_mapping', {}).get('verified'):
        raise ValueError('蓝湖原图与设计画布的坐标映射未验证')
    reference = Image.new('RGBA', (width, height))
    tile_total=((width+1099)//1100)*((height+1099)//1100);tile_index=0
    for y in range(0, height, 1100):
        for x in range(0, width, 1100):
            tile_index+=1
            if progress:progress('下载原稿',tile=tile_index,tiles=tile_total)
            tile_width, tile_height = min(1100, width - x), min(1100, height - y)
            tile = await call(session, 'lanhu_inspect_design_region', {
                'snapshot_id': snapshot_id,
                'region': {'x': x / scale_x, 'y': y / scale_y,
                           'width': tile_width / scale_x, 'height': tile_height / scale_y},
                'annotate': False, 'limit': 1,
            })
            if tile['snapshot_id'] != snapshot_id or tile['resolved_version'] != version:
                raise ValueError('蓝湖原图分块与快照版本不一致')
            resource = await session.read_resource(tile['reference_crop_resource'])
            image = Image.open(io.BytesIO(base64.b64decode(resource.contents[0].blob, validate=True))).convert('RGBA')
            if image.size != (tile_width, tile_height):
                raise ValueError('蓝湖原图分块尺寸与请求不一致')
            reference.paste(image, (x, y))

    folder.mkdir(parents=True, exist_ok=True)
    reference.save(folder / 'reference.png')
    snapshot = {key: first[key] for key in (
        'snapshot_id', 'design_id', 'design_name', 'resolved_version', 'canvas',
        'coordinate_space', 'coordinate_mapping', 'reference_size', 'font_requirements',
        'total_nodes', 'gaps') if key in first}
    snapshot.update({'nodes': list(nodes.values()), 'project_name': project['project_name'],
                     'source_url': project_url})
    write_json(folder / 'snapshot.json', snapshot)
    return {**entry, 'kind': 'design', 'bundle': design_id,
            'resolved_version': version, 'snapshot_id': snapshot_id}


async def run(mode, url, output=None):
    async with stdio_client(StdioServerParameters(command='/bin/bash', args=[LAUNCHER]), errlog=sys.stderr) as (reader, writer):
        async with ClientSession(reader, writer) as session:
            await session.initialize()
            project_url = await resolve_url(session, url)
            project = await call(session, 'lanhu_get_designs', {'url': project_url})
            result = {'project_name': project['project_name'], 'source_url': project_url,
                      'total_designs': 0, 'designs': [entry for entry in project.get('designs', [])
                                                    if entry.get('url') and is_screen(entry)]}
            result['total_designs'] = len(result['designs'])
            if mode == 'preview':
                return result
            output.mkdir(parents=True, exist_ok=True)
            write_json(output / 'source.json', {'source_url': project_url,
                                                 'project_name': project['project_name'],
                                                 'total_designs': result['total_designs']})
            items = []
            designs=result['designs'];total=len(designs)
            report_progress(output,status='running',completed=0,current=0,total=total,
                            name='',phase='准备同步')
            for position,entry in enumerate(designs,1):
                def progress(phase,**extra):
                    report_progress(output,status='running',completed=position-1,current=position,
                                    total=total,name=str(entry.get('name','未命名页面')).splitlines()[0],
                                    phase=phase,**extra)
                try:
                    items.append(await fetch_design(session, project_url, project, entry, output, progress))
                except Exception as error:
                    items.append({**entry, 'kind': 'unavailable', 'error': str(error)})
                report_progress(output,status='running',completed=position,current=position,total=total,
                                name=str(entry.get('name','未命名页面')).splitlines()[0],phase='页面已完成')
            result['items'] = items
            write_json(output / 'manifest.json', result)
            report_progress(output,status='complete',completed=total,current=total,total=total,
                            name='',phase='正在写入项目')
            return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=('preview', 'sync'))
    parser.add_argument('--url', required=True)
    parser.add_argument('--output')
    args = parser.parse_args()
    output = Path(args.output).resolve() if args.output else None
    if args.mode == 'sync' and output is None:
        raise SystemExit('--output is required for sync')
    print(json.dumps(asyncio.run(run(args.mode, args.url, output)), ensure_ascii=False, allow_nan=False))


if __name__ == '__main__':
    main()
