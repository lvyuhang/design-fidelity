#!/usr/bin/env python3
"""Portable setup, diagnostics, preview and example verification."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import socket
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
LOCAL = ROOT/'.local'
CONFIG = LOCAL/'project.json'
APP = ROOT/'flutter_ui_components'
TOOLS = json.loads((ROOT/'toolchain.json').read_text())
EXAMPLE = ROOT/'examples/withdraw-2'


def load_config():
    return json.loads(CONFIG.read_text()) if CONFIG.is_file() else {}


def environment(config=None):
    env = os.environ.copy()
    for path in (ROOT/'.env.local',ROOT/'android-design-review/.env.local'):
        if not path.is_file(): continue
        for line in path.read_text().splitlines():
            match = re.fullmatch(r'\s*(?:export\s+)?([A-Z][A-Z0-9_]*)=(.*)',line)
            if match:
                value = match[2].strip()
                if value[:1] in ('"',"'") and value[-1:] == value[:1]: value=value[1:-1]
                env.setdefault(match[1],os.path.expandvars(os.path.expanduser(value)))
    config = config if config is not None else load_config()
    if config.get('flutter'): env['PATH']=str(Path(config['flutter']).parent)+os.pathsep+env.get('PATH','')
    if config.get('python'): env.setdefault('LANHU_CLIENT_PYTHON',config['python'])
    if config.get('mcp_installed'): env.setdefault('LANHU_MCP_LAUNCHER',str(ROOT/'integrations/run-lanhu-mcp.sh'))
    return env


def run(command,cwd=ROOT,env=None,capture=False):
    return subprocess.run([str(v) for v in command],cwd=cwd,env=env or environment(),
                          check=True,text=True,capture_output=capture)


def python_path():
    py=load_config().get('python') or str(ROOT/'.venv/bin/python')
    if not Path(py).is_file(): raise ValueError('尚未安装依赖，请先运行 ./setup.command')
    return py


def find_flutter(explicit=None):
    env=environment();candidates=[]
    for value in (explicit,env.get('FLUTTER_ROOT')):
        if value:
            p=Path(value).expanduser();candidates.append(p/'bin/flutter' if p.is_dir() else p)
    candidates.extend([ROOT/'.tools/flutter/bin/flutter',load_config().get('flutter'),shutil.which('flutter',path=env.get('PATH'))])
    return next((str(Path(p).resolve()) for p in candidates if p and Path(p).is_file()),None)


def flutter_info(executable):
    output=run([executable,'--version','--machine'],capture=True).stdout
    return json.loads(output[output.index('{'):])


def source_fingerprint():
    digest=hashlib.sha256()
    files=[APP/'pubspec.yaml',APP/'pubspec.lock']
    for directory in ('lib','assets','web'):
        files.extend(p for p in (APP/directory).rglob('*') if p.is_file() and p.name!='font-receipt.json')
    for path in sorted(files):
        digest.update(str(path.relative_to(APP)).encode());digest.update(path.read_bytes())
    digest.update(TOOLS['flutter_revision'].encode())
    return digest.hexdigest()


def record_build():
    LOCAL.mkdir(exist_ok=True)
    receipt={'source_sha256':source_fingerprint(),
             'main_js_sha256':hashlib.sha256((APP/'build/web/main.dart.js').read_bytes()).hexdigest()}
    (LOCAL/'flutter-build.json').write_text(json.dumps(receipt,indent=2)+'\n')


def build_current():
    receipt=LOCAL/'flutter-build.json';main=APP/'build/web/main.dart.js'
    if not receipt.is_file() or not main.is_file():return False
    try:
        data=json.loads(receipt.read_text())
        return data['source_sha256']==source_fingerprint() and data['main_js_sha256']==hashlib.sha256(main.read_bytes()).hexdigest()
    except (ValueError,KeyError,OSError):return False


def setup(args):
    if sys.version_info < (3,11): raise ValueError('请使用 Python 3.11+ 运行安装入口')
    py=ROOT/'.venv/bin/python'
    if not py.exists():run([sys.executable,'-m','venv',ROOT/'.venv'])
    req=ROOT/('requirements-review.txt' if args.profile in ('all','review') else 'requirements-setup.txt')
    run([py,'-m','pip','install','--disable-pip-version-check','-r',req])
    config=load_config();config.update(python=str(py),profile=args.profile)
    if args.profile == 'skill':
        args.with_mcp = True  # Page work always needs the Lanhu MCP server.
    if args.with_mcp:
        run([py,'-m','pip','install','--disable-pip-version-check','-c',ROOT/'constraints-mcp.txt','-e',ROOT/'integrations/lanhu-mcp'])
        config['mcp_installed']=True
    if args.profile in ('all','flutter'):
        flutter=find_flutter(args.flutter_sdk)
        if not flutter:raise ValueError('未找到 Flutter SDK。按 https://docs.flutter.dev/install/manual 安装 '+TOOLS['flutter']+'，然后用 --flutter-sdk /path/to/flutter 重试。')
        info=flutter_info(flutter)
        if info.get('frameworkRevision') != TOOLS['flutter_revision']:
            raise ValueError('需要冻结的 Flutter '+TOOLS['flutter']+' / '+TOOLS['flutter_revision'][:10]+'，请用 --flutter-sdk 指定对应 SDK；不会静默更换版本。')
        config.update(flutter=flutter,framework_revision=info['frameworkRevision'])
        command=[py,ROOT/'tools/prepare_fonts.py']
        for flag,value in (('--font-dir',args.font_dir),('--pingfang',args.pingfang),('--arial-unicode',args.arial_unicode)):
            if value:command.extend([flag,value])
        if args.regenerate_fonts:command.append('--force')
        run(command)
        env=environment(config)
        run([flutter,'pub','get','--enforce-lockfile'],cwd=APP,env=env)
        run([flutter,'build','web','--no-pub'],cwd=APP,env=env)
        record_build()
    LOCAL.mkdir(exist_ok=True);CONFIG.write_text(json.dumps(config,ensure_ascii=False,indent=2)+'\n')
    (LOCAL/'python-resolved.txt').write_text(run([py,'-m','pip','freeze'],capture=True).stdout)
    print('安装完成：python3 project.py doctor 查看状态；python3 project.py start flutter 启动对比。')


def doctor(args):
    config=load_config();env=environment(config);py=config.get('python');deps={}
    fonts=APP/'assets/fonts'
    names=['PingFangSC-Regular.otf','PingFangSC-Medium.otf','PingFangSC-Semibold.otf',
           'PingFangSC-Full-Regular.ttf','PingFangSC-Full-Medium.ttf','ArialUnicode-Gift.ttf']
    if py and Path(py).is_file():
        result=run([py,'-c','import importlib.util,json;print(json.dumps({n:importlib.util.find_spec(n) is not None for n in ["PIL","numpy","fontTools","av","mcp"]}))'],capture=True)
        deps=json.loads(result.stdout)
    status={
        'preview_ready':bool(find_flutter() and all((fonts/n).is_file() for n in names) and build_current()),
        'python_dependencies':deps,'flutter_version_required':TOOLS['flutter'],
        'fonts_present':all((fonts/n).is_file() for n in names),
        'offline_example_present':(EXAMPLE/'source.json').is_file(),
        'review_ready':all(deps.get(n,False) for n in ('PIL','numpy','av')),
        'lanhu_configured_not_authenticated':bool(env.get('LANHU_MCP_LAUNCHER') and Path(env['LANHU_MCP_LAUNCHER']).is_file() and deps.get('mcp')),
        'adb_found_not_device_authorized':bool(env.get('REVIEW_ADB') or shutil.which('adb',path=env.get('PATH'))),
        'codex_found_not_authenticated':bool(shutil.which('codex',path=env.get('PATH'))),
        'scope':'Local configuration only. MCP/AI login and device authorization require real connectivity checks.',
    }
    print(json.dumps(status,ensure_ascii=False,indent=2))
    return 2 if args.strict and not status['preview_ready'] else 0


def port_available(port):
    if not 1<=port<=65535:raise ValueError('端口必须介于1和65535之间')
    with socket.socket() as listener:
        try:listener.bind(('127.0.0.1',port))
        except OSError:raise ValueError('端口%s已占用，请用 --port 换端口；不会终止已有服务。'%port)


def start(args):
    py=python_path();port=args.port or (8767 if args.target=='flutter' else 8769)
    port_available(port);config=load_config();env=environment(config)
    if args.target=='flutter':
        build=APP/'build/web'
        if args.build or not build_current():
            run([config['flutter'],'build','web','--no-pub'],cwd=APP,env=env)
            record_build()
        print('Flutter 对比：http://127.0.0.1:%s/?case=withdraw-2-skill2186'%port,flush=True)
        run([py,'-m','http.server',port,'--bind','127.0.0.1','--directory',build],env=env)
    else:
        env.setdefault('REVIEW_DATA_DIR',str(LOCAL/'review-data'))
        if args.demo:
            env['REVIEW_DATA_DIR']=str(LOCAL/'review-demo')
            run([py,ROOT/'android-design-review/server.py','--import-snapshot',EXAMPLE/'source.json',
                 '--reference',EXAMPLE/'reference.png','--name','提现-2 · 离线设计快照'],env=env)
        print('安卓验收台：http://127.0.0.1:%s/'%port,flush=True)
        run([py,ROOT/'android-design-review/server.py','--port',port],env=env)


def verify(args):
    py=python_path()
    run([py,ROOT/'tools/verify_installation.py',*(['--render'] if args.render else [])])


def check_mcp(args):
    command=[python_path(),ROOT/'integrations/check_mcp_connection.py']
    if args.url:command.extend(['--url',args.url])
    if args.launcher:command.extend(['--launcher',args.launcher])
    run(command)


def mcp_serve(args):
    executable=ROOT/'.venv/bin/lanhu-mcp'
    if not executable.is_file():raise ValueError('请先安装 --with-mcp')
    os.execve(str(executable),[str(executable),'--transport','stdio'],environment())


def main():
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='command',required=True)
    s=sub.add_parser('setup');s.add_argument('--profile',choices=('skill','flutter','review','all'),default='flutter',help='skill: 仅研发页面工作所需（Skill 依赖 + 蓝湖 MCP），不构建样例')
    for flag in ('--flutter-sdk','--font-dir','--pingfang','--arial-unicode'):s.add_argument(flag)
    s.add_argument('--regenerate-fonts',action='store_true');s.set_defaults(handler=setup)
    s.add_argument('--with-mcp',action='store_true')
    d=sub.add_parser('doctor');d.add_argument('--strict',action='store_true');d.set_defaults(handler=doctor)
    s=sub.add_parser('start');s.add_argument('target',choices=('flutter','review'));s.add_argument('--port',type=int)
    s.add_argument('--build',action='store_true');s.add_argument('--demo',action='store_true');s.set_defaults(handler=start)
    v=sub.add_parser('verify');v.add_argument('--render',action='store_true');v.set_defaults(handler=verify)
    m=sub.add_parser('check-mcp');m.add_argument('--launcher');m.add_argument('--url');m.set_defaults(handler=check_mcp)
    sub.add_parser('mcp-serve').set_defaults(handler=mcp_serve)
    a=p.parse_args()
    try:return a.handler(a) or 0
    except (ValueError,KeyError,OSError,subprocess.CalledProcessError) as e:
        print('未完成：'+str(e),file=sys.stderr);return 2
    except KeyboardInterrupt:return 130


if __name__=='__main__':raise SystemExit(main())
