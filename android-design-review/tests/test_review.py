import io
import json
import sys
import tempfile
import threading
import time
import unittest
import urllib.error
import urllib.request
import zipfile
from pathlib import Path
from unittest.mock import patch

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import capture
import server
from imaging import compare, normalize, png_bytes, validate_calibration


class ImageTests(unittest.TestCase):
    def test_width_fit_preserves_aspect_and_reports_uncovered_area(self):
        candidate=Image.new('RGB',(100,100),'red')
        image,coverage=normalize(candidate,(200,400),{'width':100,'height':200},{})
        self.assertEqual(image.size,(200,400))
        self.assertEqual(float(coverage.mean()),.5)
        self.assertEqual(image.getpixel((20,150)),(255,0,0))
        self.assertNotEqual(image.getpixel((20,300)),(255,0,0))

    def test_translation_in_design_units(self):
        candidate=Image.new('RGB',(100,100),'black')
        ImageDraw.Draw(candidate).rectangle((10,10,19,19),fill='white')
        aligned,_=normalize(candidate,(200,200),{'width':100,'height':100},{'offset_x':5})
        self.assertEqual(aligned.getpixel((32,25)),(255,255,255))
        self.assertEqual(aligned.getpixel((22,25)),(0,0,0))

    def test_difference_and_exact_exclusion(self):
        reference=Image.new('RGB',(200,200),'white'); candidate=reference.copy()
        ImageDraw.Draw(candidate).rectangle((60,60,79,79),fill='black')
        canvas={'width':100,'height':100}
        _,_,stats=compare(reference,candidate,canvas,{},28)
        self.assertGreater(stats['region_count'],0)
        self.assertEqual(stats['status'],'DIAGNOSTIC_ONLY')
        self.assertEqual(stats['changed_pixels'],400)
        _,_,excluded=compare(reference,candidate,canvas,{},28,[{'rect':{'x':30,'y':30,'width':10,'height':10},'reason':'固定的测试区域'}])
        self.assertEqual(excluded['changed_pixels'],0)
        self.assertEqual(excluded['excluded_fraction'],.01)
        self.assertEqual(candidate.getpixel((65,65)),(0,0,0))

    def test_reject_distorted_reference_and_invalid_calibration(self):
        with self.assertRaises(ValueError):normalize(Image.new('RGB',(100,100)),(200,300),{'width':100,'height':100},{})
        with self.assertRaises(ValueError):validate_calibration({'offset_x':float('nan')})
        with self.assertRaises(ValueError):validate_calibration({'scale_percent':0})


class RecordTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.old_data=server.DATA;server.DATA=Path(self.tmp.name)
        server.PROJECT_JOBS.clear();server.PROJECT_JOB_KEYS.clear()
        self.raw=png_bytes(Image.new('RGB',(200,200),'white'))
        self.snapshot={'snapshot_id':'test-snapshot','resolved_version':'test-version','canvas':{'width':100,'height':100},'nodes':[],'total_nodes':0}
        self.design=server.import_design(self.snapshot,self.raw,key='test')

    def tearDown(self):
        server.PROJECT_JOBS.clear();server.PROJECT_JOB_KEYS.clear()
        server.DATA=self.old_data;self.tmp.cleanup()

    def test_ai_applied_ids_survive_annotation_deletion(self):
        r=server.create_run('test',self.raw,{'method':'test'},'import')
        r=server.save_run(r['id'],{**r,'ai_applied_ids':['ai-example'],'issues':[]})
        saved=server.save_run(r['id'],{**r,'issues':[]})
        self.assertEqual(saved['ai_applied_ids'],['ai-example'])
        self.assertEqual(saved['issues'],[])

    def test_ai_runs_in_parallel_with_bounded_queue(self):
        gate=threading.Event();entered=[];guard=threading.Lock()
        def review(*args):
            with guard: entered.append(args[1])
            gate.wait(5)
            return {'same_screen':True,'summary':'ok','issues':[]}
        server.AI_JOBS.clear()
        runs=[server.create_run('test',self.raw,{'method':'test'},'import') for _ in range(4)]
        with patch('server.ai_review.selection',return_value=('test-model','low')),patch('server.ai_review.codex_path',return_value='codex'),patch('server.ai_review.review',side_effect=review):
            try:
                for run in runs: server.start_ai(run['id'],{})
                deadline=time.time()+2
                while len(entered)<3 and time.time()<deadline:time.sleep(.01)
                self.assertEqual(len(entered),3)
                self.assertEqual(sum(j['status']=='queued' for j in server.AI_JOBS.values()),1)
                server.start_ai(runs[0]['id'],{})
                self.assertEqual(len(server.AI_JOBS),4)
            finally:
                gate.set()
                deadline=time.time()+3
                while any(j['status'] in ('queued','running') for j in server.AI_JOBS.values()) and time.time()<deadline:time.sleep(.01)
            self.assertTrue(all(j['status']=='done' for j in server.AI_JOBS.values()))
            self.assertEqual(len(entered),4)
            for run in runs:
                self.assertTrue(list(server.run_path(run['id']).glob('ai-result-*.json')))
        server.AI_JOBS.clear()

    def test_ai_status_shows_region_progress_but_hides_unverified_candidates(self):
        gate=threading.Event();published=threading.Event()
        result={'same_screen':True,'summary':'partial','issues':[dict(description='标题字号偏大',x=.2,y=.1,confidence=.95,state_relation='equivalent')]}
        def review(*args):
            progress,metrics=args[5:7]
            metrics.update(partial_result=result,completed_regions=['header'])
            progress('comparing');published.set();gate.wait(3)
            metrics.pop('partial_result',None)
            return result
        server.AI_JOBS.clear();run=server.create_run('test',self.raw,{'method':'test'},'import')
        with patch('server.ai_review.selection',return_value=('test-model','low')),patch('server.ai_review.codex_path',return_value='codex'),patch('server.ai_review.review',side_effect=review):
            try:
                server.start_ai(run['id'],{});self.assertTrue(published.wait(2))
                current=server.ai_status(run['id'])
                self.assertEqual(current['status'],'running')
                self.assertEqual(current['completed_regions'],['header'])
                self.assertNotIn('issues',current)
                self.assertNotIn('same_screen',current)
            finally:
                gate.set();deadline=time.time()+3
                while server.ai_status(run['id'])['status']=='running' and time.time()<deadline:time.sleep(.01)
        self.assertEqual(server.ai_status(run['id'])['status'],'done');server.AI_JOBS.clear()

    def test_ai_receives_capture_time_environment(self):
        contexts=[]
        def review(*args):
            contexts.append(args[2])
            return {'same_screen':True,'summary':'ok','issues':[],'comparison_basis':{'environment':'内容区未知','components':[]}}
        server.AI_JOBS.clear()
        capture={'android_version':'15','display_density':'Physical density: 480','font_scale':'1.2',
                 'device':{'id':'private-serial'},'package':'private.package'}
        run=server.create_run('test',self.raw,capture,'import')
        with patch('server.ai_review.selection',return_value=('test-model','low')),patch('server.ai_review.codex_path',return_value='codex'),patch('server.ai_review.review',side_effect=review):
            server.start_ai(run['id'],{})
            deadline=time.time()+3
            while server.ai_status(run['id'])['status'] in ('queued','running') and time.time()<deadline:time.sleep(.01)
        self.assertEqual(server.ai_status(run['id'])['status'],'done')
        self.assertEqual(server.ai_status(run['id'])['comparison_basis']['environment'],'内容区未知')
        saved=server.read_json(next(server.run_path(run['id']).glob('ai-result-*.json')))
        self.assertEqual(saved['comparison_basis']['components'],[])
        self.assertEqual(contexts[0]['display']['density_dpi'],480)
        self.assertEqual(contexts[0]['display']['font_scale'],1.2)
        self.assertNotIn('private-serial',json.dumps(contexts));self.assertNotIn('private.package',json.dumps(contexts))
        server.AI_JOBS.clear()

    def ai_fixture(self):
        run=server.create_run('test',self.raw,{'method':'test'},'import')
        old={'id':'ai-old','rect':{'x':10,'y':20,'width':1,'height':1},'title':'旧AI标注','note':'人工编辑过的旧AI描述',
             'priority':'P2','status':'已确认','coordinate_space':'image','annotation_type':'point','node_label':'Codex 视觉分析'}
        manual={**old,'id':'manual-kept','title':'手动标注','note':'手动备注','node_label':''}
        return server.save_run(run['id'],{**run,'issues':[manual,old],'ai_applied_ids':['ai-old','ai-deleted']})

    def wait_ai(self,key):
        deadline=time.time()+3
        while server.ai_status(key)['status'] in ('running','queued') and time.time()<deadline:time.sleep(.01)
        return server.ai_status(key)

    def test_reanalysis_clears_only_ai_and_never_reuses_previous_results(self):
        server.AI_JOBS.clear();run=self.ai_fixture();gate=threading.Event();contexts=[]
        def review(*args):
            contexts.append(args[2]);gate.wait(3)
            return {'same_screen':True,'summary':'ok','issues':[dict(description='新AI结果',x=.5,y=.2,confidence=.95,state_relation='equivalent')]}
        with patch('server.ai_review.selection',return_value=('test-model','low')),patch('server.ai_review.codex_path',return_value='codex'),patch('server.ai_review.review',side_effect=review):
            try:
                first=server.start_ai(run['id'],{})
                cleared=first['run']
                self.assertEqual([i['id'] for i in cleared['issues']],['manual-kept'])
                self.assertEqual(cleared['ai_applied_ids'],[])
                self.assertEqual(cleared['ai_reanalysis']['issues'][0]['note'],'人工编辑过的旧AI描述')
                active=server.start_ai(run['id'],{})
                self.assertEqual(active['attempt_id'],first['attempt_id'])
                with self.assertRaises(ValueError):server.restore_ai_annotations(run['id'],first['attempt_id'])
            finally:gate.set();done=self.wait_ai(run['id'])
            self.assertEqual(done['status'],'done')
            current=server.read_json(server.run_path(run['id'])/'run.json')
            committed=server.save_run(run['id'],{**current,'issues':current['issues']+done['issues'],
                'ai_applied_ids':[i['id'] for i in done['issues']],'ai_result_attempt':done['attempt_id']})
            self.assertNotIn('ai_reanalysis',committed)
            self.assertEqual(len(committed['issues']),2)
            second=server.start_ai(run['id'],{});second_done=self.wait_ai(run['id'])
        self.assertNotEqual(first['attempt_id'],second['attempt_id'])
        self.assertNotEqual(first['signature'],second['signature'])
        self.assertNotEqual(done['issues'][0]['id'],second_done['issues'][0]['id'])
        self.assertEqual(len(contexts),2)
        self.assertEqual(contexts[0]['existing_issues'],['手动备注'])
        self.assertEqual([i['id'] for i in second['run']['issues']],['manual-kept'])
        self.assertEqual(len(list(server.run_path(run['id']).glob('ai-result-*.json'))),2)
        pending=server.read_json(server.run_path(run['id'])/'run.json')
        with self.assertRaises(ValueError):server.save_run(run['id'],{**pending,'ai_result_attempt':done['attempt_id']})
        self.assertEqual(server.read_json(server.run_path(run['id'])/'run.json')['revision'],pending['revision'])
        server.AI_JOBS.clear()

    def test_failed_reanalysis_restores_previous_ai_and_keeps_new_manual_edits(self):
        server.AI_JOBS.clear();run=self.ai_fixture();gate=threading.Event()
        def review(*args):
            gate.wait(3);raise ValueError('模拟分析失败')
        with patch('server.ai_review.selection',return_value=('test-model','low')),patch('server.ai_review.codex_path',return_value='codex'),patch('server.ai_review.review',side_effect=review):
            try:
                job=server.start_ai(run['id'],{});current=job['run']
                current=server.save_run(run['id'],{**current,'issues':[{**current['issues'][0],'note':'分析期间编辑手动问题'}]})
            finally:gate.set();self.wait_ai(run['id'])
        self.assertEqual(server.ai_status(run['id'])['status'],'error')
        with self.assertRaises(ValueError):server.restore_ai_annotations(run['id'],'wrong-attempt')
        restored=server.restore_ai_annotations(run['id'],job['attempt_id'])
        self.assertEqual([i['id'] for i in restored['issues']],['manual-kept','ai-old'])
        self.assertEqual(restored['issues'][0]['note'],'分析期间编辑手动问题')
        self.assertEqual(restored['ai_applied_ids'],['ai-old','ai-deleted'])
        self.assertNotIn('ai_reanalysis',restored)
        server.AI_JOBS.clear()

    def test_zero_results_and_restart_recovery(self):
        server.AI_JOBS.clear();run=self.ai_fixture()
        with patch('server.ai_review.selection',return_value=('test-model','low')),patch('server.ai_review.codex_path',return_value='codex'),patch('server.ai_review.review',return_value={'same_screen':True,'summary':'无新增','issues':[]}):
            job=server.start_ai(run['id'],{});done=self.wait_ai(run['id'])
            current=server.read_json(server.run_path(run['id'])/'run.json')
            committed=server.save_run(run['id'],{**current,'ai_result_attempt':done['attempt_id']})
            self.assertEqual([i['id'] for i in committed['issues']],['manual-kept'])
            self.assertNotIn('ai_reanalysis',committed)
            # Another uncommitted attempt survives a service restart safely.
            job=server.start_ai(run['id'],{});self.wait_ai(run['id'])
            interrupted=self.ai_fixture()
            server.start_ai(interrupted['id'],{});self.wait_ai(interrupted['id'])
        server.AI_JOBS.clear();server.recover_interrupted_ai()
        restored=server.read_json(server.run_path(run['id'])/'run.json')
        self.assertNotIn('ai_reanalysis',restored)
        self.assertEqual([i['id'] for i in restored['issues']],['manual-kept'])
        self.assertEqual(restored['ai_result_attempt'],committed['ai_result_attempt'])
        restored_ai=server.read_json(server.run_path(interrupted['id'])/'run.json')
        self.assertEqual([i['id'] for i in restored_ai['issues']],['manual-kept','ai-old'])
        self.assertEqual(restored_ai['issues'][1]['note'],'人工编辑过的旧AI描述')

    def test_state_hint_type_survives_save(self):
        r=server.create_run('test',self.raw,{'method':'test'},'import')
        hint={'id':'hint-1','rect':{'x':10,'y':20,'width':1,'height':1},'title':'待核对：键盘状态',
              'priority':'P2','status':'待确认','note':'待核对：键盘状态','review_kind':'state_hint',
              'coordinate_space':'image','annotation_type':'point'}
        saved=server.save_run(r['id'],{**r,'issues':[hint]})
        self.assertEqual(saved['issues'][0]['review_kind'],'state_hint')

    def test_save_retest_and_original_hash(self):
        r=server.create_run('test',self.raw,{'method':'test'},'import')
        issue={'id':'issue-1','rect':{'x':10,'y':20,'width':30,'height':40},'title':'偏移','priority':'P2','status':'已确认','note':'待修复'}
        saved=server.save_run(r['id'],{**r,'issues':[issue]})
        self.assertEqual(saved['revision'],1)
        with self.assertRaises(ValueError):server.save_run(r['id'],r)
        retest=server.create_run('test',self.raw,{'method':'test'},'import',previous_id=r['id'])
        self.assertEqual(retest['issues'][0]['status'],'待复测')
        self.assertFalse(retest['calibration']['confirmed'])
        self.assertEqual(retest['raw_sha256'],r['raw_sha256'])
        self.assertEqual((server.run_path(r['id'])/'original.bin').read_bytes(),self.raw)

    def test_cannot_analyze_unconfirmed_state(self):
        r=server.create_run('test',self.raw,{},'import')
        with self.assertRaises(ValueError):server.analyze(r['id'])

    def test_thumbnail_preserves_capture_and_record(self):
        raw = png_bytes(Image.new('RGB', (400, 1000), 'red'))
        record = server.create_run('test', raw, {}, 'import')
        folder = server.run_path(record['id'])
        saved = (folder/'run.json').read_bytes()
        thumbnail = server.run_thumbnail(record['id'])
        with Image.open(thumbnail) as image:
            self.assertEqual(image.size, (208, 520))
        self.assertEqual((folder/'original.bin').read_bytes(), raw)
        self.assertEqual((folder/'original.png').read_bytes(), raw)
        self.assertEqual((folder/'run.json').read_bytes(), saved)
        self.assertEqual(server.run_thumbnail(record['id']), thumbnail)

    def test_image_pin_round_trip_and_full_height_export(self):
        raw=png_bytes(Image.new('RGB',(400,1000),'white'))
        r=server.create_run('test',raw,{},'import')
        pin={'id':'pin-1','annotation_type':'point','coordinate_space':'image',
             'rect':{'x':200,'y':950,'width':1,'height':1},
             'title':'底部标注','note':'原始截图底部','priority':'P2','status':'待确认'}
        r=server.save_run(r['id'],{**r,'issues':[pin]})
        self.assertEqual(r['issues'][0]['coordinate_space'],'image')
        self.assertEqual(r['issues'][0]['rect']['y'],950)
        with zipfile.ZipFile(io.BytesIO(server.export_run(r['id']))) as archive:
            marked=Image.open(io.BytesIO(archive.read('annotated.png')))
            self.assertEqual(marked.size,(424,542))
            self.assertEqual(marked.getpixel((324,525)),(231,77,61))
        smaller=server.create_run('test',png_bytes(Image.new('RGB',(200,500),'white')),{},'import',previous_id=r['id'])
        self.assertEqual(smaller['issues'][0]['rect']['y'],475)
        self.assertEqual(smaller['issues'][0]['status'],'待复测')

    def test_change_calibration_invalidates_diagnostic(self):
        r=server.create_run('test',self.raw,{},'import')
        r=server.save_run(r['id'],{**r,'calibration':{**r['calibration'],'confirmed':True}})
        r=server.analyze(r['id']);self.assertIsNotNone(r['comparison'])
        r=server.save_run(r['id'],{**r,'threshold':30});self.assertIsNone(r['comparison'])

    def test_bubble_placement_preserves_pin_and_survives_retest(self):
        record=server.create_run('test',self.raw,{},'import')
        pin={'id':'bubble-pin','annotation_type':'point','coordinate_space':'image',
             'rect':{'x':30,'y':80,'width':1,'height':1},'title':'字号偏大',
             'note':'字号偏大','priority':'P2','status':'待确认','bubble_offset':{'x':.35,'y':-.12}}
        saved=server.save_run(record['id'],{**record,'issues':[pin]})
        self.assertEqual(saved['issues'][0]['rect'],pin['rect'])
        self.assertEqual(server.read_json(server.run_path(record['id'])/'run.json')['issues'][0]['bubble_offset'],pin['bubble_offset'])
        retest=server.create_run('test',png_bytes(Image.new('RGB',(400,400),'white')),{},'import',previous_id=record['id'])
        self.assertEqual(retest['issues'][0]['bubble_offset'],pin['bubble_offset'])
        self.assertEqual(retest['issues'][0]['rect']['x'],60)
        for offset in ({'x':float('nan'),'y':0},{'x':0},{'x':21,'y':0},'invalid'):
            with self.subTest(offset=offset), self.assertRaises(ValueError):
                server.save_run(saved['id'],{**saved,'issues':[{**pin,'bubble_offset':offset}]})
        self.assertEqual(server.read_json(server.run_path(record['id'])/'run.json')['revision'],saved['revision'])

    def test_export_escape_and_complete_evidence(self):
        r=server.create_run('test',self.raw,{},'import')
        issue={'id':'issue-1','rect':{'x':10,'y':20,'width':30,'height':40},'title':'<script>alert(1)</script>','priority':'P2','status':'待确认','note':'=HYPERLINK("evil")'}
        r=server.save_run(r['id'],{**r,'issues':[issue]})
        with zipfile.ZipFile(io.BytesIO(server.export_run(r['id']))) as archive:
            report=archive.read('report.html').decode()
            self.assertNotIn('<script>',report)
            self.assertIn('&lt;script&gt;',report)
            self.assertIn("'=HYPERLINK",archive.read('issues.csv').decode('utf-8-sig'))
            self.assertEqual(archive.read('original.bin'),self.raw)
            self.assertIn('annotated.png',archive.namelist())
            self.assertIn('source-snapshot.json',archive.namelist())

    def test_partial_node_scope_and_invalid_path(self):
        design=server.import_design({**self.snapshot,'total_nodes':50},self.raw,key='partial')
        self.assertFalse(design['complete_nodes'])
        with self.assertRaises(ValueError):server.run_path('../private')

    def test_lanhu_project_link_validation_and_association(self):
        url='https://lanhuapp.com/web/#/item/project/stage?tid=team&pid=project-1'
        self.assertEqual(server.validate_lanhu_url(url),url)
        for invalid in ('http://lanhuapp.com/?pid=x','https://evil.example/?pid=x',
                        'https://lanhuapp.com/web/#/item/project/product?pid=x&docId=doc','https://lanhuapp.com/'):
            with self.subTest(invalid=invalid),self.assertRaises(ValueError):server.validate_lanhu_url(invalid)

        def bridge(mode,received,output=None):
            self.assertEqual(mode,'sync');self.assertEqual(received,url)
            folder=output/'design-1';folder.mkdir(parents=True)
            snapshot={**self.snapshot,'design_id':'design-1','design_name':'首页',
                      'project_name':'新项目','source_url':url}
            server.write_json(folder/'snapshot.json',snapshot)
            (folder/'reference.png').write_bytes(self.raw)
            return {'project_name':'新项目','source_url':url,'total_designs':1,
                    'items':[{'index':1,'id':'design-1','name':'首页','kind':'design',
                              'bundle':'design-1','resolved_version':'test-version'}]}
        with patch.object(server,'project_catalog',return_value=None),patch.object(server,'run_lanhu_bridge',side_effect=bridge):
            catalog=server.associate_project(url)
            self.assertEqual(catalog['project_name'],'新项目')
            self.assertEqual(len(catalog['items']),1)
            design_key=catalog['items'][0]['design_key']
            self.assertTrue((server.DATA/'designs'/design_key/'reference.png').is_file())
            self.assertEqual(server.project_catalogs()[0]['id'],catalog['id'])

    def test_project_sync_runs_in_background_and_deduplicates(self):
        url='https://lanhuapp.com/web/#/item/project/stage?tid=team&pid=background-project'
        started=threading.Event();release=threading.Event()
        catalog={'id':server.project_key(url),'project_name':'大项目','source_url':url,
                 'total_designs':254,'items':[]}
        def associate(received,folder=None):
            self.assertEqual(received,url);started.set();release.wait(2);return catalog
        with patch.object(server,'project_catalogs',return_value=[]),patch.object(server,'associate_project',side_effect=associate):
            first=server.start_project_job(url);self.assertTrue(started.wait(1))
            second=server.start_project_job(url)
            self.assertEqual(first['id'],second['id']);self.assertIn(second['status'],('queued','running'))
            release.set()
            for _ in range(100):
                current=server.get_project_job(first['id'])
                if current['status']=='complete':break
                time.sleep(.01)
            self.assertEqual(current['status'],'complete');self.assertEqual(current['catalog']['project_name'],'大项目')

    def test_bootstrap_keeps_records_older_than_latest_100(self):
        expected = set()
        for index in range(105):
            record = server.create_run('test', self.raw, {}, 'import', title=str(index))
            expected.add(record['id'])
        http = server.ThreadingHTTPServer(('127.0.0.1', 0), server.Handler)
        old_port = server.PORT
        server.PORT = http.server_address[1]
        thread = threading.Thread(target=http.serve_forever, daemon=True)
        thread.start()
        try:
            with urllib.request.urlopen('http://127.0.0.1:'+str(server.PORT)+'/api/bootstrap') as response:
                result = json.load(response)
            self.assertEqual({record['id'] for record in result['runs']}, expected)
        finally:
            http.shutdown(); http.server_close(); thread.join(); server.PORT = old_port

    def test_local_api_rejects_foreign_origin_and_missing_token(self):
        http=server.ThreadingHTTPServer(('127.0.0.1',0),server.Handler)
        old_port=server.PORT;server.PORT=http.server_address[1]
        thread=threading.Thread(target=http.serve_forever,daemon=True);thread.start()
        url='http://127.0.0.1:'+str(server.PORT)
        try:
            with urllib.request.urlopen(url+'/api/bootstrap') as response:self.assertEqual(response.status,200)
            for headers in ({'Origin':'https://example.com'},{'Host':'evil.example'},{}):
                request=urllib.request.Request(url+'/api/demo',data=b'{}',headers={**headers,'Content-Type':'application/json'})
                with self.assertRaises(urllib.error.HTTPError) as caught:urllib.request.urlopen(request)
                self.assertEqual(caught.exception.code,403)
        finally:
            http.shutdown();http.server_close();thread.join();server.PORT=old_port


class AdbTests(unittest.TestCase):
    def test_screen_off_is_distinct_from_awake_or_unknown(self):
        for power in ('mWakefulness=Asleep', 'mWakefulness=Dozing'):
            with self.assertRaisesRegex(ValueError, '手机已息屏'):
                capture.ensure_screen_awake('test', power)
        capture.ensure_screen_awake('test', 'mWakefulness=Awake')
        capture.ensure_screen_awake('test', '')

    def test_parse_device_states(self):
        result=capture.parse_devices('List of devices attached\nemulator-5554 device product:sdk model:Pixel\nabc unauthorized usb:42 transport_id:2\ndef offline\n')
        self.assertEqual([d['state'] for d in result],['device','unauthorized','offline'])
        self.assertEqual([d['kind'] for d in result],['emulator','usb','device'])

    def test_unknown_device_rejected_before_capture(self):
        with patch.object(capture,'devices',return_value={'devices':[]}):
            with self.assertRaises(ValueError):capture.capture('unknown')


if __name__=='__main__':unittest.main()
