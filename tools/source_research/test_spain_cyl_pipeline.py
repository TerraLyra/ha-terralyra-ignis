"""Collection evidence must survive review and HTML rendering."""
import json
import unittest
from spain_cyl_paging import collect_pages
from spain_cyl_review import inspect_response
from spain_cyl_snapshot import latest_bulletin_indexes
from spain_cyl_preview import render


class PipelineTests(unittest.TestCase):
    def test_count_complete_collection_cannot_hide_older_rows(self):
        rows = [dict(provincia=['A'], termino_municipal='Town', fecha_del_parte=day,
                     hora_del_parte='10:00') for day in ('2026-09-24','2026-09-25')]
        collection = collect_pages(lambda *_: json.dumps(dict(total_count=2, results=rows)).encode())
        raw = json.dumps(collection).encode()
        review = inspect_response(raw)
        self.assertTrue(review['collection_status']['count_complete'])
        self.assertFalse(review['response_complete'])
        self.assertEqual(latest_bulletin_indexes(review)['indexes'], [0,1])
        html = render(raw)
        self.assertIn('2026-09-24', html)
        self.assertIn('2026-09-25', html)
        self.assertIn('A jelzett számú sor megérkezett', html)

    def test_failed_first_page_remains_failure_not_all_clear(self):
        def fail(*_):
            raise OSError('unavailable')
        raw = json.dumps(collect_pages(fail)).encode()
        review = inspect_response(raw)
        self.assertFalse(review['response_complete'])
        self.assertIn('A lekérés hibával megszakadt', render(raw))

    def test_reported_failure_overrides_matching_count(self):
        raw = json.dumps(dict(total_count=0, results=[], count_complete=False,
                              snapshot_verified=False, reason='page_error')).encode()
        self.assertFalse(latest_bulletin_indexes(inspect_response(raw))['applied'])
