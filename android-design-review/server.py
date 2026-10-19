"""Local Android design review workbench. Bind only to loopback."""
import argparse
import base64
import csv
import hashlib
import html
import io
import json
import mimetypes
import os
import re
import secrets
import shutil
import subprocess
import tempfile
import threading
import uuid
import zipfile
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit, unquote

import capture
import ai_review
from catalog_rules import is_screen
from preview import PreviewStore
from virtual_devices import VirtualDevices, MAX_APK
from imaging import (compare, finite_number, node_matches, normalize, numbered_comparison,
                     png_bytes, read_image, validate_calibration, validate_rect, numbered_capture)

ROOT = Path(__file__).resolve().parent
WORKSPACE = ROOT.parent
DATA = Path(os.environ.get('REVIEW_DATA_DIR', ROOT / '.data')).resolve()
TOKEN = secrets.token_urlsafe(32)
LOCK = threading.RLock()
PORT = 8769
PREVIEW = PreviewStore()
VIRTUAL = VirtualDevices(DATA)
PROJECT_JOBS = {}
PROJECT_JOB_KEYS = {}
PROJECT_JOB_LOCK = threading.RLock()
LANHU_CLIENT_PYTHON = Path(os.environ.get(
    'LANHU_CLIENT_PYTHON',
    str(WORKSPACE / '.venv/bin/python'),
))


def now():
    return datetime.now(timezone.utc).isoformat()


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + '.' + uuid.uuid4().hex + '.tmp')
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False))
    temp.replace(path)


def read_json(path):
    return json.loads(path.read_text())


def identifier(value):
    if not isinstance(value,str) or not re.fullmatch(r'[a-zA-Z0-9_-]{1,80}',value):
        raise ValueError('无效的记录编号')
    return value


def design_path(key):
    path = DATA/'designs'/identifier(key)
    if not (path/'design.json').is_file():
        raise ValueError('设计基线不存在')
    return path


def run_path(key):
    path = DATA/'runs'/identifier(key)
    if not (path/'run.json').is_file():
        raise ValueError('验收记录不存在')
    return path


def run_thumbnail(key):
    """Cache a small preview without changing the original capture evidence."""
    path = run_path(key)
    with LOCK:
        target = path/'thumbnail.png'
        if not target.is_file():
            image = read_image((path/'original.png').read_bytes())
            image.thumbnail((240, 520))
            target.write_bytes(png_bytes(image))
    return target


def import_design(snapshot, image_data, name=None, key=None, demo_candidate=None):
    if not isinstance(snapshot,dict) or not snapshot.get('snapshot_id') or not snapshot.get('resolved_version'):
        raise ValueError('蓝湖 JSON 必须包含 snapshot_id 和 resolved_version')
    canvas = snapshot.get('canvas') or {}
    canvas = {k: finite_number(canvas.get(k), 1, 8000, '画布'+k) for k in ('width','height')}
    image = read_image(image_data)
    normalize(image, image.size, canvas, {'scale_percent':100})
    node_list = snapshot.get('nodes', [])
    if not isinstance(node_list,list) or len(node_list)>10000:
        raise ValueError('节点清单格式不正确或超过 10000 个节点')
    nodes = {n['node_id']: n for n in node_list if isinstance(n,dict) and n.get('node_id')}
    key = identifier(key or uuid.uuid4().hex)
    path = DATA/'designs'/key
    if path.exists():
        if not (path/'thumbnail.png').exists():
            thumb=read_image((path/'reference.png').read_bytes());thumb.thumbnail((240,520))
            (path/'thumbnail.png').write_bytes(png_bytes(thumb))
        return read_json(path/'design.json')
    path.mkdir(parents=True)
    normalized_bytes = png_bytes(image)
    (path/'reference.png').write_bytes(normalized_bytes)
    (path/'source-image.bin').write_bytes(image_data)
    thumb=image.copy();thumb.thumbnail((240,520))
    (path/'thumbnail.png').write_bytes(png_bytes(thumb))
    write_json(path/'snapshot.json',snapshot)
    design = {'id':key, 'name':name or snapshot.get('design_name','未命名画板'),
              'project':snapshot.get('project_name','蓝湖已存快照'), 'canvas':canvas,
              'snapshot_id':snapshot['snapshot_id'], 'version':snapshot['resolved_version'],
              'design_id':snapshot.get('design_id'), 'source_url':snapshot.get('source_url'),
              'node_count':len(nodes), 'total_nodes':snapshot.get('total_nodes'),
              'complete_nodes':len(nodes)==snapshot.get('total_nodes'),
              'reference_sha256':hashlib.sha256(normalized_bytes).hexdigest(),
              'original_source_sha256':hashlib.sha256(image_data).hexdigest(),
              'snapshot_sha256':hashlib.sha256((path/'snapshot.json').read_bytes()).hexdigest(),
              'reference_size':[image.width,image.height], 'created_at':now(),
              'demo_available':bool(demo_candidate)}
    if demo_candidate:
        (path/'demo.png').write_bytes(Path(demo_candidate).read_bytes())
    write_json(path/'design.json',design)
    return design


