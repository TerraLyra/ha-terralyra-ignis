"""Exercise actual pure context modules without loading Home Assistant."""
import sys
import types
import unittest
from pathlib import Path
from datetime import datetime, UTC, timedelta
from dataclasses import replace

package=types.ModuleType('_bm_context_test')
package.__path__=[str(Path(__file__).resolve().parents[2]/'custom_components/terralyra_ignis')]
sys.modules['_bm_context_test']=package
from _bm_context_test.bm_satellite_context import BMTownReport, bm_reports_for_satellite
from _bm_context_test.report_context import IncidentContext

class SatelliteContextTests(unittest.TestCase):
    def setUp(self):
        self.now=datetime(2026,10,7,12,tzinfo=UTC)
        self.incident=IncidentContext('a',47,19,self.now,self.now)
        self.report=BMTownReport('https://www.katasztrofavedelem.hu/modules/vesz/esemeny/1',self.now+timedelta(hours=2),frozenset({'HU:1'}),True)

    def run_match(self, report=None):
        return bm_reports_for_satellite('a',(self.incident,),{'a':frozenset({'HU:1'})},(report or self.report,))

    def test_publication_need_not_equal_observation(self):
        result=self.run_match()
        self.assertEqual(result['reports'][0]['relation'],'probable')
        self.assertFalse(result['creates_incident'])

    def test_unrelated_town_old_notice_and_nonfire_do_not_link(self):
        for r in [replace(self.report,event_settlement_ids=frozenset()),replace(self.report,event_settlement_ids=frozenset({'HU:2'})),replace(self.report,fire_report=False),replace(self.report,published_at=self.now+timedelta(hours=6,seconds=1))]:
            self.assertEqual(self.run_match(r)['reports'],[])

    def test_actual_competing_detection_is_disclosed_without_downgrade(self):
        r=bm_reports_for_satellite('a',(self.incident,replace(self.incident,incident_id='b')),{'a':frozenset({'HU:1'}),'b':frozenset({'HU:1'})},(self.report,))
        self.assertEqual(r['reports'][0]['relation'],'probable')
        self.assertTrue(r['reports'][0]['ambiguous'])
        self.assertEqual(r['reports'][0]['candidate_incident_ids'],['a','b'])

    def test_report_alone_cannot_create_incident(self):
        with self.assertRaises(ValueError):bm_reports_for_satellite('a',(),{},(self.report,))
        with self.assertRaises(ValueError):replace(self.report,published_at=self.now.replace(tzinfo=None))
