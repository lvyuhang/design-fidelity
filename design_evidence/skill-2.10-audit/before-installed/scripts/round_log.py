"""Persistent visual rounds. Revalidating identical inputs is a separate attempt."""
from __future__ import annotations
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import html
import json
import os
from pathlib import Path
import time
import uuid

from fidelity_contract import read_json, sha256


def input_signature(contract_path):
    c = read_json(contract_path)
    paths = {c.get('reference'), *c.get('source_documents', []),
             *c.get('assets', []), *c.get('implementation_inputs', []),
             *(f.get('path') for f in c.get('fonts', [])), *c.get('pinned_files', {})}
    hashes = {}
    for p in sorted(x for x in paths if x):
        f = contract_path.parent / p
        hashes[p] = sha256(f) if f.is_file() else 'MISSING'
    signature = hashlib.sha256(json.dumps({'contract':sha256(contract_path), 'inputs':hashes},
        sort_keys=True).encode()).hexdigest()
    identity = {'name':c.get('name'), 'snapshot':c.get('source_snapshot'),
                'version':c.get('source_version'), 'canvas':c.get('canvas')}
    return signature, identity, sha256(contract_path)


def utc(value):
    return datetime.fromtimestamp(value, timezone.utc).isoformat(timespec='seconds')


def summary(log):
    attempts = [a for r in log['rounds'] for a in r['attempts']]
    rounds = len(log['rounds'])
    return {'rounds': rounds, 'target_rounds': [2,3], 'validation_attempts':len(attempts),
            'repeat_attempts':len(attempts)-rounds, 'over_target':rounds > 3,
            'total_validation_seconds':round(sum(a.get('seconds',0) for a in attempts),3),
            'latest_status':attempts[-1]['status'] if attempts else 'NOT_STARTED',
            'tool_call_count':None,
            'timing_scope':'Validation execution only; excludes work before first validation and model editing time',
            'count_scope':'Tracked render/validation attempts only; not all model/tool calls or visual reviews'}


def render_html(log, destination):
    esc = lambda v: html.escape(str(v))
    s = summary(log)
    cards = []
    for r in log['rounds']:
        entries = []
        for a in r['attempts']:
            failure = '\n'.join(f"{f.get('check')}: {f.get('failures') or f.get('error') or ''}"
                                for f in a.get('failures',[]))
            details = failure or a.get('error') or '自动检查未报告失败；仍需最终视觉复查'
            entries.append(f'<tr><td>{a["attempt_number"]}</td><td>{esc(a["status"])}</td>'
                f'<td>{esc(a.get("gate_status") or "尚未验收")}</td><td>{esc(a.get("seconds", "运行中"))}</td>'
                f'<td>{esc(a["note"] or "未填写修改说明")}</td><td><pre>{esc(details)}</pre></td>'
                f'<td><a href="{esc(os.path.relpath(a["run_report"],destination.parent))}">run.json</a></td></tr>')
        cards.append(f'<section><h2>第 {r["round_number"]} 轮 · R{r["round_number"]-1}</h2>'
            f'<p>基线变更：{"是，请核对修改说明" if r["contract_changed"] else "否"}</p>'
            '<table><tr><th>尝试</th><th>运行状态</th><th>门禁结果</th><th>执行秒数</th>'
            '<th>本轮处理</th><th>发现/剩余问题</th><th>证据</th></tr>'+''.join(entries)+'</table></section>')
    warn = ('已超过 3 轮：需要记录原因并调整处理策略。验收门槛不变。' if s['over_target']
            else '目标：初版加修正共 2–3 轮；一次通过即可交付，无需凑轮数。')
    page = ('<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>任务运行日志</title>'
            '<style>body{font:15px/1.6 system-ui;max-width:1200px;margin:32px auto;padding:0 24px;background:#f5f6f8;color:#20252c}'
            'section,.summary{background:white;border-radius:12px;padding:20px;margin:16px 0}table{width:100%;border-collapse:collapse}'
            'td,th{text-align:left;vertical-align:top;padding:10px;border-bottom:1px solid #ddd}pre{white-space:pre-wrap;max-width:340px}'
            'h1{font-size:26px}.counts{font-size:22px;font-weight:650}a{color:#1563c5}</style>'
            f'<h1>{esc(log["identity"].get("name") or "页面")} · 任务运行日志</h1>'
            f'<div class="summary"><p class="counts">{s["rounds"]} 轮 / 目标 2–3 轮 · '
            f'{s["validation_attempts"]} 次验证 · {s["repeat_attempts"]} 次重复验证或重试</p>'
            f'<p>{warn}</p><p>验证累计执行：{s["total_validation_seconds"]} 秒。包含失败尝试；不代表整页开发耗时。</p>'
            '<p>初版计第 1 轮（R0）；输入改变后计新一轮，相同输入再次执行单列为尝试。工具调用总数未采集，不能用轮数代替。</p>'
            '<p>仅统计接入本日志后的运行，不补造之前未记录的轮次。自动门禁通过仍需视觉复查。</p></div>'
            +''.join(cards)+'</html>')
    destination.write_text(page, encoding='utf-8')


