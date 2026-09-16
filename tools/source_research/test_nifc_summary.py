from dataclasses import replace
from datetime import datetime, timedelta, timezone
import json
import unittest

from nifc_fetch import FetchResult
from nifc_records import normalize_page
from nifc_refresh import RefreshState, failed, succeeded
from nifc_summary import summarize
from test_nifc_records import sample


class SummaryTests(unittest.TestCase):
    def setUp(self):
        self.record=normalize_page(sample())[0]
        self.now=datetime(2026,9,16,tzinfo=timezone.utc)

    def summary(self,state,**kwargs):
        options=dict(now=self.now,monotonic_now=100,max_source_age=timedelta(hours=24),max_retrieval_age=timedelta(minutes=15))
        options.update(kwargs)
        return summarize(state,**options)

    def state(self,records):
        return succeeded(RefreshState(),FetchResult(records,1,100,'terminal_reported'),now=10)

    def test_no_response_is_not_zero_fires(self):
        output=self.summary(RefreshState())
        self.assertIsNone(output['source_record_count'])
        self.assertIsNone(output['active_fire_count'])
        self.assertEqual(output['availability'],'no_cached_response')

    def test_empty_terminal_response_does_not_claim_no_fires(self):
        output=self.summary(self.state(()))
        self.assertEqual(output['source_record_count'],0)
        self.assertIsNone(output['active_fire_count'])
        self.assertEqual(output['national_completeness'],'not_established')

    def test_recent_retrieval_does_not_refresh_old_source_time(self):
        output=self.summary(self.state((self.record,)))
        self.assertEqual(output['retrieval_age'],'within_threshold')
        self.assertEqual(output['records_by_modification_age']['older_than_threshold'],1)

    def test_retained_data_label_after_failure_and_no_mutation(self):
        original=self.state((self.record,))
        broken=failed(original,now=50,kind='transient')
        output=self.summary(broken)
        self.assertEqual(output['availability'],'retained_response')
        self.assertIs(broken.last_success,original.last_success)
        self.assertEqual(original.status,'retrieved')

    def test_distinct_categories_relationships_and_missing_values(self):
        parent=replace(self.record,irwin_id='parent',category='incident_complex',complex_child=False)
        member=replace(self.record,complex_child=True,parent_complex_id='parent')
        burn=replace(self.record,irwin_id='burn',category='prescribed_fire',latitude=None,longitude=None,discovered_at=None,modified_at=None)
        output=self.summary(self.state((parent,member,burn)))
        self.assertEqual(output['records_by_category'],{'wildfire':1,'prescribed_fire':1,'incident_complex':1})
        self.assertEqual(output['records_by_complex_role']['linked_complex_member'],1)
        self.assertEqual(output['missing_location_count'],1)
        self.assertEqual(output['missing_discovery_time_count'],1)
        self.assertEqual(output['records_by_modification_age']['unknown'],1)
        self.assertIsNone(output['active_fire_count'])

    def test_aggregate_output_has_no_raw_id_coordinates_or_dates(self):
        output=json.dumps(self.summary(self.state((self.record,))),allow_nan=False)
        for raw in (self.record.irwin_id,'-120','1970-01-01'):
            self.assertNotIn(raw,output)

    def test_invalid_thresholds_even_when_empty(self):
        for kwargs in ({'max_source_age':timedelta(0)}, {'now':datetime(2026,9,16)}, {'monotonic_now':float('nan')}):
            with self.assertRaises(ValueError): self.summary(RefreshState(),**kwargs)

    def test_clock_mismatch_and_unknown_receipt_are_not_recent(self):
        state=self.state((self.record,))
        self.assertEqual(self.summary(state,monotonic_now=0)['retrieval_age'],'clock_mismatch')
        self.assertEqual(self.summary(replace(state,last_success_at=None))['retrieval_age'],'unknown')