def seed():
    DATA.mkdir(parents=True,exist_ok=True)
    current = ROOT/'evidence/wanqia-feed'
    if (current/'snapshot.json').exists():
        import_design(read_json(current/'snapshot.json'),(current/'reference.png').read_bytes(),key='wanqia-feed')
    project = ROOT/'evidence/project/catalog.json'
    if project.exists():
        for item in read_json(project)['items']:
            if item['kind']=='design':
                evidence=ROOT/item['evidence']
                import_design(read_json(evidence/'snapshot.json'),(evidence/'reference.png').read_bytes(),key=item['design_key'])
    demo = WORKSPACE/'design_evidence/message-backup-34'
    if (demo/'reference.png').exists():
        import_design(read_json(demo/'source/snapshot.json'),(demo/'reference.png').read_bytes(),
                      name='消息页 · 工作流程示例',key='demo-message',demo_candidate=demo/'r0/render.png')


def project_catalog():
    path=ROOT/'evidence/project/catalog.json'
    if not path.exists():return None
    source=read_json(path)
    items=[]
    for item in source['items']:
        if not is_screen(item):continue
        entry={k:item[k] for k in ('index','id','name','kind','design_key','width','height','sectors') if k in item}
        entry.update({'name':item['name'].splitlines()[0], 'source_name':item['name']})
        if item['kind']=='note':entry['body']=item['body']
        if item['kind']=='unavailable':entry['error']=item['error']
        if item['kind']=='design' and not (DATA/'designs'/item['design_key']/'design.json').exists():
            entry.update({'kind':'unavailable','error':'本地快照尚未导入，请重启工作台。'})
        items.append(entry)
    return {'project_name':source['project_name'],'source_url':source['source_url'],
            'total_designs':len(items),'items':items,'excluded_design_keys':[i['design_key'] for i in source['items'] if not is_screen(i) and i.get('design_key')]}


def validate_lanhu_url(value):
    if not isinstance(value,str) or not value.strip() or len(value)>2000:
        raise ValueError('请粘贴蓝湖项目链接')
    value=value.strip(); parsed=urlsplit(value)
    if parsed.scheme!='https' or parsed.username or parsed.password or parsed.hostname not in ('lanhuapp.com','www.lanhuapp.com'):
        raise ValueError('只支持 lanhuapp.com 的 HTTPS 项目链接')
    if 'pid=' not in value and not ('/link/' in parsed.path and 'sid=' in value):
        raise ValueError('链接中缺少项目 pid；邀请链接需要包含 sid')
    if 'docId=' in value:
        raise ValueError('这是需求文档链接，请复制 UI 设计项目的 stage 链接')
    return value


def project_key(url):
    match=re.search(r'(?:[?&#]|^)pid=([a-zA-Z0-9_-]{1,80})',url)
    if not match:raise ValueError('蓝湖项目链接中缺少 pid')
    return 'project-'+hashlib.sha256(match.group(1).encode()).hexdigest()[:20]


def normalize_catalog(source, key=None):
    items=[]
    for item in source.get('items',[]):
        if not is_screen(item):continue
        entry={field:item[field] for field in ('index','id','name','kind','design_key','width','height','sectors') if field in item}
        entry.update({'name':str(item.get('name','未命名页面')).splitlines()[0],
                      'source_name':str(item.get('name','未命名页面'))})
        if entry.get('kind')=='note':entry['body']=item.get('body',item.get('name',''))
        if entry.get('kind')=='unavailable':entry['error']=item.get('error','原稿暂不可用')
        if entry.get('kind')=='design' and not (DATA/'designs'/entry['design_key']/'design.json').exists():
            entry.update({'kind':'unavailable','error':'本地快照尚未导入'})
        items.append(entry)
    return {'id':key or project_key(source['source_url']),'project_name':source['project_name'],
            'source_url':source['source_url'],'total_designs':len(items),
            'items':items,'excluded_design_keys':list(set(source.get('excluded_design_keys',[])+[i['design_key'] for i in source.get('items',[]) if not is_screen(i) and i.get('design_key')]))}


def project_catalogs():
    catalogs=[];builtin=project_catalog()
    if builtin:catalogs.append(normalize_catalog(builtin))
    folder=DATA/'projects'
    if folder.exists():
        for path in sorted(folder.glob('*.json')):
            source=read_json(path);key=identifier(source.get('id',path.stem))
            if not any(c['id']==key for c in catalogs):catalogs.append(normalize_catalog(source,key))
    return catalogs


def run_lanhu_bridge(mode,url,output=None):
    url=validate_lanhu_url(url)
    if not LANHU_CLIENT_PYTHON.is_file():raise ValueError('蓝湖 MCP 客户端环境不可用')
    command=[str(LANHU_CLIENT_PYTHON),str(ROOT/'lanhu_bridge.py'),mode,'--url',url]
    if output:command.extend(['--output',str(output)])
    try:
        result=subprocess.run(command,cwd=ROOT,text=True,capture_output=True,timeout=120 if mode=='preview' else 1800)
    except subprocess.TimeoutExpired:raise ValueError('蓝湖 MCP 连接超时，请检查登录状态后重试')
    if result.returncode:
        detail=(result.stderr.strip().splitlines() or ['蓝湖 MCP 请求失败'])[-1][:400]
        raise ValueError('蓝湖 MCP 连接失败：'+detail)
    try:return json.loads(result.stdout)
    except json.JSONDecodeError:raise ValueError('蓝湖 MCP 返回的数据无法解析')


def preview_project(url):
    result=run_lanhu_bridge('preview',url)
    return {'project_name':result['project_name'],'source_url':result['source_url'],
            'total_designs':result['total_designs'],
            'designs':[{'index':d.get('index'),'id':d.get('id'),'name':str(d.get('name','')).splitlines()[0]}
                       for d in result.get('designs',[])]}


