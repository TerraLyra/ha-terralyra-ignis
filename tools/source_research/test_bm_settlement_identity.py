import unittest
from bm_settlement_identity import bridge_identity, audit

class IdentityTests(unittest.TestCase):
    def test_exact_record_and_homonyms(self):
        rows=((1,'Town',47.,19.),(2,'Town',48.,20.))
        self.assertEqual(bridge_identity('Town','HU',47.,19.,rows),frozenset({'geonames:1'}))
        for name,country,lat,lon in [('Town','SK',47.,19.),('Town','HU',47.001,19.),('Other','HU',47.,19.)]:
            self.assertFalse(bridge_identity(name,country,lat,lon,rows))

    def test_duplicate_centres_and_invalid_coordinates(self):
        self.assertFalse(bridge_identity('Town','HU',47.,19.,((1,'Town',47.,19.),(2,'Town',47.,19.))))
        with self.assertRaises(ValueError):
            bridge_identity('Town','HU',float('nan'),19.,())

    def test_bundled_audit_is_nonempty_and_accounts_for_every_record(self):
        result=audit()
        self.assertGreater(result['exact_identity_matches'],0)
        self.assertEqual(result['cities500_hu_records'],result['exact_identity_matches']+result['unresolved'])
        self.assertFalse(result['production_enabled'])
