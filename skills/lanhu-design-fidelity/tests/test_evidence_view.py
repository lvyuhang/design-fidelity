import json
from pathlib import Path
import tempfile
import unittest
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))

from evidence_view import encode, resolve, view


class EvidenceViewTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name)/'source.json'

    def save(self, data):
        self.path.write_text(json.dumps(data,ensure_ascii=False))

    def pages(self, pointer=''):
        cursor, digest = 0, None
        for _ in range(1000):
            page = view(self.path,pointer,cursor,2000,digest)
            self.assertLessEqual(len(encode(page)),2000)
            yield page
            if page['next_cursor'] is None:
                return
            self.assertGreater(page['next_cursor'],cursor)
            cursor,digest = page['next_cursor'],page['sha256']
        self.fail('Pagination failed to terminate')

    def test_all_small_nodes_survive_bounded_pagination(self):
        data=[{'node_id':str(i),'rect':[1,2,1,1],'fill':'#090909'} for i in range(600)]
        self.save(data)
        records=[item['value'] for p in self.pages() for item in p['items']]
        self.assertEqual(records,data)

    def test_large_geometry_deferred_without_hiding_following_nodes(self):
        points=[{'x':i/300,'y':.1} for i in range(300)]
        self.save([{'points':points,'blur':{'radius':24,'type':'background'}},{'tiny_badge':True}])
        records=[v for p in self.pages() for v in p['items']]
        self.assertTrue(records[0]['deferred'])
        self.assertEqual(records[1]['value'],{'tiny_badge':True})
        detail=view(self.path,records[0]['pointer'],limit=2000)
        self.assertEqual(detail['items'][0]['pointer'],'/0/points')
        rebuilt=[v['value'] for p in self.pages('/0/points') for v in p['items']]
        self.assertEqual(rebuilt,points)

    def test_long_string_can_be_reconstructed_including_escapes(self):
        content='中文\\\n\t"'*500
        self.save({'a/b~c':content})
        pointer='/a~1b~0c'
        self.assertEqual(resolve({'a/b~c':content},pointer),content)
        rebuilt=''.join(p['items'][0]['text'] for p in self.pages(pointer))
        self.assertEqual(rebuilt,content)

    def test_changed_evidence_cannot_continue_old_cursor(self):
        self.save(list(range(500)))
        first=view(self.path,limit=2000)
        self.save(list(range(501)))
        with self.assertRaisesRegex(ValueError,'changed'):
            view(self.path,cursor=first['next_cursor'],limit=2000,expected_hash=first['sha256'])

    def test_budget_cannot_be_disabled(self):
        self.save({'small':True})
        for n in [0,1999,24001]:
            with self.assertRaises(ValueError):
                view(self.path,limit=n)


if __name__ == '__main__':
    unittest.main()