class RoundLog:
    def __init__(self, path):
        self.path = Path(path).resolve()

    @contextmanager
    def locked(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        lock = self.path.with_suffix(self.path.suffix+'.lock')
        try:
            fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        except FileExistsError:
            raise ValueError(f'Task log busy: {lock}; do not run the same page concurrently')
        try:
            os.close(fd)
            yield
        finally:
            lock.unlink()

    def save(self, data):
        data['summary'] = summary(data)
        temporary = self.path.with_suffix('.tmp')
        temporary.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
        temporary.replace(self.path)
        render_html(data, self.path.with_suffix('.html'))

    def begin(self, contract, output, note='', command=None):
        fingerprint, identity, contract_hash = input_signature(Path(contract).resolve())
        # A changed renderer/test is an implementation change even if code hashes agree.
        fingerprint = hashlib.sha256(json.dumps([fingerprint,command],sort_keys=True).encode()).hexdigest()
        with self.locked():
            data = read_json(self.path) if self.path.exists() else {
                'schema_version':1, 'task_id':str(uuid.uuid4()),'identity':identity,
                'created_at':utc(time.time()),'rounds':[]}
            if data['identity'] != identity:
                raise ValueError('Task log belongs to a different source page/version; use another log')
            if data['rounds'] and data['rounds'][-1]['attempts'][-1]['status']=='RUNNING':
                # Preserve an interrupted attempt rather than silently dropping it.
                previous = data['rounds'][-1]['attempts'][-1]
                if previous.get('pid'):
                    try:
                        os.kill(previous['pid'], 0)
                    except ProcessLookupError:
                        pass
                    except PermissionError:
                        raise ValueError('Previous logged attempt is still active')
                    else:
                        raise ValueError('Previous logged attempt is still active')
                if Path(previous['run_report']).is_file():
                    previous.update(self.result_fields(read_json(previous['run_report'])))
                else:
                    previous.update(status='INTERRUPTED', error='Previous attempt ended without run.json; duration unknown')
            if not data['rounds'] or data['rounds'][-1]['fingerprint'] != fingerprint:
                data['rounds'].append({'round_number':len(data['rounds'])+1,'fingerprint':fingerprint,
                    'contract_sha256':contract_hash,
                    'contract_changed':bool(data['rounds'] and data['rounds'][-1]['contract_sha256'] != contract_hash),
                    'attempts':[]})
            r = data['rounds'][-1]
            a = {'attempt_id':str(uuid.uuid4()),'attempt_number':len(r['attempts'])+1,
                 'started_at':utc(time.time()),'status':'RUNNING','note':note,'pid':os.getpid(),
                 'run_report':str(Path(output).resolve()/'run.json')}
            r['attempts'].append(a)
            self.save(data)
            return {'task_id':data['task_id'], 'round_number':r['round_number'],
                    'attempt_number':a['attempt_number'],'attempt_id':a['attempt_id'],
                    'target_rounds':[2,3], 'over_target':r['round_number']>3,
                    'log':str(self.path), 'html':str(self.path.with_suffix('.html'))}

    @staticmethod
    def result_fields(report):
        return {k:report[k] for k in ('status','seconds','gate_status','failures','error','failed_stage','stages','metrics') if k in report}

    def finish(self, ticket, report):
        with self.locked():
            data = read_json(self.path)
            for r in data['rounds']:
                for a in r['attempts']:
                    if a['attempt_id'] == ticket['attempt_id']:
                        a.update(self.result_fields(report))
                        a['finished_at'] = utc(time.time())
                        self.save(data)
                        return
            raise ValueError('Round attempt not found')
