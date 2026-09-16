from dataclasses import replace
from datetime import datetime, timedelta, timezone
import unittest

from nifc_assessment import source_age, complex_roles
from nifc_records import normalize_page
from test_nifc_records import sample


class AssessmentTests(unittest.TestCase):
    def setUp(self): self.record=normalize_page(sample())[0]

    def test_source_age_missing_future_boundary_and_old(self):
        now=datetime(2026,9,16,tzinfo=timezone.utc); limit=timedelta(hours=1)
        for modified,expected in [(None,'unknown'),(now+timedelta(seconds=1),'future_source_time'),
                                  (now-limit,'within_threshold'),(now-limit-timedelta(seconds=1),'older_than_threshold')]:
            self.assertEqual(source_age(replace(self.record,modified_at=modified),now=now,max_age=limit),expected)

    def test_explicit_aware_clock_and_positive_threshold_required(self):
        for now,limit in [(datetime(2026,9,16),timedelta(hours=1)),
                          (datetime(2026,9,16,tzinfo=timezone.utc),timedelta(0))]:
            with self.assertRaises(ValueError): source_age(self.record,now=now,max_age=limit)

    def test_complex_and_member_are_distinct_roles(self):
        parent=replace(self.record,irwin_id='parent',category='incident_complex',complex_child=False)
        child=replace(self.record,complex_child=True,parent_complex_id='parent')
        self.assertEqual(complex_roles((parent,child)),('complex_container','linked_complex_member'))
        self.assertEqual(complex_roles((child,)),('parent_not_in_result',))

    def test_unknown_membership_is_not_independent(self):
        self.assertEqual(complex_roles((self.record,)),('relationship_unknown',))
        self.assertEqual(complex_roles((replace(self.record,complex_child=False),)),('reported_non_child',))

    def test_invalid_parent_type_and_nested_complex_not_flattened(self):
        parent=replace(self.record,irwin_id='parent',complex_child=False)
        child=replace(self.record,complex_child=True,parent_complex_id='parent')
        self.assertEqual(complex_roles((parent,child))[1],'parent_relationship_conflict')
        nested=replace(parent,category='incident_complex',parent_complex_id='ancestor',complex_child=True)
        self.assertEqual(complex_roles((nested,child)),('complex_relationship_unresolved','parent_relationship_conflict'))

    def test_duplicate_ids_rejected(self):
        with self.assertRaises(ValueError): complex_roles((self.record,self.record))

    def test_normalization_validates_relationship_fields(self):
        for child,parent in [(True,None),(2,None),(0,'12345678-1234-1234-1234-123456789abd'),
                             (1,self.record.irwin_id),(1,'bad')]:
            page=sample(); page['features'][0]['attributes'].update(IsCpxChild=child,CpxID=parent)
            with self.subTest(child=child,parent=parent),self.assertRaises(ValueError): normalize_page(page)
        page=sample(); page['features'][0]['attributes'].update(IsCpxChild=1,CpxID='12345678-1234-1234-1234-123456789abd')
        result=normalize_page(page)[0]
        self.assertTrue(result.complex_child)
        self.assertEqual(result.parent_complex_id,'12345678-1234-1234-1234-123456789abd')
