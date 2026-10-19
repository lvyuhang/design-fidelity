"""The configured entry point must preserve scope, failures and elapsed time."""
import json
import os
import subprocess
import sys
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
        self.assertGreaterEqual(result['elapsed_seconds'],result['command_seconds'])
        self.assertEqual(self.call('finish')[0].returncode,2)
        run,result=self.call('finish','--note','fixture inspected; no business preview claim')
        self.assertEqual(run.returncode,0,run.stdout)
        self.assertEqual(result['status'],'COMPLETE')

    def test_page_scope_cannot_silently_shrink(self):
        self.call('start')
        self.f.c['source_scope']['kind']='provided_nodes';self.f.save()
        run,result=self.call('validate')
        self.assertEqual(run.returncode,2)
        self.assertIn('scope differs',result['action']['error'])
        self.assertFalse((self.f.root/'session/task-run.json').exists())

    def test_finish_rejects_edit_after_last_validated_render(self):
        self.call('start');self.call('validate')
        code=self.f.root/'render.py';code.write_text(code.read_text()+'\n# changed')
        run,result=self.call('finish','--note','reviewed')
        self.assertEqual(run.returncode,2)
        self.assertIn('Inputs changed',result['action']['error'])

    def test_failure_stays_logged_and_not_marked_complete(self):
        self.call('start')
        self.c['test']='missing';self.config.write_text(json.dumps(self.c))
        run,result=self.call('validate')
        self.assertEqual(run.returncode,2)
        self.assertEqual(result['rounds']['latest_status'],'NOT_ACCEPTED')
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
        run,_=self.call('compile');self.assertEqual(run.returncode,0,run.stdout)
        before=(self.f.root/'compiled.json').read_bytes()
        self.assertEqual(self.call('compile')[0].returncode,2)
        self.assertEqual((self.f.root/'compiled.json').read_bytes(),before)

    def test_prepare_delegates_and_preserves_input_failures(self):
        from test_preparation import PreparationTests
        f=PreparationTests();f.setUp();self.addCleanup(f.doCleanups)
        f.run_prepare()
        self.config=f.root/'page.json'
        self.config.write_text(json.dumps({'name':'prepare fixture','run_dir':'session',
            'evidence':['source.json'],'reference':'reference.png','manifest':'manifest.json',
            'font_map':'fonts.json'}))
        self.call('start')
        run,_=self.call('prepare');self.assertEqual(run.returncode,0,run.stdout)
        draft=json.loads((f.root/'session/001-prepare/draft.json').read_text())
        self.assertEqual(draft['status'],'draft')
        f.manifest['snapshot_id']='wrong'
        (f.root/'manifest.json').write_text(json.dumps(f.manifest))
        run,result=self.call('prepare');self.assertEqual(run.returncode,2)
        self.assertEqual(result['action']['status'],'FAILED')
        self.assertFalse((f.root/'session/002-prepare/draft.json').exists())
