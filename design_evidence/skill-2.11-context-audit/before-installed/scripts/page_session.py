#!/usr/bin/env python3
"""Project-configured entry point; delegates evidence and acceptance to existing tools."""
from __future__ import annotations
import argparse
import html
import json
from pathlib import Path
import subprocess
import sys
import time

from fidelity_contract import read_json, sha256, verify_receipt
from round_log import RoundLog, utc

SCRIPTS = Path(__file__).resolve().parent


def status(data, root):
    end = data.get('finished_unix') or time.time()
    active = sum(e.get('seconds', 0) for e in data['events'])
    rounds = read_json(root/'task-run.json').get('summary') if (root/'task-run.json').exists() else None
    return {'status': data['status'], 'elapsed_seconds': round(end-data['started_unix'], 3),
            'command_seconds': round(active, 3),
            'unattributed_seconds': round(max(0, end-data['started_unix']-active), 3),
            'timing_scope': 'Since explicit start; includes editing, waiting and failures. Time before start is unknown.',
            'tokens': None, 'rounds': rounds, 'session_log': str(root/'session.html')}


def save(data, root):
    data['summary'] = status(data, root)
    temp = root/'session.tmp'
    temp.write_text(json.dumps(data, ensure_ascii=False, indent=2)+'\n')
    temp.replace(root/'session.json')
    esc = lambda x: html.escape(str(x))
    rows = ''.join('<tr>'+''.join(f'<td>{esc(e.get(k, ""))}</td>' for k in
        ('action','status','seconds','note','error'))+'</tr>' for e in data['events'])
    s = data['summary']
    (root/'session.html').write_text(
        '<!doctype html><meta charset="utf-8"><title>页面全程日志</title>'
        '<style>body{font:15px/1.6 system-ui;max-width:1100px;margin:32px auto}td,th{padding:10px;text-align:left;border-bottom:1px solid #ddd}pre{white-space:pre-wrap}</style>'
        f'<h1>{esc(data["name"])} · {esc(data["status"])}</h1>'
        f'<p>从 start 到当前/结束：{s["elapsed_seconds"]} 秒；命令执行：{s["command_seconds"]} 秒；其余未归因时间：{s["unattributed_seconds"]} 秒。</p>'
        '<p>未归因时间含编辑、等待等，不能全部算为模型思考；start 前耗时未知。Token 未采集。</p>'
        '<p><a href="task-run.html">逐轮视觉验证</a> · <a href="session.json">完整运行记录</a></p>'
        '<table><tr><th>操作</th><th>状态</th><th>秒</th><th>说明</th><th>错误</th></tr>'+rows+'</table>'
        f'<pre>{esc(json.dumps(s.get("rounds"),ensure_ascii=False,indent=2))}</pre>')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--config', type=Path, required=True)
    p.add_argument('action', choices=['start','prepare','compile','validate','status','finish'])
    p.add_argument('--note', default='')
    p.add_argument('--build', action='store_true')
    args = p.parse_args()
    config = args.config.resolve()
    c = read_json(config)
    path = lambda key: (config.parent/c[key]).resolve()
    root = path('run_dir')
    root.mkdir(parents=True, exist_ok=True)
    try:
        # One page operation at a time; interrupted locks are never silently removed.
        with RoundLog(root/'session.json').locked():
            state = root/'session.json'
            if args.action == 'start':
                if state.exists():
                    raise ValueError('Session already exists; resume it, do not reset its timer')
                data = {'name':c['name'], 'status':'RUNNING', 'started_unix':time.time(),
                        'started_at':utc(time.time()), 'config':str(config), 'events':[]}
                save(data, root)
                print(json.dumps(data['summary'], ensure_ascii=False)); return 0
            if not state.exists():
                raise ValueError('Run start before evidence collection; no retroactive timing')
            data = read_json(state)
            if data['config'] != str(config) or data['name'] != c['name']:
                raise ValueError('Session belongs to another config/page')
            if args.action == 'status':
                save(data, root)
                print(json.dumps(data['summary'], ensure_ascii=False)); return 0
            if data['status'] != 'RUNNING':
                raise ValueError('Session is already complete; use a new explicitly named task')
            started = time.monotonic()
            event = {'action':args.action, 'status':'RUNNING', 'started_at':utc(time.time()),
                     'config_sha256':sha256(config), 'note':args.note}
            data['events'].append(event)
            save(data, root)
            output = root/f'{len(data["events"]):03d}-{args.action}'

            def invoke(script, flags):
                command = [sys.executable, str(SCRIPTS/script), *map(str, flags)]
                log = root/f'{len(data["events"]):03d}-{Path(script).stem}.log'
                event.setdefault('commands', []).append({'argv':command, 'log':str(log)})
                with log.open('w') as stream:
                    run = subprocess.run(command, cwd=config.parent, stdout=stream,
                                         stderr=subprocess.STDOUT, timeout=900)
                if run.returncode:
                    raise ValueError(f'{script} returned {run.returncode}; see {log}')

            try:
                if args.action == 'prepare':
                    evidence = [v for entry in c['evidence'] for v in ('--evidence', (config.parent/entry).resolve())]
                    invoke('prepare_page.py', [*evidence, '--reference', path('reference'),
                        '--manifest',path('manifest'),'--output',output,
                        *(['--font-map',path('font_map')] if c.get('font_map') else [])])
                    invoke('init_visual_contract.py', [*evidence,'--reference',path('reference'),
                        '--output',output/'draft.json','--name',c['name']])
                elif args.action == 'compile':
                    invoke('compile_contract.py', ['--spec',path('spec'),'--output',path('contract')])
                elif args.action == 'validate':
                    contract = read_json(path('contract'))
                    expected = c.get('scope', 'page')
                    if expected not in ('page','provided_nodes') or contract['source_scope']['kind'] != expected:
                        raise ValueError('Requested scope differs from contract; whole-page tasks cannot silently become local checks')
                    invoke('run_flutter.py', ['--contract',path('contract'),'--app',path('app'),
                        '--test',c['test'],'--output-env',c['output_env'],'--output',output,
                        '--task-log',root/'task-run.json','--round-note',args.note,
                        *(['--analyze',*c['analyze']] if c.get('analyze') else []),
                        *(['--build'] if args.build else [])])
                    event['report'] = str(output/'run.json')
                else:
                    prior = [e for e in data['events'][:-1] if e['action'] != 'finish']
                    latest = prior[-1] if prior else {}
                    if latest.get('action') != 'validate' or latest.get('status') != 'OK' or not args.note.strip():
                        raise ValueError('Finish needs a last successful validation and a final visual-review/preview note')
                    rendered = Path(latest['report']).parent
                    verify_receipt(rendered/'receipt.json', rendered/'render.png',
                                   path('contract'), read_json(path('contract')))
                    data.update(status='COMPLETE', finished_unix=time.time())
                event['status'] = 'OK'
            except (ValueError,OSError,KeyError,subprocess.TimeoutExpired) as exc:
                event.update(status='FAILED', error=str(exc))
            event['seconds'] = round(time.monotonic()-started,3)
            save(data, root)
            print(json.dumps({'action':event, **data['summary']}, ensure_ascii=False))
            return 0 if event['status'] == 'OK' else 2
    except (ValueError,OSError,KeyError) as exc:
        print(json.dumps({'status':'SESSION_ERROR','error':str(exc)},ensure_ascii=False)); return 2


if __name__ == '__main__':
    raise SystemExit(main())