def associate_project(url, folder=None):
    url=validate_lanhu_url(url)
    if 'pid=' in url:
        key=project_key(url)
        existing=next((item for item in project_catalogs() if item['id']==key),None)
        if existing:return existing
    imports=DATA/'imports';imports.mkdir(parents=True,exist_ok=True)
    folder=Path(folder) if folder else Path(tempfile.mkdtemp(prefix='lanhu-',dir=imports))
    folder.mkdir(parents=True,exist_ok=True)
    succeeded=False
    try:
        result=run_lanhu_bridge('sync',url,folder);key=project_key(result['source_url']);items=[]
        for item in result.get('items',[]):
            if item.get('kind')=='design':
                bundle=folder/identifier(item['bundle'])
                snapshot=read_json(bundle/'snapshot.json')
                digest=hashlib.sha256((key+item['id']+snapshot['resolved_version']).encode()).hexdigest()[:24]
                design_key='lanhu-'+digest
                import_design(snapshot,(bundle/'reference.png').read_bytes(),item.get('name'),design_key)
                items.append({**item,'design_key':design_key})
            elif not is_screen(item):continue
            else:items.append({**item,'design_key':key+'-missing-'+hashlib.sha256(item['id'].encode()).hexdigest()[:12]})
        catalog={'id':key,'project_name':result['project_name'],'source_url':result['source_url'],
                 'total_designs':result['total_designs'],'items':items,'connected_at':now()}
        write_json(DATA/'projects'/(key+'.json'),catalog)
        succeeded=True
        return normalize_catalog(catalog,key)
    finally:
        # Keep an interrupted import so a retry can continue from downloaded pages.
        if succeeded:shutil.rmtree(folder,ignore_errors=True)


def resumable_import(url):
    imports=DATA/'imports';imports.mkdir(parents=True,exist_ok=True)
    for source in sorted(imports.glob('lanhu-*/source.json')):
        try:
            if read_json(source).get('source_url')==url:return source.parent
        except (ValueError,KeyError,FileNotFoundError,json.JSONDecodeError):
            pass
    folder=Path(tempfile.mkdtemp(prefix='lanhu-',dir=imports))
    write_json(folder/'source.json',{'source_url':url,'created_at':now()})
    return folder


def project_job_view(job):
    result={key:job.get(key) for key in ('id','project_id','status','created_at','updated_at','error','catalog')}
    progress=dict(job.get('progress') or {})
    path=Path(job['folder'])/'progress.json' if job.get('folder') else None
    if path and path.is_file():
        try:progress.update(read_json(path))
        except (ValueError,OSError,json.JSONDecodeError):pass
    result['progress']=progress
    return result


def start_project_job(url):
    url=validate_lanhu_url(url)
    key=project_key(url) if 'pid=' in url else 'pending-'+hashlib.sha256(url.encode()).hexdigest()[:20]
    existing=next((item for item in project_catalogs() if item['id']==key),None)
    if existing:
        return {'id':None,'project_id':key,'status':'complete','created_at':now(),'updated_at':now(),
                'error':'','catalog':existing,'progress':{'completed':existing['total_designs'],
                                                         'total':existing['total_designs'],'phase':'完成'}}
    with PROJECT_JOB_LOCK:
        active_id=PROJECT_JOB_KEYS.get(key);active=PROJECT_JOBS.get(active_id)
        if active and active.get('status') in ('queued','running'):return project_job_view(active)
        job_id=uuid.uuid4().hex;folder=resumable_import(url)
        job={'id':job_id,'project_id':key,'url':url,'folder':str(folder),'status':'queued',
             'created_at':now(),'updated_at':now(),'error':'','catalog':None,
             'progress':{'completed':len(list(folder.glob('*/snapshot.json'))),'phase':'等待同步'}}
        PROJECT_JOBS[job_id]=job;PROJECT_JOB_KEYS[key]=job_id

    def work():
        with PROJECT_JOB_LOCK:
            job['status']='running';job['updated_at']=now()
        try:
            catalog=associate_project(url,folder)
            with PROJECT_JOB_LOCK:
                job.update({'status':'complete','catalog':catalog,'project_id':catalog['id'],
                            'updated_at':now(),'progress':{'completed':catalog['total_designs'],
                                                           'total':catalog['total_designs'],'phase':'完成'}})
        except Exception as error:
            with PROJECT_JOB_LOCK:
                job.update({'status':'error','error':str(error)[:600],'updated_at':now()})
                if PROJECT_JOB_KEYS.get(key)==job_id:PROJECT_JOB_KEYS.pop(key,None)

    threading.Thread(target=work,name='lanhu-project-'+job_id[:8],daemon=True).start()
    return project_job_view(job)


def get_project_job(key):
    key=identifier(key)
    with PROJECT_JOB_LOCK:
        job=PROJECT_JOBS.get(key)
        if not job:raise ValueError('同步任务不存在或服务已重启，请重新关联')
        return project_job_view(job)


def view_run(record):
    result = dict(record)
    result['design'] = read_json(design_path(record['design_id'])/'design.json')
    result['original_url'] = '/files/runs/'+record['id']+'/original.png'
    result['reference_url'] = '/files/designs/'+record['design_id']+'/reference.png'
    return result


