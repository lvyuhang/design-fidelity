"""Read binary references without routing base64 through a truncated tool response."""
import asyncio
import base64
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

ROOT = Path(__file__).resolve().parents[1]
SERVER = '/Users/tan/Documents/Codex/2026-10-10/https-github-com-dsphper-lanhu-mcp/lanhu-mcp/run-local-mcp.sh'
SNAPSHOT = 'ed07411fb68b9878b1395ab190b98915'
REFERENCES = {
    'region': '7eac060a3b71fe8bc3b974ac220d53d2',
    'buttons-4x': 'f3f1cf24cbc18d18223f714a688e6c38',
    'agreement-4x': '8876cc3321ea9e6c7e2741e0d147d3f0',
}

async def main():
    params = StdioServerParameters(command='/bin/bash', args=[SERVER])
    with (ROOT / 'design_evidence/resource-client.log').open('w') as errors:
        async with stdio_client(params, errlog=errors) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                for name, preview in REFERENCES.items():
                    result = await session.read_resource(f'lanhu://design/{SNAPSHOT}/preview/{preview}')
                    data = base64.b64decode(result.contents[0].blob, validate=True)
                    dest = ROOT / f'design_evidence/reference-{name}.png'
                    dest.write_bytes(data)
                    print(f'{dest.name}: {len(data)} bytes')

asyncio.run(main())
