import unittest
from copy import deepcopy
from datetime import datetime, UTC
from tasalert_package import load
from tasalert_engine import Engine, advance
from test_tasalert_snapshot import record
views=load('presentation').report_views


class PresentationTests(unittest.TestCase):
    def setUp(self):
        self.engine=advance(Engine(),datetime(2026,10,12,tzinfo=UTC),200,record())

    def test_source_status_is_not_lifecycle_claim(self):
        view=views(self.engine)[0]
        self.assertEqual(view['source_status'],'Going')
        self.assertFalse(view['active_fire_verified'])
        self.assertFalse(view['satellite_detection'])
        self.assertEqual(view['attribution'],'TasALERT')

    def test_categories_are_distinct(self):
        for source,category in [('Bushfire','bushfire'),('Fuel Reduction Burn','planned_burn'),('Structure Fire','structure_fire'),('Unknown','other')]:
            self.engine.ledger['one']['record']['fields']['type']=source
            self.assertEqual(views(self.engine)[0]['category'],category)

    def test_missing_disputed_and_areas_are_not_map_candidates(self):
        for presence in ('not_in_snapshot','review_required'):
            state=deepcopy(self.engine);state.ledger['one']['presence']=presence
            self.assertEqual(views(state),[])
        state=deepcopy(self.engine);state.ledger['one']['record']['fields']['feedType']='burnt-area'
        self.assertEqual(views(state),[])
