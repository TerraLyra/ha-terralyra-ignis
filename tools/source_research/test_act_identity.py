import unittest
from act_feed import ActItem
from act_identity import inspect_identity_location, repeated_ids, POINT


def record(guid='synthetic-1', cadid='synthetic-1', point='-35.3 149.1'):
    return ActItem(tuple((k,v) for k,v in (('guid',guid),('cadid',cadid),(POINT,point)) if v is not None))


class IdentityTests(unittest.TestCase):
    def test_matching_identity_and_georss_order(self):
        result = inspect_identity_location(record())
        self.assertEqual(result.identity_status, 'matching_pair')
        self.assertEqual(result.source_id, 'synthetic-1')
        self.assertEqual((result.latitude,result.longitude), (-35.3,149.1))

    def test_missing_incomplete_and_conflicting_ids(self):
        for guid,cadid,status in [(None,None,'missing'),('', '','missing'),
                                 ('a',None,'incomplete'),(None,'a','incomplete'),
                                 ('a','b','conflict')]:
            with self.subTest(status=status):
                result = inspect_identity_location(record(guid,cadid))
                self.assertEqual(result.identity_status,status)
                self.assertIsNone(result.source_id)

    def test_identity_is_case_sensitive_and_only_trimmed(self):
        self.assertEqual(inspect_identity_location(record(' a ','a')).source_id, 'a')
        self.assertEqual(inspect_identity_location(record('a','A')).identity_status, 'conflict')

    def test_invalid_points_do_not_get_swapped_or_clamped(self):
        for value in ('149.1 -35.3','-91 149','0 181','NaN 1','1 Infinity',
                      '1','1 2 3','x y','1e9999 2','3_5 149','٣٥ 149'):
            with self.subTest(value=value):
                result=inspect_identity_location(record(point=value))
                self.assertEqual(result.location_status,'invalid')
                self.assertIsNone(result.latitude)
                self.assertIsNone(result.longitude)

    def test_missing_points_and_boundaries(self):
        for value in (None,'','  '):
            self.assertEqual(inspect_identity_location(record(point=value)).location_status,'missing')
        for value in ('-90 -180','90 180','0 0'):
            self.assertEqual(inspect_identity_location(record(point=value)).location_status,'valid_point')

    def test_repeated_ids_reported_without_merging(self):
        items=(record(),record(point='-35.4 149.2'),record('b','b'),record('b','b'))
        self.assertEqual(repeated_ids(items),('b','synthetic-1'))
        self.assertEqual(len(items),4)

    def test_duplicate_fields_rejected(self):
        with self.assertRaises(ValueError):
            inspect_identity_location(ActItem((('guid','a'),('guid','b'))))
