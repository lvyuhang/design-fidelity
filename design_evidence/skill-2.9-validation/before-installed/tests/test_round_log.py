"""Round totals reflect input changes; retries/failures cannot disappear."""
import json
import unittest
import test_fidelity as fixtures
from round_log import RoundLog


class RoundLogTests(unittest.TestCase):
    def setUp(self):
        self.f = fixtures.GateTests(); self.f.setUp()
        self.addCleanup(self.f.doCleanups); self.f.save()
        self.path = self.f.root/'task.json'
        self.log = RoundLog(self.path)

    def begin(self, note='fixture'):
        return self.log.begin(self.f.root/'contract.json', self.f.root/'run', note)

    def finish(self, ticket, status='NOT_ACCEPTED'):
        self.log.finish(ticket, {'status':status,'seconds':1.25,'gate_status':'FAIL',
            'failures':[{'check':'features.icon','failures':['shift']}], 'failed_stage':'gate'})

    def test_first_implementation_counts_and_retries_are_separate(self):
        a = self.begin(); self.finish(a)
        b = self.begin('repeat'); self.finish(b)
        self.assertEqual((a['round_number'], b['round_number'], b['attempt_number']), (1,1,2))
        s = json.loads(self.path.read_text())['summary']
        self.assertEqual((s['rounds'],s['validation_attempts'],s['repeat_attempts']), (1,2,1))
        self.assertEqual(s['total_validation_seconds'],2.5)
        self.assertIsNone(s['tool_call_count'])

    def test_changed_implementation_increments_automatically(self):
        a=self.begin(); self.finish(a)
        p=self.f.root/'render.py';p.write_text(p.read_text()+'\n')
        b=self.begin('fix icon');self.finish(b)
        self.assertEqual(b['round_number'],2)
        data=json.loads(self.path.read_text())
        self.assertEqual(data['rounds'][0]['attempts'][0]['failures'][0]['check'],'features.icon')
        self.assertEqual(data['rounds'][1]['attempts'][0]['note'],'fix icon')

    def test_overrun_is_visible_without_changing_acceptance(self):
        for i in range(4):
            p=self.f.root/'render.py';p.write_text(p.read_text()+'\n')
            t=self.begin('additional correction');self.finish(t)
        data=json.loads(self.path.read_text())
        self.assertTrue(data['summary']['over_target'])
        self.assertEqual(data['summary']['latest_status'],'NOT_ACCEPTED')
        self.assertEqual(data['summary']['rounds'],4)

    def test_contract_change_is_logged(self):
        a=self.begin();self.finish(a)
        self.f.c['regions']['whole']['max_mae']=5;self.f.save()
        b=self.begin('strengthen check');self.finish(b)
        self.assertTrue(json.loads(self.path.read_text())['rounds'][1]['contract_changed'])

    def test_different_page_does_not_reset_existing_task(self):
        a=self.begin();self.finish(a);before=self.path.read_bytes()
        self.f.c['source_snapshot']='another';self.f.save()
        with self.assertRaisesRegex(ValueError,'different source'):
            self.begin()
        self.assertEqual(self.path.read_bytes(),before)

    def test_active_attempt_cannot_be_mislabelled_interrupted(self):
        self.begin()
        with self.assertRaisesRegex(ValueError,'still active'):
            self.begin()

    def test_interrupted_attempt_stays_in_log(self):
        self.begin()
        data=json.loads(self.path.read_text());data['rounds'][0]['attempts'][0]['pid']=None
        self.path.write_text(json.dumps(data))
        b=self.begin();self.finish(b)
        data=json.loads(self.path.read_text())
        self.assertEqual(data['rounds'][0]['attempts'][0]['status'],'INTERRUPTED')
        self.assertEqual(data['summary']['validation_attempts'],2)

    def test_html_escapes_notes_and_includes_failure_details(self):
        a=self.begin('<script>bad()</script>');self.finish(a)
        page=self.path.with_suffix('.html').read_text()
        self.assertNotIn('<script>',page)
        self.assertIn('&lt;script&gt;',page)
        self.assertIn('features.icon',page)
