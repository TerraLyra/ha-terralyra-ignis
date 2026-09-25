import json
import unittest
from spain_cyl_paging import collect_pages


def page(total, *ids):
    return json.dumps(dict(total_count=total, results=[dict(sample_id=i) for i in ids])).encode()


class PagingTests(unittest.TestCase):
    def collect(self, pages, **kwargs):
        calls = []
        def fetch(offset, limit):
            calls.append((offset, limit))
            result = pages[len(calls)-1]
            if isinstance(result, Exception):
                raise result
            return result
        return collect_pages(fetch, page_size=2, **kwargs), calls

    def test_complete_counts_are_not_snapshot_verification(self):
        result, calls = self.collect([page(3, 1, 2), page(3, 3)])
        self.assertTrue(result['count_complete'])
        self.assertFalse(result['snapshot_verified'])
        self.assertEqual(calls, [(0,2),(2,2)])

    def test_changes_errors_and_overlap_do_not_promote_partial_data(self):
        for second, reason in [(page(4,3,4), 'total_changed'), (page(3,2), 'overlapping_pages'),
                               (page(3), 'short_page'), (OSError('offline'), 'page_error'),
                               (b'{}', 'page_error')]:
            result, _ = self.collect([page(3,1,2), second])
            self.assertEqual(result['reason'], reason)
            self.assertFalse(result['count_complete'])
            self.assertEqual(len(result['results']), 2)

    def test_limit_and_empty(self):
        result, _ = self.collect([page(3,1,2)], max_pages=1)
        self.assertEqual(result['reason'], 'page_limit')
        result, _ = self.collect([page(0)])
        self.assertTrue(result['count_complete'])

    def test_oversized_and_byte_limits(self):
        result, _ = self.collect([page(3,1,2,3)])
        self.assertEqual(result['reason'], 'oversized_page')
        result, _ = self.collect([b' '*(1024*1024+1)])
        self.assertEqual(result['reason'], 'byte_limit')

    def test_invalid_limits(self):
        for opts in (dict(page_size=True), dict(page_size=101), dict(max_pages=6),
                     dict(page_size=100, max_pages=2)):
            with self.assertRaises(ValueError):
                collect_pages(lambda *_: b'', **opts)
