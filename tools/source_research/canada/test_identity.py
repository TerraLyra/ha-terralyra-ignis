import unittest
from identity import report_identity

class IdentityTests(unittest.TestCase):
    def test_new_transport_and_revision_ids_preserve_fire_identity(self):
        a={'id':'transport-A','properties':{'id':1,'agency_code':'BC','national_fire_id':'2026_BC_example'}}
        b={'id':'transport-B','properties':{**a['properties'],'id':2}}
        self.assertEqual(report_identity(a),report_identity(b))

    def test_year_and_agency_distinguish_reports(self):
        a={'properties':{'agency_code':'BC','national_fire_id':'2026_BC_example'}}
        b={'properties':{'agency_code':'BC','national_fire_id':'2025_BC_example'}}
        self.assertNotEqual(report_identity(a),report_identity(b))

    def test_missing_id_is_not_replaced_with_unstable_transport_id(self):
        with self.assertRaises(ValueError):
            report_identity({'id':'transport-A','properties':{'agency_code':'BC'}})
