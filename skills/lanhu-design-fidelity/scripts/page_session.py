#!/usr/bin/env python3
"""Project-configured entry point; delegates evidence and acceptance to existing tools."""
from __future__ import annotations
import argparse
import html
import json
import os
from pathlib import Path
import subprocess
import sys
import time

from fidelity_contract import read_json, sha256, verify_receipt
from round_log import RoundLog, utc

SCRIPTS = Path(__file__).resolve().parent


def session_rounds(data, root):
    """Use immutable attempt reports, so renaming a task log cannot reset totals."""
    tickets, attempts, baselines = set(), set(), set()
    total, latest, missing, calls = 0.0, 'NOT_STARTED', 0, 0
    for event in data['events']:
        if event['action'] not in ('validate', 'accept'):
            continue
        calls += 1
        report = Path(event['report']) if event.get('report') else None
        if not report or not report.is_file():
            missing += 1
            continue
        run = read_json(report)
        ticket = run.get('iteration', {})
        identity = ticket.get('attempt_id')
        if not identity or identity in attempts:
            if not identity:
                missing += 1
            continue
        attempts.add(identity)
        tickets.add((ticket['task_id'], ticket['round_number']))
        baselines.add(ticket['task_id'])
        total += run.get('seconds', 0)
        latest = run.get('status', 'RUNNING')
    if not calls:
        return None
    # Per-baseline classifications remain in individual task logs. A baseline
    # restart must not be represented as an implementation correction.
    return {'rounds': len(tickets), 'validation_attempts': len(attempts),
            'validation_calls': calls, 'untracked_calls': missing,
            'baseline_count': len(baselines), 'implementation_revisions': None,
            'criteria_revisions': None, 'repeat_attempts': len(attempts)-len(tickets),
            'latest_status': latest, 'over_target': len(tickets)>3,
            'total_validation_seconds': round(total, 3),
            'count_scope': 'Session attempt reports across all baselines; missing reports are not invented'}


def phase_seconds(data, end):
    marks = data.get('phase_marks', [])
    if not marks:
        return {'unclassified': round(end-data['started_unix'], 3)}
    totals = {}
    for i, mark in enumerate(marks):
        stop = marks[i+1]['unix'] if i+1 < len(marks) else end
        totals[mark['phase']] = totals.get(mark['phase'], 0) + max(0, stop-mark['unix'])
    return {k:round(v, 3) for k,v in totals.items()}


def status(data, root):
    end = data.get('finished_unix') or time.time()
    active = sum(e.get('seconds', 0) for e in data['events'])
    rounds = session_rounds(data, root)
    return {'status': data['status'], 'elapsed_seconds': round(end-data['started_unix'], 3),
            'command_seconds': round(active, 3),
            'unattributed_seconds': round(max(0, end-data['started_unix']-active), 3),
            'timing_scope': 'Since explicit start; includes editing, waiting and failures. Time before start is unknown.',
            'tokens': None, 'rounds': rounds, 'phase_seconds': phase_seconds(data, end),
            'session_log': str(root/'session.html')}


def next_action(event=None, details=None):
    """Route only from recorded stages/statuses, never from error-message text."""
    code, action, instruction = 'READ_REPORT', 'read_report', '读取 report 和对应日志，确认阻断项后再继续。'
    details = details or {}
    if event:
        current, outcome = event['action'], event['status']
        state = details.get('status')
        if current == 'prepare':
            if state == 'NEEDS_INPUT_FIXES':
                code, action, instruction = ('FIX_INPUTS', 'inspect --view issues',
                    '按 issues 补齐源证据，再 prepare。')
            elif outcome == 'OK' and state == 'PREPARED_FOR_REVIEW' and details.get('generate_configured'):
                code, action, instruction = ('GENERATE', 'generate',
                    '生成确定性首版（原语 + token + sourceKey），再按报告复核 unsupported/issues。')
            elif outcome == 'OK' and state == 'PREPARED_FOR_REVIEW':
                code, action, instruction = ('REVIEW_SOURCE', 'inspect --view components',
                    '读取并复核组件证据后实施；准备完成不代表验收通过。')
        elif current == 'generate' and outcome == 'OK':
            code, action, instruction = ('IMPLEMENT_SEMANTICS', 'phase --phase implementation',
                '页面组合生成的 Scene：用 overrides 替换需要组件化/动态数据的组，用 onTap 接交互；'
                '不改 .g.dart。处理 unsupported 与 issues，把 draft_node_decisions 复核后写入 reviewed spec。')
        elif current == 'compile' and outcome == 'OK' and state == 'ready':
            code, action, instruction = ('VALIDATE', 'validate',
                '用冻结契约验证当前实现；编译完成不代表视觉通过。')
        elif current in ('validate', 'accept'):
            gate = details.get('gate_status')
            if gate == 'NOT_EVALUATED' or details.get('failed_stage') in ('baseline', 'preflight'):
                code, action, instruction = ('FIX_PREREQUISITES', 'read_report',
                    '先按报告修复证据、契约或前置检查，再 validate；勿盲目重渲染。')
            elif gate == 'FAIL':
                code, action, instruction = ('FIX_IMPLEMENTATION', 'fix_implementation_then_validate',
                    '按完整失败报告批量修实现后再 validate；禁止改阈值、删检查或扩大排除。')
            elif outcome == 'OK' and state in ('PASS', 'PASS_WITH_EXCLUSIONS') and gate == state:
                code, action, instruction = ('REVIEW_AND_FINISH', 'phase --phase preview',
                    '核对当前收据，并列复查原稿与渲染、完成预览后 finish --note，披露排除项。')
        elif current == 'finish' and outcome == 'OK':
            code, action, instruction = 'COMPLETE', 'none', '本次验收与复查已记录。'
    return {'code': code, 'action': action, 'instruction': instruction}


