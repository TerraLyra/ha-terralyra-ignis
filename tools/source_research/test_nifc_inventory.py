import json
import unittest
from nifc_package import load_module
from test_nifc_fetch import encoded

steps = load_module('query')._fetch_id_steps

def ids(values):
    return json.dumps({'objectIdFieldName':'OBJECTID','objectIds':values}).encode()

class InventoryTests(unittest.TestCase):
    def drive(self, payloads, **kwargs):
        gen = steps(**kwargs)
        calls = [next(gen)]
        for payload in payloads:
            try: calls.append(gen.send(payload))
            except StopIteration as result: return result.value, calls
        self.fail('Unexpected additional request')

    def test_exact_coverage_without_transfer_flag(self):
        page = json.loads(encoded());page.pop('exceededTransferLimit')
        result,calls = self.drive([ids([1]),json.dumps(page).encode(),ids([1])])
        self.assertEqual(len(result.records),1)
        self.assertEqual(result.retrieval_method,'verified_id_inventory')
        self.assertIn('objectIds=1', calls[1][0])
        self.assertEqual(result.snapshot_consistency,'not_established')

    def test_empty_inventory_requires_final_confirmation(self):
        result,calls = self.drive([ids([]),ids([])])
        self.assertEqual(result.records,())
        self.assertEqual(len(calls),2)

    def test_changed_missing_duplicate_and_truncated_abort(self):
        cases = [[ids([1]),encoded(),ids([1,2])],
                 [ids([1]),encoded(empty=True)], [ids([1,1])],
                 [ids([1]),encoded(more=True)], [ids([True])],
                 [ids([1]),encoded(2)], [ids([1]),b'{"error":{}}']]
        for payloads in cases:
            with self.subTest(payloads=payloads), self.assertRaises(ValueError):
                self.drive(payloads)

    def test_budgets(self):
        for limits in ({'max_records':1},{'max_pages':1,'page_size':1},{'max_total_bytes':1}):
            with self.assertRaises(ValueError):self.drive([ids([1,2])],**limits)
        with self.assertRaises(ValueError):self.drive([],page_size=501)

    def test_multiple_batches(self):
        result,calls=self.drive([ids([2,1]),encoded(1),encoded(2),ids([1,2])],page_size=1)
        self.assertEqual(len(result.records),2)
        self.assertEqual(len(calls),4)