def create_run(design_id, raw, metadata, kind, title='', previous_id=None):
    design = read_json(design_path(design_id)/'design.json')
    image = read_image(raw)
    key = uuid.uuid4().hex
    path = DATA/'runs'/key
    path.mkdir(parents=True)
    # Raw bytes are retained separately; the viewer always reads a decoded PNG.
    (path/'original.bin').write_bytes(raw)
    (path/'original.png').write_bytes(png_bytes(image))
    previous = read_json(run_path(previous_id)/'run.json') if previous_id else None
    if previous and previous['design_id'] != design_id:
        raise ValueError('复测必须使用相同设计基线')
    record = {'id':key,'design_id':design_id,'title':str(title or design['name'])[:120],
              'kind':kind,'created_at':now(),'updated_at':now(),'revision':0,
              'capture':metadata,'raw_sha256':hashlib.sha256(raw).hexdigest(),
              'image_size':[image.width,image.height], 'previous_id':previous_id,
              'calibration':{'scale_percent':100,'offset_x':0,'offset_y':0,'confirmed':False},
              'threshold':28,'issues':[],'exclusions':[],'comparison':None}
    if previous:
        record['calibration'] = {**previous['calibration'],'confirmed':False}
        # Reuse mapping only on equal screenshot sizes; otherwise force width-fit defaults.
        if previous['image_size'] != record['image_size']:
            record['calibration'] = {'scale_percent':100,'offset_x':0,'offset_y':0,'confirmed':False}
        record['issues'] = [{**issue,'status':'待复测','previous_status':issue['status']} for issue in previous['issues']]
        for issue in record['issues']:
            if issue.get('coordinate_space')=='image' and previous['image_size']!=record['image_size']:
                sx=image.width/previous['image_size'][0]; sy=image.height/previous['image_size'][1]
                rect=issue['rect']
                issue['rect']={'x':rect['x']*sx,'y':rect['y']*sy,
                               'width':max(.1,rect['width']*sx),'height':max(.1,rect['height']*sy)}
        record['exclusions'] = previous['exclusions']
    write_json(path/'run.json',record)
    return view_run(record)


def save_run(key, body):
    path=run_path(key); record=read_json(path/'run.json')
    if body.get('revision') != record['revision']:
        raise ValueError('记录已在其他窗口更新，请刷新后再编辑。')
    design=read_json(design_path(record['design_id'])/'design.json'); canvas=design['canvas']
    calibration=validate_calibration(body.get('calibration', record['calibration']))
    issues=[]
    for raw in body.get('issues',[])[:300]:
        if raw.get('priority') not in ('P1','P2','P3') or raw.get('status') not in ('待确认','已确认','已修复','待复测','复测通过','不处理'):
            raise ValueError('问题优先级或状态无效')
        space=raw.get('coordinate_space','source_canvas')
        kind=raw.get('annotation_type','rect')
        if space not in ('source_canvas','image') or kind not in ('rect','point'):
            raise ValueError('标注坐标或类型无效')
        bounds={'width':record['image_size'][0],'height':record['image_size'][1]} if space=='image' else canvas
        issues.append({'id':identifier(raw['id']), 'rect':validate_rect(raw['rect'],bounds),
                       'coordinate_space':space, 'annotation_type':kind,
                       'review_kind':'state_hint' if raw.get('review_kind')=='state_hint' else 'issue',
                       'title':str(raw.get('title') or '未命名问题')[:200], 'note':str(raw.get('note',''))[:4000],
                       'priority':raw['priority'],'status':raw['status'],
                       'node_id':str(raw.get('node_id',''))[:200], 'node_label':str(raw.get('node_label',''))[:200]})
        if raw.get('bubble_offset') is not None:
            offset=raw['bubble_offset']
            if not isinstance(offset,dict): raise ValueError('气泡位置无效')
            # Fractions of the screenshot dimensions keep placement on resize/retest.
            issues[-1]['bubble_offset']={axis:finite_number(offset.get(axis),-20,20,'气泡位置') for axis in ('x','y')}
    exclusions=[]
    for raw in body.get('exclusions',[])[:100]:
        reason=str(raw.get('reason','')).strip()[:500]
        if not reason: raise ValueError('排除区域需要原因')
        exclusions.append({'id':identifier(raw['id']),'rect':validate_rect(raw['rect'],canvas),'reason':reason})
    threshold=finite_number(body.get('threshold',record['threshold']),1,255,'差异阈值')
    invalidated=calibration!=record['calibration'] or exclusions!=record['exclusions'] or threshold!=record['threshold']
    record.update({'issues':issues,'exclusions':exclusions,'calibration':calibration,'threshold':threshold,
                   'title':str(body.get('title',record['title']))[:120], 'updated_at':now(),'revision':record['revision']+1})
    applied=body.get('ai_applied_ids',record.get('ai_applied_ids',[]))
    if not isinstance(applied,list) or len(applied)>300: raise ValueError('AI 标注记录无效')
    record['ai_applied_ids']=list(dict.fromkeys(identifier(x) for x in applied))
    completed=body.get('ai_result_attempt')
    if completed:
        completed=identifier(completed)
        pending=record.get('ai_reanalysis')
        if pending and pending['attempt_id']==completed:
            record.pop('ai_reanalysis')
            record['ai_result_attempt']=completed
        elif pending or record.get('ai_result_attempt')!=completed:
            raise ValueError('这轮分析结果已过期，请刷新后重试。')
    if invalidated: record['comparison']=None
    write_json(path/'run.json',record)
    return view_run(record)


AI_JOBS = {}
AI_JOB_LOCK = threading.RLock()
AI_SLOTS = threading.BoundedSemaphore(3)

