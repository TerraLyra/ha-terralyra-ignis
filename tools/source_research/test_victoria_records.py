import unittest
from datetime import datetime,timezone
from victoria_records import inspect_update,inspect_id,summarize_records,compare_ids


def row(utc,local):
    epoch=datetime(1970,1,1,tzinfo=timezone.utc)
    delta=utc-epoch
    return {'incidentNo':1,'lastUpdatedDt':delta.days*86400000+delta.seconds*1000+delta.microseconds//1000,
            'lastUpdateDateTime':local}

class VictoriaRecordsTests(unittest.TestCase):
    def test_winter_summer_and_raw_preservation(self):
        for month,hour in ((7,2),(1,1)):
            record=row(datetime(2026,month,1,hour,tzinfo=timezone.utc),f'01/{month:02}/2026 12:00:00')
            result=inspect_update(record)
            self.assertEqual(result.status,'match_unverified')
            self.assertEqual(result.raw_local,record['lastUpdateDateTime'])
            self.assertEqual(result.raw_epoch,record['lastUpdatedDt'])

    def test_fold_both_instants_and_gap(self):
        for hour in (15,16):
            result=inspect_update(row(datetime(2026,4,4,hour,30,tzinfo=timezone.utc),'05/04/2026 02:30:00'))
            self.assertEqual(result.status,'fold_match_unverified')
        self.assertEqual(inspect_update(row(datetime(2026,10,3,16,30,tzinfo=timezone.utc),'04/10/2026 02:30:00')).status,'nonexistent_local_time')

    def test_conflicts_precision_and_invalid_values(self):
        record=row(datetime(2026,7,1,2,0,0,123000,tzinfo=timezone.utc),'01/07/2026 12:00:00')
        self.assertEqual(inspect_update(record).status,'match_unverified')
        record['lastUpdateDateTime']='01/07/2026 13:00:00'
        self.assertEqual(inspect_update(record).status,'conflict')
        for value in (True,1.2,'123',10**100):
            self.assertEqual(inspect_update({'lastUpdatedDt':value}).status,'invalid_epoch')
        for value in ('31/02/2026 12:00:00','07/01/26 12:00:00',False):
            record['lastUpdateDateTime']=value
            self.assertEqual(inspect_update(record).status,'invalid_local')

    def test_no_date_fallback(self):
        self.assertEqual(inspect_update({'originDateTime':'01/07/2026 12:00:00'}).status,'missing_epoch')
        self.assertIsNone(inspect_update({'lastUpdateDateTime':'01/07/2026 12:00:00'}).epoch_candidate)
        self.assertEqual(inspect_update({'lastUpdatedDt':0}).status,'missing_local')

    def test_identity_types_and_duplicates(self):
        self.assertNotEqual(inspect_id({'incidentNo':1})[1],inspect_id({'incidentNo':'1'})[1])
        for value in (True,0,-1,1.0,'',' a','a\n'):
            self.assertEqual(inspect_id({'incidentNo':value})[0],'invalid')
        records=[{'incidentNo':1},{'incidentNo':1},{'incidentNo':'1'}]
        summary=summarize_records(records)
        self.assertEqual(summary['duplicate_id_groups'],1)
        self.assertEqual(summary['identity'],{'candidate':3})
        self.assertEqual(records[0],{'incidentNo':1})

    def test_snapshot_comparison_no_closure_or_stability_claim(self):
        self.assertEqual(compare_ids([{'incidentNo':1}],[{'incidentNo':2}]),
                         {'shared':0,'only_before':1,'only_after':1,'identity_stability':'not_established'})
        for bad in ([{}],[{'incidentNo':1},{'incidentNo':1}]):
            with self.assertRaises(ValueError):compare_ids(bad,[])

    def test_diagnostics_exclude_source_content(self):
        summary=summarize_records([{'incidentNo':'SECRET','lastUpdateDateTime':'PRIVATE'}])
        self.assertNotIn('SECRET',str(summary));self.assertNotIn('PRIVATE',str(summary))
