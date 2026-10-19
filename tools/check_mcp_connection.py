"""Check real stdio MCP capabilities, optionally read a project with the user's login."""
import argparse
import asyncio
import json
import os
from pathlib import Path
import sys
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

ROOT=Path(__file__).resolve().parents[1]
REQUIRED={'lanhu_get_designs','lanhu_get_design_overview','lanhu_inspect_design_region','lanhu_export_design_assets'}


async def check(args):
    launcher=args.launcher or os.environ.get('LANHU_MCP_LAUNCHER') or str(ROOT/'integrations/run-lanhu-mcp.sh')
    if not Path(launcher).expanduser().is_file():raise ValueError('蓝湖 MCP 启动脚本不存在')
    folder=ROOT/'.local';folder.mkdir(exist_ok=True)
    async with asyncio.timeout(60):
        with (folder/'mcp-connection.log').open('w') as log:
            async with stdio_client(StdioServerParameters(command='/bin/bash',args=[str(Path(launcher).expanduser().resolve())],env=os.environ.copy()),errlog=log) as (reader,writer):
                async with ClientSession(reader,writer) as session:
                    await session.initialize()
                    tools=await session.list_tools();names={v.name for v in tools.tools}
                    missing=sorted(REQUIRED-names)
                    result={'stdio_initialized':True,'required_tools_present':not missing,'missing_tools':missing,'login':'NOT_TESTED'}
                    if missing:raise ValueError('当前 MCP 缺少 Skill 所需扩展接口：'+', '.join(missing))
                    if args.url:
                        response=await session.call_tool('lanhu_get_designs',{'url':args.url})
                        data=response.structuredContent or next((json.loads(c.text) for c in response.content if getattr(c,'type',None)=='text'),{})
                        if response.isError or not isinstance(data,dict) or data.get('status') != 'success' or not isinstance(data.get('designs'),list):
                            raise ValueError('真实项目读取失败；请在本机配置自己的蓝湖登录后重试。详见 .local/mcp-connection.log')
                        result.update(login='PROJECT_READ_SUCCEEDED',design_count=data.get('total_designs'))
                    (folder/'mcp-report.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
                    print(json.dumps(result,ensure_ascii=False,indent=2))


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--launcher');p.add_argument('--url');a=p.parse_args()
    try:asyncio.run(check(a))
    except Exception as error:
        # Raw MCP errors may echo headers or tool arguments; keep them in local diagnostics.
        print('MCP 检查未完成：'+type(error).__name__+'；检查本机路径、依赖和登录配置。',file=sys.stderr);return 2
    return 0


if __name__=='__main__':raise SystemExit(main())