def ai_status(key):
    run_path(key)  # validate the record identifier
    with AI_JOB_LOCK:
        return dict(AI_JOBS.get(key, {'status':'idle','run_id':key}))

def is_ai_annotation(issue, applied=()):
    return str(issue.get('id','')).startswith('ai-') or issue.get('id') in applied or issue.get('node_label')=='Codex 视觉分析'

def restore_ai_annotations(key, attempt):
    # Use the same lock order as start_ai. Preserve the latest manual edits.
    with AI_JOB_LOCK, LOCK:
        active=AI_JOBS.get(key,{})
        if active.get('status') in ('queued','running'):
            raise ValueError('分析仍在进行，请等待本轮结束。')
        path=run_path(key);record=read_json(path/'run.json');backup=record.get('ai_reanalysis')
        if not backup:return view_run(record)
        if backup['attempt_id']!=attempt:raise ValueError('这轮分析已过期，请刷新后重试。')
        manual=[i for i in record['issues'] if not is_ai_annotation(i,record.get('ai_applied_ids',[]))]
        record.update(issues=manual+backup['issues'],ai_applied_ids=backup['ai_applied_ids'],
                      ai_result_attempt=backup.get('previous_result_attempt',''),revision=record['revision']+1,updated_at=now())
        record.pop('ai_reanalysis')
        write_json(path/'run.json',record)
        return view_run(record)

def recover_interrupted_ai():
    # A durable backup also covers a service restart or a browser closed mid-task.
    for path in (DATA/'runs').glob('*/run.json'):
        record=read_json(path)
        if record.get('ai_reanalysis'):
            restore_ai_annotations(record['id'],record['ai_reanalysis']['attempt_id'])

def start_ai(key, options=None):
    options=options or {}
    model,effort=ai_review.selection(options.get("model"),options.get("effort"))
    speed=ai_review.speed_selection(model,options.get("speed"))
    region=ai_review.validate_region(options.get("region"))
    reference_region=ai_review.validate_region(options.get("reference_region"))
    if reference_region and not region:raise ValueError("请同时框选截图范围")
    with AI_JOB_LOCK, LOCK:
        if AI_JOBS.get(key,{}).get('status') in ('running','queued'):return dict(AI_JOBS[key])
        path=run_path(key);record=read_json(path/'run.json');dp=design_path(record['design_id'])
        design=read_json(dp/'design.json')
        if design.get('kind'):raise ValueError('请选择界面设计原稿再分析。')
        if not ai_review.codex_path():raise ValueError('未找到本机 Codex，请先安装并登录。')
        context={'speed':speed,'analysis_region':region,'reference_region':reference_region,
                 'design_canvas':design['canvas'],'screenshot_size':record['image_size'],
                 'page':{'design_name':design.get('name'),'project_name':design.get('project')},
                 'display':ai_review.environment_context(record.get('capture') or {},record['image_size'])}
        attempt=uuid.uuid4().hex
        signature=hashlib.sha256((dp/'reference.png').read_bytes()+(path/'original.png').read_bytes()+
            (model+':'+effort+':'+speed+':'+ai_review.POLICY_VERSION+':'+json.dumps(context,sort_keys=True)+':'+attempt).encode()).hexdigest()
        cache=path/('ai-result-'+signature[:20]+'.json')
        applied=record.get('ai_applied_ids',[])
        # Carry an uncommitted backup forward if a previous attempt failed or was
        # never opened. A second attempt must not overwrite that recovery data.
        backup=record.get('ai_reanalysis') or {'issues':[i for i in record['issues'] if is_ai_annotation(i,applied)],
            'ai_applied_ids':applied,'previous_result_attempt':record.get('ai_result_attempt','')}
        record.update(issues=[i for i in record['issues'] if not is_ai_annotation(i,applied)],
                      ai_applied_ids=[],ai_result_attempt='',ai_reanalysis={**backup,'attempt_id':attempt},
                      revision=record['revision']+1,updated_at=now())
        write_json(path/'run.json',record)
        cleared=view_run(record)
        job={'status':'queued','stage':'queued','title':design.get('name') or record.get('title') or key[:8],'run_id':key,'signature':signature,'attempt_id':attempt,'replaces_ai':True,'speed':speed,'region':region,'reference_region':reference_region,'model':model,'effort':effort,'submitted_at':now(),'started_at':now()}
        AI_JOBS[key]=job
        context['existing_issues']=[i.get('note') or i['title'] for i in record['issues']]
        metrics={}
        def progress(stage):
            # Never expose region candidates as editable annotations before verdict.
            updates={'stage':stage,'completed_regions':list(metrics.get('completed_regions',[]))}
            with AI_JOB_LOCK:
                AI_JOBS[key]={**AI_JOBS[key],**updates}
        def work():
            with AI_SLOTS:
                execute()
        def execute():
            with AI_JOB_LOCK:
                job.update(status='running',stage='preparing',started_at=now())
                AI_JOBS[key]=dict(job)
            try:
                metrics.update(queue_seconds=round((datetime.fromisoformat(job['started_at'])-datetime.fromisoformat(job['submitted_at'])).total_seconds(),3))
                result=ai_review.review(dp/'reference.png',path/'original.png',context,model,effort,progress,metrics)
                issues=ai_review.annotations(result,record['image_size'],signature)
                if region:
                    w,h=record['image_size'];issues=[i for i in issues if region['x']<=i['rect']['x']/w<=region['x']+region['width'] and region['y']<=i['rect']['y']/h<=region['y']+region['height']]
                done={**job,'status':'done','stage':'done','issues':issues,'same_screen':result['same_screen'],
                      'summary':str(result.get('summary',''))[:1000],'state_differences':[str(x)[:300] for x in result.get('state_differences',[])[:20]],'coverage':result.get('coverage',{}),'comparison_basis':result.get('comparison_basis',{}),'review_audit':result.get('review_audit',[]),'metrics':metrics,'policy_version':ai_review.POLICY_VERSION,'finished_at':now()}
                with AI_JOB_LOCK:
                    write_json(cache,done);AI_JOBS[key]=done
            except Exception as error:
                message=str(error) if isinstance(error,ValueError) else 'AI 分析失败，请重试；已有标注未改变。'
                with AI_JOB_LOCK:AI_JOBS[key]={**AI_JOBS[key],'status':'error','error':message,'metrics':metrics,'finished_at':now()}
        threading.Thread(target=work,daemon=True,name='visual-review').start()
        return {**job,'run':cleared}