def compact_result(data, root, event=None):
    """Return actionable results; keep command arrays and complete evidence on disk."""
    s = data['summary']
    result = {k:s[k] for k in ('status','elapsed_seconds','command_seconds','tokens')}
    result['rounds'] = ({k:s['rounds'][k] for k in ('rounds','validation_attempts',
        'implementation_revisions','criteria_revisions','repeat_attempts','latest_status','over_target')}
        if s['rounds'] else None)
    result['report'] = str(root/'session.json')
    result['phase_seconds'] = s.get('phase_seconds')
    result['next_action'] = next_action()
    if s['rounds']:
        result['rounds'].update({k:s['rounds'][k] for k in
            ('baseline_count', 'validation_calls', 'untracked_calls')})
    if not event:
        return result
    result.update(action=event['action'], action_status=event['status'], seconds=event['seconds'])
    if event.get('error'):
        result['error'] = event['error'][:500]
    report = Path(event['report']) if event.get('report') else None
    details = None
    if report and report.is_file():
        result['report'] = str(report)
        details = read_json(report)
        if event['action'] in ('validate', 'accept'):
            failures = details.get('failures', [])
            result.update(gate_status=details.get('gate_status'), failed_stage=details.get('failed_stage'),
                failed_check_count=len(failures), failed_checks=failures[:5])
            if details.get('error'):
                result['error'] = details['error'][:500]
        elif event['action'] == 'prepare':
            result['preparation'] = {k:details[k] for k in
                ('status','source_nodes','asset_count','issue_counts','review_count','brief',
                 'missing_bitmap_count','text_style_group_count','major_frame_count','error') if k in details}
            details = {**details, 'generate_configured': bool(data.get('generate_configured'))}
        elif event['action'] == 'generate':
            result['generation'] = {k:details.get(k) for k in ('status','mode_counts','output')}
            result['generation'].update(
                unsupported=[{k:u[k] for k in ('node_id','feature')} for u in details.get('unsupported', [])][:10],
                issue_counts={i['kind']: sum(1 for j in details.get('issues', []) if j['kind'] == i['kind'])
                              for i in details.get('issues', [])},
                system_chrome=[c['kind'] for c in details.get('system_chrome', [])])
    result['next_action'] = next_action(event, details)
    return result


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
        f'<p>阶段墙钟（含该阶段的等待）：{esc(s["phase_seconds"])}</p>'
        f'<p>全任务验证统计：{esc(s["rounds"])}</p>'
        '<p><a href="task-run.html">逐轮视觉验证</a> · <a href="session.json">完整运行记录</a></p>'
        '<table><tr><th>操作</th><th>状态</th><th>秒</th><th>说明</th><th>错误</th></tr>'+rows+'</table>'
        f'<pre>{esc(json.dumps(s.get("rounds"),ensure_ascii=False,indent=2))}</pre>')


