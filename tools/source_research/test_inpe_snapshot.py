from dataclasses import replace
from datetime import datetime, timezone, timedelta
from unittest import TestCase
from unittest.mock import Mock, patch
from inpe_centroids import parse_centroids, InvalidCentroids
from inpe_fetch import fetch_centroids
from inpe_snapshot import collect_states, report
from test_inpe_centroids import feature, payload
from test_gwis_transport import Response

NOW = datetime(2026, 9, 30, 12, tzinfo=timezone.utc)


def record(states=('AC','AM')):
    f=feature(); f['properties']['estados']=list(states)
    return parse_centroids(payload([f]),requested_state=states[0])[0]


class StateSnapshotTests(TestCase):
    def test_state_request_and_response_membership(self):
        f=feature(); f['properties']['estados']=['AC']
        with patch('inpe_fetch.build_opener') as opener:
            opener.return_value.open.return_value=Response(payload([f]),content_type='application/json')
            self.assertEqual(fetch_centroids(state='AC')[0].states,('AC',))
            self.assertTrue(opener.return_value.open.call_args.args[0].full_url.endswith('?uf=AC'))

    def test_bad_state_before_network(self):
        for state in ('xx','ac','AC&other=1',{},True):
            with patch('inpe_fetch.build_opener') as opener,self.assertRaises(ValueError):
                fetch_centroids(state=state)
            opener.assert_not_called()

    def test_wrong_missing_duplicate_memberships_rejected(self):
        for states in ([],['AM'],['AC','AC'],['XX'],None):
            f=feature(); f['properties']['estados']=states
            with self.assertRaises(InvalidCentroids): parse_centroids(payload([f]),requested_state='AC')

    def test_shared_event_retained_once_and_no_completeness_claim(self):
        fetch=Mock(return_value=(record(),)); sleep=Mock()
        snapshot=collect_states(['AM','AC'],fetch=fetch,sleep=sleep,now=lambda:NOW)
        self.assertEqual(len(snapshot.records),1)
        self.assertEqual(snapshot.requested_states,('AC','AM'))
        sleep.assert_called_once_with(1)
        result=report(snapshot)
        self.assertFalse(result['complete'])
        self.assertFalse(result['production_ready'])
        self.assertFalse(result['observation_time_known'])
        self.assertIn('by-sa/4.0',result['license_url'])
        self.assertEqual(result['events'][0]['status'],'Observação')

    def test_conflict_not_last_response_wins(self):
        fetch=Mock(side_effect=[(record(),),(replace(record(),area_ha=99),)])
        with self.assertRaises(ValueError): collect_states(['AC','AM'],fetch=fetch,sleep=lambda _:None,now=lambda:NOW)

    def test_failure_does_not_return_partial_or_retry(self):
        fetch=Mock(side_effect=[(record(),),OSError('unavailable')])
        with self.assertRaises(OSError): collect_states(['AC','AM'],fetch=fetch,sleep=lambda _:None,now=lambda:NOW)
        self.assertEqual(fetch.call_count,2)

    def test_invalid_plan_before_io(self):
        for states in ([],['AC','AC'],['AC','AM','MG','SP'],'AC',['XX']):
            fetch=Mock()
            with self.assertRaises(ValueError): collect_states(states,fetch=fetch,now=lambda:NOW)
            fetch.assert_not_called()

    def test_bad_retrieval_clock(self):
        clock=Mock(side_effect=[NOW,NOW-timedelta(seconds=1)])
        with self.assertRaises(ValueError): collect_states(['AC'],fetch=Mock(return_value=(record(),)),now=clock)
