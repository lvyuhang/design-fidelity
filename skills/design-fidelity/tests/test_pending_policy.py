import hashlib,json,os,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from pending_assets import load_policy,pending_allowed
from source_disposition import placeholder_issue

class PendingPolicyTests(unittest.TestCase):
    def test_wrong_schema_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'policy.json';p.write_text('{"version":1,"pending_assets":[]}')
            with self.assertRaisesRegex(ValueError,'INVALID_PENDING_ASSETS'):load_policy(p)

    def test_fallback_is_not_original_asset(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);e=root/'e.json';p=root/'policy.json'
            nodes={'n':{'node_type':'shape','asset_ids':['a'],'bounds':dict(x=0,y=0,width=10,height=10),'raw_style':{'fills':[{}]}}}
            for kind,allowed in [('render_fallback',True),('exported_asset',False),('unknown',False)]:
                e.write_text(json.dumps({'assets':[{'asset_id':'a','kind':kind}]}))
                p.write_text(json.dumps({'policy':'placeholder_after_reinspection','nodes':{'n':{'reason':'Authorized missing source after reinspection','evidence':[{'path':'e.json','sha256':hashlib.sha256(e.read_bytes()).hexdigest()}]}}}))
                with patch.dict(os.environ,{'LANHU_PENDING_ASSETS':str(p)}):
                    self.assertEqual(pending_allowed('n',nodes),allowed)
                    self.assertEqual(placeholder_issue('n',nodes) is None,allowed)
                    e.write_text('{}')
                    self.assertFalse(pending_allowed('n',nodes))