def require_prepared_sources(data, config, config_dir):
    """Fail before expensive work for configured full-page evidence pipelines."""
    if not config.get('evidence'):
        return  # Legacy validation-only configs; not a complete page workflow.
    ready = [e for e in data['events'] if e['action'] == 'prepare' and e.get('status') == 'OK']
    if not ready:
        raise ValueError('Full-page acceptance requires successful prepare before rendering')
    latest = ready[-1]
    inputs = [(config_dir / name).resolve() for name in config['evidence']]
    inputs += [(config_dir / config[key]).resolve() for key in
               ('reference', 'manifest', 'font_map', 'pending_assets') if config.get(key)]
    current = {str(p): sha256(p) for p in inputs}
    if current != latest.get('prepared_input_hashes'):
        raise ValueError('Prepared source inputs changed; prepare again before rendering')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--config', type=Path, required=True)
    p.add_argument('action', choices=['start','phase','prepare','generate','inspect','compile','validate','accept','status','finish','stop'])
    p.add_argument('--view', choices=['overview','components','text','visual','assets','scenes','effects','issues','nodes'], default='overview')
    p.add_argument('--component', action='append', help='Source group ID/alias; repeat for flat siblings; all selects the page')
    p.add_argument('--file', type=Path, help='Saved JSON path, relative to config')
    p.add_argument('--pointer', default=None, help='Exact JSON pointer for deferred data')
    p.add_argument('--node', help='Read one raw source node by ID')
    p.add_argument('--cursor', type=int, default=0)
    p.add_argument('--limit', type=int, help='Optional character guard. Component packets are atomic; generic views default to 8000')
    p.add_argument('--sha256', help='File identity required for continuation')
    p.add_argument('--refresh', action='store_true', help='Re-send a previously delivered evidence page after context loss')
    p.add_argument('--phase', choices=['evidence','implementation','validation','preview','diagnostic_preview','infrastructure'])
    p.add_argument('--note', default='')
    p.add_argument('--build', action='store_true')
    p.add_argument('--verbose', action='store_true', help='Print full session/event details; default is a compact result')
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
                now = time.time()
                data = {'name':c['name'], 'status':'RUNNING', 'started_unix':now,
                        'started_at':utc(time.time()), 'config':str(config), 'events':[]}
                data['python'] = sys.executable
                data['phase_marks'] = [{'phase':'evidence','unix':now}]
                save(data, root)
                print(json.dumps(data['summary'] if args.verbose else compact_result(data,root), ensure_ascii=False)); return 0
            if not state.exists():
                raise ValueError('Run start before evidence collection; no retroactive timing')
            data = read_json(state)
            if data['config'] != str(config) or data['name'] != c['name']:
                raise ValueError('Session belongs to another config/page')
            data['generate_configured'] = bool(c.get('generated'))
            if args.action == 'status':
                save(data, root)
                print(json.dumps(data['summary'] if args.verbose else compact_result(data,root), ensure_ascii=False)); return 0
            if args.action == 'stop':
                if data['status'] != 'RUNNING' or not args.note.strip():
                    raise ValueError('Stop requires a running session and reason; it does not grant acceptance')
                now = time.time()
                data['events'].append({'action':'stop','status':'OK','seconds':0,'note':args.note})
                data.update(status='STOPPED_NOT_ACCEPTED', finished_unix=now)
                save(data, root)
                print(json.dumps(compact_result(data, root), ensure_ascii=False)); return 0
            if data['status'] != 'RUNNING':
                raise ValueError('Session is terminal; inspect status or start a separate experiment')
            if args.action == 'inspect':
                from evidence_view import view, encode
                if args.cursor and not args.sha256:
                    raise ValueError('Continuation requires --sha256 from the first response')
                pointer = args.pointer or ''
                if args.component or args.view == 'components':
                    from component_evidence import write_component
                    if args.file or args.node or args.pointer is not None or args.cursor:
                        raise ValueError('Component selection cannot be combined with generic JSON navigation')
                    preparations = [e for e in data['events'] if e['action'] == 'prepare' and e.get('report')]
                    if not preparations:
                        raise ValueError('Run prepare before component inspection')
                    folder=Path(preparations[-1]['report']).parent
                    target=write_component(folder,[(config.parent/p).resolve() for p in c['evidence']],args.component)
                elif args.file:
                    target = (config.parent/args.file).resolve()
                elif args.node:
                    from component_evidence import node_aliases
                    from visual_fidelity_gate import _load_nodes
                    source_nodes=_load_nodes([(config.parent/p).resolve() for p in c['evidence']])
                    requested_node={v:k for k,v in node_aliases(source_nodes).items()}.get(args.node,args.node)
                    target = None
                    for entry in c['evidence']:
                        source = (config.parent/entry).resolve()
                        for i, node in enumerate(read_json(source).get('nodes', [])):
                            if node.get('node_id') == requested_node:
                                target, pointer = source, f'/nodes/{i}' + pointer
                                break
                        if target:
                            break
                    if not target:
                        raise ValueError('Source node not found')
                else:
                    preparations = [e for e in data['events'] if e['action'] == 'prepare' and e.get('report')]
                    if not preparations:
                        raise ValueError('Run prepare before inspecting its views')
                    folder = Path(preparations[-1]['report']).parent
                    fields = {'text':'text_style_groups','visual':'visual_style_groups',
                              'assets':'assets','scenes':'scene_requirements','effects':'effect_requirements'}
                    if args.view == 'overview':
                        target = folder/'summary.json'
                    elif args.view in ('issues','nodes'):
                        target = folder/'page-plan.json'
                        pointer = args.pointer if args.pointer is not None else '/'+args.view
                    else:
                        target = folder/'implementation-brief.json'
                        pointer = args.pointer if args.pointer is not None else '/'+fields[args.view]
                if args.component or args.view == 'components':
                    digest=sha256(target)
                    if args.sha256 and args.sha256!=digest:
                        raise ValueError('Component evidence changed')
                    result={'file':str(target),'sha256':digest,'complete_packet':True,
                            'packet':read_json(target),'next_cursor':None}
                    if args.limit is not None:
                        if args.limit<2000:
                            raise ValueError('Component guard must be at least 2000 characters')
                        if len(encode(result))>args.limit:
                            result={'file':str(target),'sha256':digest,'complete_packet':False,
                                    'required_characters':len(encode(result)),
                                    'hint':'Select a smaller source group or explicitly raise the guard. No component data was silently truncated.',
                                    'next_cursor':None}
                else:
                    result = view(target,pointer,args.cursor,args.limit if args.limit is not None else 8000,args.sha256)
                history_path = root/'inspections.jsonl'
                identity = {'file':str(target),'sha256':result['sha256'],
                            'pointer':pointer,'cursor':args.cursor,'limit':args.limit}
                previous = [json.loads(line) for line in history_path.read_text().splitlines()] if history_path.exists() else []
                delivered = next((r for r in reversed(previous) if all(r.get(k)==v for k,v in identity.items())
                                  and not r.get('already_returned') and r.get('complete_packet',True)),None)
                if delivered and not args.refresh:
                    result = {**identity,'already_returned':True,'next_cursor':result['next_cursor'],
                              'first_returned_at':delivered['at'],
                              'hint':'Reuse prior evidence; use --refresh if it is no longer in context. This is not a review or acceptance receipt.'}
                payload = encode(result)
                with history_path.open('a') as stream:
                    stream.write(encode({'at':utc(time.time()),**identity,
                        'next_cursor':result['next_cursor'],'already_returned':result.get('already_returned',False),
                        'complete_packet':result.get('complete_packet',True),
                        'returned_characters':len(payload)})+'\n')
                print(payload)
                return 0
            if data['status'] != 'RUNNING':
                raise ValueError('Session is already complete; use a new explicitly named task')
            if args.action == 'phase':
                if not args.phase:
                    raise ValueError('phase requires --phase')
                if args.phase == 'preview':
                    prior = [e for e in data['events'] if e['action'] != 'finish']
                    latest = prior[-1] if prior else {}
                    if latest.get('action') not in ('validate', 'accept') or latest.get('status') != 'OK':
                        raise ValueError('Accepted preview requires successful validation; use diagnostic_preview for an explicitly unaccepted result')
                    rendered = Path(latest['report']).parent
                    verify_receipt(rendered/'receipt.json', rendered/'render.png',
                                   path('contract'), read_json(path('contract')))
                data.setdefault('phase_marks', []).append({'phase':args.phase,'unix':time.time()})
                save(data, root)
                print(json.dumps(compact_result(data,root),ensure_ascii=False)); return 0
            started = time.monotonic()
            event = {'action':args.action, 'status':'RUNNING', 'started_at':utc(time.time()),
                     'config_sha256':sha256(config), 'note':args.note}
            data['events'].append(event)
            save(data, root)
            output = root/f'{len(data["events"]):03d}-{args.action}'

            def invoke(script, flags):
                command = [data.get('python', sys.executable), str(SCRIPTS/script), *map(str, flags)]
                log = root/f'{len(data["events"]):03d}-{Path(script).stem}.log'
                child_env = os.environ.copy()
                env_overrides = {}
                if c.get('pending_assets'):
                    pending = str(path('pending_assets'))
                    from pending_assets import load_policy
                    load_policy(pending)
                    child_env['LANHU_PENDING_ASSETS'] = pending
                    env_overrides['LANHU_PENDING_ASSETS'] = pending
                record = {'argv':command, 'log':str(log), 'env_overrides':env_overrides}
                event.setdefault('commands', []).append(record)
                command_started = time.monotonic()
                with log.open('w') as stream:
                    run = subprocess.run(command, cwd=config.parent, env=child_env, stdout=stream,
                                         stderr=subprocess.STDOUT, timeout=900)
                record.update(returncode=run.returncode,
                              seconds=round(time.monotonic()-command_started, 3))
                if run.returncode:
                    raise ValueError(f'{script} returned {run.returncode}; see {log}')

            try:
                if args.action == 'prepare':
                    event['report'] = str(output/'summary.json')
                    evidence = [v for entry in c['evidence'] for v in ('--evidence', (config.parent/entry).resolve())]
                    invoke('prepare_page.py', [*evidence, '--reference', path('reference'),
                        '--manifest',path('manifest'),'--output',output,
                        *(['--font-map',path('font_map')] if c.get('font_map') else [])])
                    invoke('init_visual_contract.py', [*evidence,'--reference',path('reference'),
                        '--output',output/'draft.json','--name',c['name']])
                    inputs = [(config.parent / name).resolve() for name in c['evidence']]
                    inputs += [path(key) for key in
                               ('reference', 'manifest', 'font_map', 'pending_assets') if c.get(key)]
                    event['prepared_input_hashes'] = {str(p): sha256(p) for p in inputs}
                elif args.action == 'generate':
                    if not c.get('generated') or not c.get('class_name'):
                        raise ValueError('generate requires "generated" (Dart output) and "class_name" in the page config')
                    require_prepared_sources(data, c, config.parent)
                    plan = Path(next(e for e in reversed(data['events'])
                                     if e['action'] == 'prepare' and e.get('status') == 'OK')['report']).parent/'page-plan.json'
                    target = path('generated')
                    event['report'] = str(target.with_suffix('').with_suffix('.codegen.json'))
                    evidence = [v for entry in c['evidence'] for v in ('--evidence', (config.parent/entry).resolve())]
                    invoke('generate_flutter.py', [*evidence, '--plan', plan, '--class-name', c['class_name'],
                        '--output', target, '--report', event['report'], '--app-root', path('app'),
                        *(['--asset-dir', c['asset_dir']] if c.get('asset_dir') else []),
                        *(['--font-map', path('font_map')] if c.get('font_map') else [])])
                elif args.action == 'compile':
                    event['report'] = str(path('contract'))
                    invoke('compile_contract.py', ['--spec',path('spec'),'--output',path('contract')])
                elif args.action in ('validate', 'accept'):
                    require_prepared_sources(data, c, config.parent)
                    event['report'] = str(output/'run.json')
                    if c.get('renderer_kind') == 'custom':
                        if not c.get('renderer_capabilities'):
                            raise ValueError('Custom renderer requires renderer_capabilities; node presence does not prove paint support')
                        evidence = [v for entry in c['evidence'] for v in ('--evidence', (config.parent/entry).resolve())]
                        coverage_report = root/f'{len(data["events"]):03d}-renderer-coverage.json'
                        event['renderer_coverage_report'] = str(coverage_report)
                        invoke('renderer_capabilities.py', [*evidence, '--capabilities', path('renderer_capabilities'), '--output', coverage_report])
                    if args.action == 'accept':
                        invoke('compile_contract.py', ['--spec',path('spec'),'--output',path('contract')])
                    contract = read_json(path('contract'))
                    expected = c.get('scope', 'page')
                    if expected not in ('page','provided_nodes') or contract['source_scope']['kind'] != expected:
                        raise ValueError('Requested scope differs from contract; whole-page tasks cannot silently become local checks')
                    invoke('run_flutter.py', ['--contract',path('contract'),'--app',path('app'),
                        '--test',c['test'],'--output-env',c['output_env'],'--output',output,
                        '--task-log',root/'task-run.json','--round-note',args.note,
                        *(['--analyze',*c['analyze']] if c.get('analyze') else []),
                        *(['--build'] if args.build else [])])
                else:
                    prior = [e for e in data['events'][:-1] if e['action'] != 'finish']
                    latest = prior[-1] if prior else {}
                    if latest.get('action') not in ('validate', 'accept') or latest.get('status') != 'OK' or not args.note.strip():
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
            result = {'action':event, **data['summary']} if args.verbose else compact_result(data,root,event)
            print(json.dumps(result, ensure_ascii=False))
            return 0 if event['status'] == 'OK' else 2
    except (ValueError,OSError,KeyError) as exc:
        print(json.dumps({'status':'SESSION_ERROR','error':str(exc)},ensure_ascii=False)); return 2


if __name__ == '__main__':
    raise SystemExit(main())
