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

class SnapshotReportTests(unittest.TestCase):
    def payload(self,ids):
        return json.dumps({'results':[{'incidentNo':value} for value in ids]}).encode()

    def test_overlap_and_disappearance_not_closure(self):
        report=inspect_report(self.payload([2,3]),previous=self.payload([1,2]))
        self.assertEqual(report['snapshot_comparison'],{
            'status':'compared','shared':1,'only_before':1,'only_after':1,
            'identity_stability':'not_established','previous_record_count':2,
            'chronology':'caller_supplied_unverified','disappearance_means_closure':False})
        self.assertEqual(report['record_count'],2)

    def test_empty_and_typed_ids(self):
        self.assertEqual(inspect_report(self.payload([]),previous=self.payload([1]))['snapshot_comparison']['only_before'],1)
        comparison=inspect_report(self.payload(['1']),previous=self.payload([1]))['snapshot_comparison']
        self.assertEqual(comparison['shared'],0)

    def test_unusable_comparison_does_not_choose_winner_or_leak_ids(self):
        for previous,current in ((['secret','secret'],[1]),([1],[None]),([None],[1]),([1],[2,2])):
            comparison=inspect_report(self.payload(current),previous=self.payload(previous))['snapshot_comparison']
            self.assertEqual(comparison['status'],'unavailable')
            self.assertNotIn('shared',comparison)
            self.assertNotIn('secret',json.dumps(comparison))

    def test_invalid_previous_or_limits_no_partial_report(self):
        for previous in (b'private invalid',b'{"results":[],"error":"partial"}'):
            with self.assertRaises(InvalidFeed):inspect_report(self.payload([]),previous=previous)
        with self.assertRaises(InvalidFeed):
            inspect_report(self.payload([]),previous=self.payload([1,2]),max_records=1)

    def test_cli_previous_file_and_redacted_read_failure(self):
        import tempfile
        with tempfile.TemporaryDirectory() as folder:
            previous=Path(folder)/'private-previous.json'
            previous.write_bytes(self.payload([1,2]))
            command=[sys.executable,str(Path(__file__).with_name('victoria_report.py')),'-',
                     '--previous',str(previous)]
            result=subprocess.run(command,input=self.payload([2,3]),capture_output=True,timeout=10)
            self.assertEqual(result.returncode,0)
            self.assertEqual(json.loads(result.stdout)['snapshot_comparison']['shared'],1)
            previous.unlink()
            result=subprocess.run(command,input=self.payload([]),capture_output=True,timeout=10)
            self.assertEqual(result.returncode,2)
            self.assertNotIn(b'private-previous',result.stdout+result.stderr)
            self.assertEqual(result.stderr,b'')