def analyze(key):
    path=run_path(key); record=read_json(path/'run.json')
    if not record['calibration']['confirmed']:
        raise ValueError('请先确认页面状态一致，并完成画面校准。')
    dp=design_path(record['design_id']); design=read_json(dp/'design.json'); snapshot=read_json(dp/'snapshot.json')
    reference=read_image((dp/'reference.png').read_bytes()); candidate=read_image((path/'original.png').read_bytes())
    normalized,heat,stats=compare(reference,candidate,design['canvas'],record['calibration'],record['threshold'],record['exclusions'],snapshot['nodes'])
    (path/'aligned.png').write_bytes(png_bytes(normalized));(path/'difference.png').write_bytes(png_bytes(heat))
    record.update({'comparison':stats,'updated_at':now(),'revision':record['revision']+1})
    write_json(path/'run.json',record)
    return view_run(record)


def export_run(key):
    path=run_path(key); record=read_json(path/'run.json'); dp=design_path(record['design_id']); design=read_json(dp/'design.json')
    reference=read_image((dp/'reference.png').read_bytes()); candidate=read_image((path/'original.png').read_bytes())
    normalized,_=normalize(candidate,reference.size,design['canvas'],record['calibration'])
    marked=png_bytes(numbered_capture(reference,candidate,record['issues'],design['canvas'],record['calibration']))
    esc=lambda value:html.escape(str(value))
    rows=''.join('<tr>'+''.join('<td>'+esc(v)+'</td>' for v in [i,issue['title'],issue['priority'],issue['status'],issue['note'],issue['node_id']])+'</tr>' for i,issue in enumerate(record['issues'],1))
    metadata={'run':record,'design':design,'scope':'视觉诊断及人工标注；不是全页自动验收结论。','coordinate_unit':'每条标注的 coordinate_space：image 为原始截图像素，source_canvas 为设计画布坐标；不默认等于 dp。'}
    encoded=base64.b64encode(marked).decode()
    report='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>设计验收记录</title><style>body{font:14px/1.7 system-ui;margin:32px auto;padding:0 24px;max-width:1200px;color:#23333c}table{width:100%;border-collapse:collapse}td,th{border:1px solid #dce3e7;padding:10px;text-align:left;white-space:pre-wrap}img{width:100%;height:auto}pre{white-space:pre-wrap;word-break:break-all}.notice{background:#fff5e8;padding:16px;border-radius:10px}</style>'''
    report+='<h1>'+esc(record['title'])+'</h1><p>'+esc(record['created_at'])+' · '+esc(record['kind'])+'</p><p class="notice">'+esc(metadata['scope'])+' 页面状态与校准确认：'+('已确认' if record['calibration']['confirmed'] else '未确认')+'。排除区域：'+str(len(record['exclusions']))+'。</p>'
    report+='<img alt="设计与截图编号对照" src="data:image/png;base64,'+encoded+'"><h2>问题清单</h2><table><tr><th>编号</th><th>问题</th><th>优先级</th><th>状态</th><th>说明</th><th>蓝湖节点</th></tr>'+rows+'</table><details><summary>原始证据、排除范围与设备信息</summary><pre>'+esc(json.dumps(metadata,ensure_ascii=False,indent=2))+'</pre></details></html>'
    csv_out=io.StringIO(); writer=csv.writer(csv_out);writer.writerow(['编号','问题','优先级','状态','说明','蓝湖节点'])
    for i,item in enumerate(record['issues'],1):
        values=[i,item['title'],item['priority'],item['status'],item['note'],item['node_id']]
        writer.writerow(["'"+v if isinstance(v,str) and v.lstrip().startswith(('=','+','-','@')) else v for v in values])
    output=io.BytesIO()
    with zipfile.ZipFile(output,'w',zipfile.ZIP_DEFLATED) as archive:
        archive.writestr('report.html',report);archive.writestr('annotated.png',marked)
        archive.writestr('issues.csv',csv_out.getvalue().encode('utf-8-sig'))
        archive.writestr('evidence.json',json.dumps(metadata,ensure_ascii=False,indent=2))
        archive.writestr('reference.png',png_bytes(reference));archive.writestr('aligned.png',png_bytes(normalized))
        archive.writestr('original.png',(path/'original.png').read_bytes())
        archive.writestr('original.bin',(path/'original.bin').read_bytes())
        archive.writestr('source-snapshot.json',(dp/'snapshot.json').read_bytes())
        if record.get('comparison') and (path/'difference.png').exists(): archive.write(path/'difference.png','difference.png')
    return output.getvalue()


