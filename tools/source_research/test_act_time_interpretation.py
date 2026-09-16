import unittest
from datetime import datetime, timezone
from act_times import SourceTime
from act_time_interpretation import interpret, ENABLED_BY_DEFAULT

class InterpretationTests(unittest.TestCase):
    def source(self, month, day=1, hour=12, minute=0, label=''):
        return SourceTime(('unchanged upstream',), 'timezone_unverified',
                          datetime(2026, month, day, hour, minute), label)

    def test_winter_and_summer(self):
        for month, label, utc_hour in ((7, 'AEST', 2), (1, 'AEDT', 1)):
            for supplied_label in ('', label):
                source = self.source(month, label=supplied_label)
                result = interpret(source)
                self.assertEqual(result.instant, datetime(2026,month,1,utc_hour,tzinfo=timezone.utc))
                self.assertEqual(result.status, 'provider_interpretation_unverified')
                self.assertIs(result.source, source)
        self.assertFalse(ENABLED_BY_DEFAULT)

    def test_gap_fold_and_labels(self):
        self.assertEqual(interpret(self.source(10,4,2,30)).status, 'nonexistent_local_time')
        self.assertEqual(interpret(self.source(4,5,2,30)).status, 'ambiguous_local_time')
        standard = interpret(self.source(4,5,2,30,'AEST')).instant
        summer = interpret(self.source(4,5,2,30,'AEDT')).instant
        self.assertEqual((standard-summer).total_seconds(), 3600)
        self.assertEqual(interpret(self.source(1,label='AEST')).status, 'zone_label_conflict')
        self.assertEqual(interpret(self.source(7,label='AEDT')).status, 'zone_label_conflict')

    def test_transition_boundaries(self):
        for month,day,hour,minute in ((4,5,1,59),(4,5,3,0),(10,4,1,59),(10,4,3,0)):
            self.assertIsNotNone(interpret(self.source(month,day,hour,minute)).instant)

    def test_missing_invalid_no_fallback(self):
        for status in ('missing','invalid','duplicate'):
            result = interpret(SourceTime((),status))
            self.assertEqual(result.status,status)
            self.assertIsNone(result.instant)

class ExplicitOffsetTests(unittest.TestCase):
    def test_offset_is_authoritative_not_sydney_override(self):
        from act_time_interpretation import inspect_explicit_offset
        raw = '2026-01-01T12:00:00+10:00'
        result = inspect_explicit_offset(raw)
        self.assertEqual(result.instant, datetime(2026,1,1,2,tzinfo=timezone.utc))
        self.assertEqual(result.source.raw_values,(raw,))
        self.assertEqual(result.status,'explicit_offset_semantics_unverified')
        self.assertEqual(inspect_explicit_offset('2026-01-01T12:00:00+11:00').instant.hour,1)
        self.assertEqual(inspect_explicit_offset('2026-01-01T12:00:00Z').instant.hour,12)

    def test_naive_invalid_and_malformed_offsets_not_guessed(self):
        from act_time_interpretation import inspect_explicit_offset
        for raw in ('2026-01-01T12:00:00','2026-02-30T12:00:00Z',
                    '2026-01-01T12:00:00+10:99',''):
            self.assertIsNone(inspect_explicit_offset(raw).instant)
