"""The configured entry point must preserve scope, failures and elapsed time."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import test_fidelity as fixtures


class PageSessionTests(unittest.TestCase):
    def setUp(self):
        self.f=fixtures.GateTests();self.f.setUp();self.addCleanup(self.f.doCleanups);self.f.save()
        self.config=self.f.root/'page.json'
        self.c={'name':'session fixture','run_dir':'session','contract':'contract.json',
                'app':'.','test':'normal','output_env':'FIXTURE_OUTPUT'}
        self.config.write_text(json.dumps(self.c))
        binary=self.f.root/'bin';binary.mkdir()
        shim=binary/'flutter'
        shim.write_text(f'#!{sys.executable}\nimport os,subprocess,sys\n'
            f'sys.exit(subprocess.call([sys.executable,{str(self.f.root/"render.py")!r},'
            'os.environ["FIXTURE_OUTPUT"],sys.argv[-1]]))\n')
        shim.chmod(0o755)
        self.env={**os.environ,'PATH':str(binary)+os.pathsep+os.environ.get('PATH','')}

    def call(self,action,*flags):
        r=subprocess.run([sys.executable,str(fixtures.SCRIPTS/'page_session.py'),
            '--config',str(self.config),action,*flags],env=self.env,capture_output=True,text=True)
        return r,json.loads(r.stdout)

    def test_stop_freezes_time_without_acceptance_or_restart(self):
        self.call('start')
        self.assertEqual(self.call('stop')[0].returncode, 2)
        run, result = self.call('stop', '--note', 'round budget exhausted')
        self.assertEqual(run.returncode, 0, run.stdout)
        self.assertEqual(result['status'], 'STOPPED_NOT_ACCEPTED')
        elapsed = result['elapsed_seconds']
        self.assertEqual(self.call('status')[1]['elapsed_seconds'], elapsed)
        self.assertEqual(self.call('validate')[0].returncode, 2)
        self.assertEqual(self.call('start')[0].returncode, 2)

    def test_start_cannot_reset_and_prestart_time_is_not_fabricated(self):
        self.assertEqual(self.call('validate')[0].returncode,2)
        self.assertEqual(self.call('start')[0].returncode,0)
        path=self.f.root/'session/session.json';before=path.read_bytes()
        self.assertEqual(self.call('start')[0].returncode,2)
        self.assertEqual(path.read_bytes(),before)
        self.assertIsNone(self.call('status')[1]['tokens'])

    def test_real_delegated_runner_and_finish_require_review_note(self):
        self.call('start')
        run,result=self.call('validate','--note','initial')
        self.assertEqual(run.returncode,0,run.stdout+run.stderr)
        self.assertEqual(result['rounds']['latest_status'],'PASS')
        self.assertEqual(result['next_action']['code'],'REVIEW_AND_FINISH')
        self.assertGreaterEqual(result['elapsed_seconds'],result['command_seconds'])
        data=json.loads((self.f.root/'session/session.json').read_text())
        self.assertTrue(data['events'][0]['commands'][0]['argv'])
        self.assertNotIn('commands',run.stdout)
        full={'action':data['events'][0],**data['summary']}
        self.assertLess(len(run.stdout),len(json.dumps(full,ensure_ascii=False))*.65)
        self.assertEqual(self.call('finish')[0].returncode,2)
        run,result=self.call('finish','--note','fixture inspected; no business preview claim')
        self.assertEqual(run.returncode,0,run.stdout)
        self.assertEqual(result['status'],'COMPLETE')
        self.assertEqual(result['next_action']['action'],'none')

    def test_page_scope_cannot_silently_shrink(self):
        self.call('start')
        self.f.c['source_scope']['kind']='provided_nodes';self.f.save()
        run,result=self.call('validate')
        self.assertEqual(run.returncode,2)
        self.assertIn('scope differs',result['error'])
        self.assertFalse((self.f.root/'session/task-run.json').exists())

    def test_custom_renderer_audit_does_not_precreate_render_output(self):
        from fidelity_contract import sha256
        caps=self.f.root/'renderer-capabilities.json'
        proof={'implementation':'render.py:fixture','test':'tests:fixture'}
        caps.write_text(json.dumps({'supported':{
            'fills.color':proof,'asset.export_frame':proof}}))
        self.c.update(evidence=['source.json'],renderer_kind='custom',
                      renderer_capabilities='renderer-capabilities.json')
        self.config.write_text(json.dumps(self.c))
        self.call('start')
        state=self.f.root/'session/session.json';data=json.loads(state.read_text())
        data['events'].append({'action':'prepare','status':'OK','seconds':0,
            'prepared_input_hashes':{str((self.f.root/'source.json').resolve()):sha256(self.f.root/'source.json')}})
        state.write_text(json.dumps(data))
        run,result=self.call('validate')
        self.assertEqual(run.returncode,0,run.stdout+run.stderr)
        saved=json.loads(state.read_text());event=saved['events'][-1]
        self.assertTrue(Path(event['renderer_coverage_report']).is_file())
        self.assertNotEqual(Path(event['renderer_coverage_report']).parent,
                            Path(event['report']).parent)
        self.assertTrue(Path(event['report']).parent.is_dir())

    def test_unvalidated_preview_is_diagnostic_only(self):
        self.call('start')
        run,result=self.call('phase','--phase','preview')
        self.assertEqual(run.returncode,2)
        self.assertIn('Accepted preview requires',result['error'])
        self.assertEqual(self.call('phase','--phase','diagnostic_preview')[0].returncode,0)
        self.assertEqual(self.call('finish','--note','not accepted')[0].returncode,2)

    def test_preview_rejects_code_changes_after_validation(self):
        self.call('start');self.call('validate')
        code=self.f.root/'render.py';code.write_text(code.read_text()+'\n# changed')
        run,result=self.call('phase','--phase','preview')
        self.assertEqual(run.returncode,2)
        self.assertIn('Inputs changed',result['error'])

    def test_finish_rejects_edit_after_last_validated_render(self):
        self.call('start');self.call('validate')
        code=self.f.root/'render.py';code.write_text(code.read_text()+'\n# changed')
        run,result=self.call('finish','--note','reviewed')
        self.assertEqual(run.returncode,2)
        self.assertIn('Inputs changed',result['error'])

    def test_failure_stays_logged_and_not_marked_complete(self):
        self.call('start')
        self.c['test']='missing';self.config.write_text(json.dumps(self.c))
        run,result=self.call('validate')
        self.assertEqual(run.returncode,2)
        self.assertEqual(result['rounds']['latest_status'],'NOT_ACCEPTED')
        self.assertIn('features.icon',[v['check'] for v in result['failed_checks']])
        self.assertEqual(result['action_status'],'FAILED')
        self.assertTrue(Path(result['report']).is_file())
        self.assertEqual(self.call('finish','--note','must fail')[0].returncode,2)
        data=json.loads((self.f.root/'session/session.json').read_text())
        self.assertEqual(data['status'],'RUNNING')
        self.assertEqual(data['events'][0]['status'],'FAILED')

    def test_compile_uses_existing_compiler_and_never_overwrites(self):
        self.call('start')
        spec={k:v for k,v in self.f.c.items() if k not in ('coverage','status','pinned_files')}
        (self.f.root/'spec.json').write_text(json.dumps(spec))
        self.c.update(spec='spec.json',contract='compiled.json')
        self.config.write_text(json.dumps(self.c))
        run,result=self.call('compile');self.assertEqual(run.returncode,0,run.stdout)
        self.assertEqual(result['next_action']['action'],'validate')
        before=(self.f.root/'compiled.json').read_bytes()
        self.assertEqual(self.call('compile')[0].returncode,0)
        self.assertEqual((self.f.root/'compiled.json').read_bytes(),before)

    def test_accept_compiles_then_validates_in_one_logged_action(self):
        spec={k:v for k,v in self.f.c.items() if k not in ('coverage','status','pinned_files')}
        # The fixture renders with Python, not the Flutter harness, so it has no
        # sourceKey geometry; the opt-out must carry a reason.
        spec.update(geometry_probe='off', geometry_probe_reason='synthetic Python renderer',
                    responsive_check='off', responsive_check_reason='synthetic Python renderer')
        (self.f.root/'spec.json').write_text(json.dumps(spec))
        self.c.update(spec='spec.json',contract='accepted.json')
        self.config.write_text(json.dumps(self.c))
        self.call('start')
        run,result=self.call('accept','--note','first complete acceptance')
        self.assertEqual(run.returncode,0,run.stdout+run.stderr)
        self.assertEqual(result['rounds']['latest_status'],'PASS')
        data=json.loads((self.f.root/'session/session.json').read_text())
        self.assertEqual(data['events'][0]['action'],'accept')
        self.assertEqual(len(data['events'][0]['commands']),2)
        self.assertEqual(Path(data['events'][0]['commands'][0]['argv'][1]).name,
                         'compile_contract.py')
        self.assertEqual(Path(data['events'][0]['commands'][1]['argv'][1]).name,
                         'run_target.py')
        self.assertEqual(self.call('finish','--note','reviewed accepted render')[0].returncode,0)

    def test_prepare_delegates_and_preserves_input_failures(self):
        from test_preparation import PreparationTests
        f=PreparationTests();f.setUp();self.addCleanup(f.doCleanups)
        f.run_prepare()
        self.config=f.root/'page.json'
        self.config.write_text(json.dumps({'name':'prepare fixture','run_dir':'session',
            'evidence':['source.json'],'reference':'reference.png','manifest':'manifest.json',
            'font_map':'fonts.json'}))
        self.call('start')
        run,result=self.call('prepare');self.assertEqual(run.returncode,0,run.stdout)
        self.assertEqual(result['preparation']['source_nodes'],3)
        self.assertEqual(result['next_action']['action'],'inspect --view components')
        self.assertEqual(result['preparation']['text_style_group_count'],1)
        self.assertTrue(Path(result['preparation']['brief']).is_file())
        draft=json.loads((f.root/'session/001-prepare/draft.json').read_text())
        self.assertEqual(draft['status'],'draft')
        f.manifest['snapshot_id']='wrong'
        (f.root/'manifest.json').write_text(json.dumps(f.manifest))
        run,result=self.call('prepare');self.assertEqual(run.returncode,2)
        self.assertEqual(result['action_status'],'FAILED')
        self.assertEqual(result['preparation']['status'],'NOT_PREPARED')
        self.assertEqual(result['next_action']['action'],'read_report')
        self.assertFalse((f.root/'session/002-prepare/draft.json').exists())

    def test_prepare_passes_and_pins_pending_asset_policy(self):
        from test_preparation import PreparationTests
        from fidelity_contract import sha256
        f=PreparationTests();f.setUp();self.addCleanup(f.doCleanups)
        missing={'node_id':'missing-vector','node_type':'shape','parent_id':'surface',
                 'bounds':{'x':70,'y':10,'width':8,'height':8},
                 'raw_style':{'fills':[{'type':'color','color':{'r':1,'g':0,'b':0,'a':1}}]}}
        f.e['nodes'].append(missing);f.e['total']=4
        (f.root/'source.json').write_text(json.dumps(f.e))
        (f.root/'manifest.json').write_text(json.dumps(f.manifest))
        pending=f.root/'pending-assets.json'
        pending.write_text(json.dumps({'policy':'placeholder_after_reinspection','nodes':{
            'missing-vector':{'reason':'source checked and unavailable','evidence':[
                {'path':'source.json','sha256':sha256(f.root/'source.json')}]}}}))
        self.config=f.root/'page.json'
        self.config.write_text(json.dumps({'name':'pending fixture','run_dir':'session',
            'evidence':['source.json'],'reference':'reference.png','manifest':'manifest.json',
            'font_map':'fonts.json','pending_assets':'pending-assets.json'}))
        self.call('start')
        run,result=self.call('prepare');self.assertEqual(run.returncode,0,run.stdout+run.stderr)
        data=json.loads((f.root/'session/session.json').read_text())
        command=data['events'][0]['commands'][0]
        self.assertEqual(command['env_overrides']['LANHU_PENDING_ASSETS'],str(pending.resolve()))
        self.assertGreaterEqual(command['seconds'],0)
        self.assertEqual(command['returncode'],0)
        self.assertIn(str(pending.resolve()),data['events'][0]['prepared_input_hashes'])
        self.assertEqual(result['preparation']['status'],'PREPARED_FOR_REVIEW')

    def test_verbose_retains_details_for_entrypoint_debugging(self):
        self.call('start')
        run,result=self.call('validate','--verbose')
        self.assertEqual(run.returncode,0,run.stdout)
        self.assertTrue(result['action']['commands'][0]['argv'])

    def test_inspect_is_bounded_logged_and_not_a_validation_round(self):
        self.call('start')
        (self.f.root/'large.json').write_text(json.dumps([{'node':i,'style':'x'*80} for i in range(150)]))
        run,page=self.call('inspect','--file','large.json','--limit','2000')
        self.assertEqual(run.returncode,0,run.stdout)
        self.assertLessEqual(len(run.stdout.strip()),2000)
        self.assertEqual(self.call('inspect','--file','large.json','--limit','0')[0].returncode,2)
        self.assertIsNotNone(page['next_cursor'])
        self.assertEqual(self.call('inspect','--file','large.json','--cursor',str(page['next_cursor']))[0].returncode,2)
        run,second=self.call('inspect','--file','large.json','--cursor',str(page['next_cursor']),
                             '--sha256',page['sha256'],'--limit','2000')
        self.assertEqual(run.returncode,0,run.stdout)
        state=json.loads((self.f.root/'session/session.json').read_text())
        self.assertEqual(state['events'],[])
        inspections=(self.f.root/'session/inspections.jsonl').read_text().splitlines()
        self.assertEqual(len(inspections),2)
        self.assertIsNone(self.call('status')[1]['rounds'])

    def test_duplicate_evidence_is_reused_but_refresh_and_changes_are_visible(self):
        self.call('start')
        file=self.f.root/'source-read.json'
        file.write_text(json.dumps({'data':'useful '*500}))
        first=self.call('inspect','--file',str(file))[1]
        repeated=self.call('inspect','--file',str(file))[1]
        self.assertTrue(repeated['already_returned'])
        self.assertLess(len(json.dumps(repeated)),len(json.dumps(first)))
        self.assertIn('items',self.call('inspect','--file',str(file),'--refresh')[1])
        file.write_text(json.dumps({'data':'changed'}))
        self.assertIn('items',self.call('inspect','--file',str(file))[1])

    def test_component_is_atomic_and_preserves_explicit_overflow_state(self):
        from test_preparation import PreparationTests
        f=PreparationTests();f.setUp();self.addCleanup(f.doCleanups);f.run_prepare()
        self.config=f.root/'page.json'
        self.config.write_text(json.dumps({'name':'component fixture','run_dir':'session',
            'evidence':['source.json'],'reference':'reference.png','manifest':'manifest.json',
            'font_map':'fonts.json'}))
        self.call('start');self.call('prepare')
        run,index=self.call('inspect','--view','components')
        self.assertEqual(run.returncode,0,run.stdout)
        self.assertTrue(index['complete_packet'])
        run,full=self.call('inspect','--component','all')
        self.assertEqual(run.returncode,0,run.stdout)
        self.assertTrue(full['complete_packet'])
        self.assertEqual(full['packet']['selection']['unselected_page_inventory'],0)
        alias=next(k for k,v in full['packet']['node_aliases'].items() if v=='icon')
        self.assertEqual(self.call('inspect','--node',alias)[0].returncode,0)
        run,small=self.call('inspect','--component','all','--limit','2000')
        self.assertEqual(run.returncode,0,run.stdout)
        self.assertFalse(small['complete_packet'])
        self.assertNotIn('packet',small)
        # An overflow notice must never become a successfully delivered packet.
        self.assertFalse(self.call('inspect','--component','all','--limit','2000')[1].get('already_returned',False))

    def test_failed_checks_are_bounded_with_complete_report_preserved(self):
        from page_session import compact_result
        self.call('start')
        root=self.f.root/'session'
        data=json.loads((root/'session.json').read_text())
        report=root/'failure.json'
        failures=[{'check':f'features.{i}','failures':['offset']} for i in range(12)]
        report.write_text(json.dumps({'failures':failures,'gate_status':'FAIL'}))
        event={'action':'validate','status':'FAILED','seconds':1,'report':str(report)}
        result=compact_result(data,root,event)
        self.assertEqual(result['failed_check_count'],12)
        self.assertEqual(len(result['failed_checks']),5)
        self.assertEqual(len(json.loads(report.read_text())['failures']),12)
        self.assertEqual(result['next_action']['code'],'FIX_IMPLEMENTATION')
        self.assertIn('完整失败报告',result['next_action']['instruction'])

    def test_archiving_baseline_log_does_not_reset_session_rounds(self):
        self.call('start'); self.call('validate')
        log=self.f.root/'session/task-run.json'
        log.rename(log.with_name('archived-task-run.json'))
        run,result=self.call('validate')
        self.assertEqual(run.returncode,0,run.stdout)
        self.assertEqual(result['rounds']['rounds'],2)
        self.assertEqual(result['rounds']['validation_attempts'],2)
        self.assertEqual(result['rounds']['baseline_count'],2)

    def test_phase_time_partition_and_pinned_interpreter(self):
        self.call('start')
        self.call('phase','--phase','implementation')
        self.call('phase','--phase','validation')
        run,result=self.call('validate')
        self.assertEqual(run.returncode,0,run.stdout)
        self.assertAlmostEqual(sum(result['phase_seconds'].values()),result['elapsed_seconds'],delta=.01)
        data=json.loads((self.f.root/'session/session.json').read_text())
        self.assertEqual(data['python'],sys.executable)
        self.assertEqual(data['events'][0]['commands'][0]['argv'][0],sys.executable)
        self.call('phase','--phase','preview')
        self.assertEqual(self.call('finish','--note','reviewed')[0].returncode,0)

    def test_missing_attempt_report_is_disclosed_not_counted_as_success(self):
        self.call('start');self.call('validate')
        data=json.loads((self.f.root/'session/session.json').read_text())
        Path(data['events'][0]['report']).unlink()
        _,result=self.call('status')
        self.assertEqual(result['rounds']['validation_calls'],1)
        self.assertEqual(result['rounds']['validation_attempts'],0)
        self.assertEqual(result['rounds']['untracked_calls'],1)
        self.assertEqual(result['next_action']['action'],'read_report')


class CompactNextActionTests(unittest.TestCase):
    def setUp(self):
        temporary=tempfile.TemporaryDirectory();self.addCleanup(temporary.cleanup)
        self.root=Path(temporary.name)
        self.data={'summary':{'status':'RUNNING','elapsed_seconds':1,
                             'command_seconds':1,'tokens':None,'rounds':None}}

    def result(self, action, outcome, details=None, error=None):
        from page_session import compact_result
        event={'action':action,'status':outcome,'seconds':1,'error':error}
        if details is not None:
            report=self.root/'report.json'
            report.write_text(json.dumps(details))
            event['report']=str(report)
        return compact_result(self.data,self.root,event)['next_action']

    def test_input_issues_must_be_inspected_and_fixed_before_reprepare(self):
        result=self.result('prepare','FAILED',{'status':'NEEDS_INPUT_FIXES'})
        self.assertEqual(result['action'],'inspect --view issues')
        self.assertIn('再 prepare',result['instruction'])

    def test_preparation_is_review_only_and_failed_followup_cannot_advance(self):
        result=self.result('prepare','OK',{'status':'PREPARED_FOR_REVIEW'})
        self.assertEqual(result['action'],'inspect --view components')
        self.assertIn('不代表验收通过',result['instruction'])
        self.assertEqual(self.result('prepare','FAILED',{'status':'PREPARED_FOR_REVIEW'})['action'],
                         'read_report')

    def test_visual_failure_repairs_implementation_without_relaxing_acceptance(self):
        result=self.result('validate','FAILED',{'status':'NOT_ACCEPTED','gate_status':'FAIL',
                                               'failed_stage':'gate'},'CONTRACT_ERROR in message')
        self.assertEqual(result['code'],'FIX_IMPLEMENTATION')
        self.assertEqual(result['action'],'fix_implementation_then_validate')
        for rule in ('批量修实现','禁止改阈值','删检查','扩大排除'):
            self.assertIn(rule,result['instruction'])

    def test_unevaluated_and_contract_preconditions_do_not_request_blind_render(self):
        for details in ({'gate_status':'NOT_EVALUATED','failed_stage':'gate'},
                        {'gate_status':None,'failed_stage':'baseline'},
                        {'gate_status':None,'failed_stage':'preflight'}):
            with self.subTest(details=details):
                result=self.result('accept','FAILED',{'status':'NOT_ACCEPTED',**details})
                self.assertEqual(result['code'],'FIX_PREREQUISITES')
                self.assertEqual(result['action'],'read_report')
                self.assertIn('勿盲目重渲染',result['instruction'])

    def test_only_complete_success_routes_to_receipt_review_and_finish(self):
        for state in ('PASS','PASS_WITH_EXCLUSIONS'):
            with self.subTest(state=state):
                result=self.result('accept','OK',{'status':state,'gate_status':state})
                self.assertEqual(result['action'],'phase --phase preview')
                self.assertIn('finish --note',result['instruction'])
                self.assertIn('排除项',result['instruction'])
        for outcome,details in (
                ('FAILED',{'status':'NOT_ACCEPTED','gate_status':'PASS','failed_stage':'build'}),
                ('OK',{'gate_status':'PASS'}),
                ('FAILED',{'status':'PASS','gate_status':'PASS'})):
            with self.subTest(outcome=outcome,details=details):
                self.assertEqual(self.result('validate',outcome,details)['action'],'read_report')

    def test_unknown_missing_and_text_only_states_require_report(self):
        from page_session import compact_result
        results=[compact_result(self.data,self.root)['next_action'],
                 self.result('validate','FAILED',None,'CONTRACT_ERROR: missing fonts; FAIL'),
                 self.result('validate','FAILED',{'gate_status':'UNKNOWN','failed_stage':'render'}),
                 self.result('compile','FAILED',{'status':'ready'}),
                 self.result('compile','OK',{'status':'draft'})]
        for result in results:
            with self.subTest(result=result):
                self.assertEqual(result['action'],'read_report')
                self.assertEqual(set(result),{'code','action','instruction'})