def decode_upload(value):
    if not isinstance(value,str) or not value.startswith(('data:image/png;base64,','data:image/jpeg;base64,')):
        raise ValueError('请选择 PNG 或 JPEG 图片')
    try: return base64.b64decode(value.split(',',1)[1],validate=True)
    except ValueError: raise ValueError('图片编码不正确')


class Handler(BaseHTTPRequestHandler):
    def log_message(self,fmt,*args):
        if not any(p in str(args) for p in ('/api/devices', '/api/preview/frame')): super().log_message(fmt,*args)

    def guard(self,mutation=False):
        allowed={'127.0.0.1:'+str(PORT),'localhost:'+str(PORT)}
        if self.headers.get('Host') not in allowed: raise PermissionError('只允许本机访问')
        origin=self.headers.get('Origin')
        if origin and origin not in {'http://'+host for host in allowed}: raise PermissionError('禁止跨站访问本地设备')
        if mutation and self.headers.get('X-Review-Token')!=TOKEN: raise PermissionError('会话已失效，请刷新工作台')

    def respond(self,data,status=200,content_type='application/json; charset=utf-8',download=None):
        if isinstance(data,(dict,list)): data=json.dumps(data,ensure_ascii=False,allow_nan=False).encode()
        elif isinstance(data,str): data=data.encode()
        self.send_response(status);self.send_header('Content-Type',content_type)
        self.send_header('Content-Length',str(len(data)));self.send_header('Cache-Control','no-store')
        self.send_header('X-Content-Type-Options','nosniff');self.send_header('Referrer-Policy','no-referrer')
        if download:self.send_header('Content-Disposition','attachment; filename="'+download+'"')
        self.end_headers();self.wfile.write(data)

    def do_GET(self):
        try:
            self.guard(); path=unquote(urlsplit(self.path).path)
            if path=='/api/bootstrap':
                designs=[read_json(p) for p in sorted((DATA/'designs').glob('*/design.json'))]
                designs.sort(key=lambda d:d['id'].startswith('demo'))
                runs=[read_json(p) for p in (DATA/'runs').glob('*/run.json')]
                runs.sort(key=lambda r:r['created_at'],reverse=True)
                projects=project_catalogs()
                return self.respond({'token':TOKEN,'designs':designs,'runs':runs,
                                     'projects':projects,'catalog':projects[0] if projects else None})
            if path=='/api/ai/jobs':
                with AI_JOB_LOCK: return self.respond({'jobs':[dict(j) for j in AI_JOBS.values()]})
            if path=='/api/ai/models': return self.respond({'models':ai_review.models()})
            if path=='/api/devices': return self.respond(capture.devices())
            if path=='/api/virtual': return self.respond(VIRTUAL.status())
            if path.startswith('/api/projects/jobs/'):
                return self.respond(get_project_job(path.split('/')[-1]))
            if path.startswith('/api/runs/'):
                parts=path.split('/');key=identifier(parts[3])
                if len(parts)==5 and parts[4]=='ai':return self.respond(ai_status(key))
                if len(parts)==5 and parts[4]=='export':return self.respond(export_run(key),content_type='application/zip',download='design-review-'+key[:8]+'.zip')
                if len(parts)==4:return self.respond(view_run(read_json(run_path(key)/'run.json')))
            if path.startswith('/api/designs/'):
                key=identifier(path.split('/')[-1]); dp=design_path(key)
                return self.respond({'design':read_json(dp/'design.json'),'nodes':read_json(dp/'snapshot.json')['nodes']})
            if path.startswith('/files/'):
                parts=path.split('/')
                if len(parts)!=5 or parts[2] not in ('runs','designs') or parts[4] not in ('reference.png','thumbnail.png','original.png','aligned.png','difference.png'):
                    raise ValueError('文件路径无效')
                file=DATA/parts[2]/identifier(parts[3])/parts[4]
                if parts[2]=='runs' and parts[4]=='thumbnail.png':
                    file=run_thumbnail(parts[3])
            else:
                relative='index.html' if path=='/' else path.lstrip('/')
                file=(ROOT/'static'/relative).resolve()
                if ROOT/'static' not in file.parents: raise PermissionError('文件路径无效')
            if not file.is_file():return self.respond({'error':'文件不存在'},404)
            return self.respond(file.read_bytes(),content_type=mimetypes.guess_type(file.name)[0] or 'application/octet-stream')
        except PermissionError as error:self.respond({'error':str(error)},403)
        except (ValueError,KeyError,FileNotFoundError) as error:self.respond({'error':str(error)},400)
        except Exception as error:
            print(type(error).__name__,str(error));self.respond({'error':'服务处理失败，请检查终端日志。'},500)

    def stream_preview(self, key):
        # Validate before sending headers. The authenticated POST keeps tokens out of URLs.
        with PREVIEW.lock:
            PREVIEW._get(key)
        self.send_response(200)
        self.send_header('Content-Type', 'application/x-ndjson')
        self.send_header('Cache-Control', 'no-store')
        self.send_header('Connection', 'close')
        self.end_headers()
        self.close_connection = True
        self.connection.settimeout(5)
        try:
            while True:
                packet = PREVIEW.next_frame(key)
                self.wfile.write(json.dumps(packet, ensure_ascii=False).encode() + b'\n')
                self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError, TimeoutError, OSError):
            pass
        except (ValueError, KeyError) as error:
            try:
                self.wfile.write(json.dumps({'error': str(error)}).encode() + b'\n')
                self.wfile.flush()
            except OSError:
                pass

    def do_POST(self):
        try:
            self.guard(True)
            path=unquote(urlsplit(self.path).path)
            if path=='/api/virtual/upload':
                length=int(self.headers.get('Content-Length',0))
                if not 0 < length <= MAX_APK: raise ValueError('APK 需要小于 1 GB')
                self.connection.settimeout(120)
                return self.respond(VIRTUAL.import_apk(self.rfile,length,unquote(self.headers.get('X-File-Name','开发包.apk'))))
            if self.headers.get('Content-Type','').split(';')[0]!='application/json':raise ValueError('需要 JSON 请求')
            length=int(self.headers.get('Content-Length',0))
            if length<1 or length>45_000_000:raise ValueError('请求大小超出限制（45 MB）')
            body=json.loads(self.rfile.read(length));path=unquote(urlsplit(self.path).path)
            if not isinstance(body,dict):raise ValueError('请求必须为 JSON 对象')
            if path=='/api/virtual/settings': return self.respond(VIRTUAL.save_device_settings(body))
            if path=='/api/virtual/jobs': return self.respond(VIRTUAL.submit(body.get('operation'),body))
            if path=='/api/virtual/cancel': return self.respond(VIRTUAL.cancel())
            if path=='/api/virtual/control': return self.respond(VIRTUAL.control(body))
            if path=='/api/virtual/collect': return self.respond(VIRTUAL.collect(body.get('device')))
            if path=='/api/projects/preview':return self.respond(preview_project(body.get('url')))
            if path=='/api/projects':return self.respond(start_project_job(body.get('url')))
            # Preview I/O never holds the record lock and never writes screenshots to disk.
            if path=='/api/preview/start':return self.respond(PREVIEW.start(body['device']))
            if path=='/api/preview/stream':return self.stream_preview(body['session_id'])
            if path=='/api/preview/frame':return self.respond(PREVIEW.next_frame(body['session_id']))
            if path=='/api/preview/stop':
                PREVIEW.stop(body['session_id']);return self.respond({'stopped':True})
            if path=='/api/capture':
                if VIRTUAL.active and body.get('device')==VIRTUAL.active['serial'] and VIRTUAL.job and VIRTUAL.job.get('status')=='running':
                    raise ValueError('设备配置正在切换，请等待预览恢复后截图。')
                design_path(body['design_id'])
                if body.get('preview_session'):
                    raw,metadata=PREVIEW.freeze(body['preview_session'],body['frame_id'],body['device'])
                else:
                    raw,metadata=capture.capture(body['device'])
                virtual=VIRTUAL.evidence(body['device'])
                if virtual: metadata['review_context']=virtual
                with LOCK:
                    result=create_run(body['design_id'],raw,metadata,'emulator' if virtual else 'device',body.get('title'),body.get('previous_id'))
                return self.respond(result)
            if path.startswith('/api/runs/') and path.endswith('/ai'):
                parts=path.split('/')
                if len(parts)!=5:raise ValueError('路径无效')
                return self.respond(start_ai(identifier(parts[3]),body))
            if path.startswith('/api/runs/') and path.endswith('/ai-restore'):
                parts=path.split('/')
                if len(parts)!=5:raise ValueError('路径无效')
                return self.respond(restore_ai_annotations(identifier(parts[3]),identifier(body['attempt_id'])))
            with LOCK:
                if path=='/api/import':
                    return self.respond(create_run(body['design_id'],decode_upload(body['image']),{'method':'manual import','device_metadata':'not supplied'},'import',body.get('title'),body.get('previous_id')))
                if path=='/api/demo':
                    dp=design_path('demo-message')
                    return self.respond(create_run('demo-message',(dp/'demo.png').read_bytes(),{'method':'existing Flutter test render','notice':'历史流程样例，并非当前 APK 或安卓设备截图'},'demo','消息页 · 流程演示'))
                if path=='/api/designs':return self.respond(import_design(body['snapshot'],decode_upload(body['image']),body.get('name')))
                if path.startswith('/api/runs/'):
                    parts=path.split('/');key=identifier(parts[3])
                    if len(parts)==5 and parts[4]=='compare':return self.respond(analyze(key))
                    if len(parts)==4:return self.respond(save_run(key,body))
                self.respond({'error':'接口不存在'},404)
        except PermissionError as error:self.respond({'error':str(error)},403)
        except (ValueError,KeyError,FileNotFoundError) as error:self.respond({'error':str(error)},400)
        except Exception as error:
            print(type(error).__name__,str(error));self.respond({'error':'服务处理失败，请检查终端日志。'},500)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--port',type=int,default=8769)
    parser.add_argument('--import-snapshot');parser.add_argument('--reference');parser.add_argument('--name')
    args=parser.parse_args();seed();recover_interrupted_ai()
    if args.import_snapshot:
        print(json.dumps(import_design(read_json(Path(args.import_snapshot)),Path(args.reference).read_bytes(),args.name),ensure_ascii=False))
    else:
        PORT=args.port
        server=ThreadingHTTPServer(('127.0.0.1',PORT),Handler)
        print('Local: http://127.0.0.1:'+str(PORT),flush=True)
        try:server.serve_forever()
        except KeyboardInterrupt:server.server_close()
