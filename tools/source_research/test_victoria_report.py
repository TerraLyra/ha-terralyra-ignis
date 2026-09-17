import json
from pathlib import Path
import subprocess
import sys
import unittest
from victoria_report import inspect_report
from victoria_feed import InvalidFeed

class VictoriaReportTests(unittest.TestCase):
    def test_combined_mixed_results_and_duplicate_ids(self):
        rows=[{'incidentNo':1,'category1':'Fire','category2':'Bushfire','latitude':-37,'longitude':145},
              {'incidentNo':1,'category1':'Medical','latitude':True,'longitude':145},
              {'category1':'Future category'}]
        report=inspect_report(json.dumps({'results':rows}).encode())
        self.assertEqual(report['record_count'],3)
        self.assertEqual(report['identity'],{'candidate':2,'missing':1})
        self.assertEqual(report['duplicate_id_groups'],1)
        self.assertEqual(report['categories'],{'medical':1,'unknown':1,'vegetation_fire_candidate':1})
        self.assertEqual(report['locations'],{'invalid':1,'missing':1,'valid_point':1})
        self.assertEqual(report['update_times'],{'missing_epoch':3})
        self.assertIn('dimensions_overlap',report['limitations'])

    def test_valid_empty_is_not_readiness_or_all_clear(self):
        report=inspect_report(b'{"results":[]}')
        self.assertEqual(report['record_count'],0)
        self.assertEqual(report['production_readiness'],'not_established')
        self.assertIn('not_an_active_fire_or_safety_assessment',report['limitations'])

    def test_entire_envelope_checked_before_partial_report(self):
        for raw in (b'{"results":[{"incidentNo":1},null]}',b'{"results":[],"error":"partial"}'):
            with self.assertRaises(InvalidFeed):inspect_report(raw)
        with self.assertRaises(InvalidFeed):inspect_report(b'{"results":[]}',max_bytes=1)
        with self.assertRaises(InvalidFeed):inspect_report(b'{"results":[{"x":1},{"x":2}]}',max_records=1)

    def test_raw_details_never_enter_report(self):
        raw={'incidentNo':'private-id','name':'private-name','category1':'private-category',
             'lastUpdateDateTime':'private-date','latitude':-37.123456,'longitude':145.123456}
        encoded=json.dumps(inspect_report(json.dumps({'results':[raw]}).encode()))
        for value in raw.values():self.assertNotIn(str(value),encoded)

    def run_cli(self,payload):
        return subprocess.run([sys.executable,str(Path(__file__).with_name('victoria_report.py')),'-'],
                              input=payload,capture_output=True,timeout=10)

    def test_cli_success(self):
        result=self.run_cli(b'{"results":[]}')
        self.assertEqual(result.returncode,0)
        self.assertEqual(json.loads(result.stdout)['record_count'],0)
        self.assertEqual(result.stderr,b'')

    def test_cli_failure_no_payload_or_traceback(self):
        result=self.run_cli(b'PRIVATE INVALID PAYLOAD')
        self.assertEqual(result.returncode,2)
        self.assertEqual(json.loads(result.stdout),{'status':'failed','reason':'input_unreadable_or_invalid'})
        self.assertEqual(result.stderr,b'')
