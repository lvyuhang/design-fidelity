import json
import tempfile
import unittest
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from page_session import require_prepared_sources
from fidelity_contract import sha256

class PreparedSourcesTests(unittest.TestCase):
    def test_unprepared_changed_and_unchanged_inputs(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d).resolve(); source = root / 'source.json'; source.write_text('{}')
            config = {'evidence':['source.json']}
            state = {'events':[]}
            with self.assertRaises(ValueError):
                require_prepared_sources(state, config, root)
            state['events'].append({'action':'prepare','status':'OK',
                'prepared_input_hashes':{str(source):sha256(source)}})
            require_prepared_sources(state, config, root)
            source.write_text('{"nodes":[]}')
            with self.assertRaises(ValueError):
                require_prepared_sources(state, config, root)

    def test_pending_asset_policy_is_a_pinned_preparation_input(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d).resolve()
            source = root/'source.json'; source.write_text('{}')
            pending = root/'pending-assets.json'; pending.write_text('{"policy":"placeholder_after_reinspection"}')
            config = {'evidence':['source.json'], 'pending_assets':'pending-assets.json'}
            state = {'events':[{'action':'prepare','status':'OK','prepared_input_hashes':{
                str(source):sha256(source), str(pending):sha256(pending)}}]}
            require_prepared_sources(state, config, root)
            pending.write_text('{"policy":"changed"}')
            with self.assertRaises(ValueError):
                require_prepared_sources(state, config, root)

if __name__ == '__main__': unittest.main()
