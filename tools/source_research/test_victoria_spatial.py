import unittest
from victoria_spatial import inspect_record,summarize_spatial

class VictoriaSpatialTests(unittest.TestCase):
    def test_exact_fire_subtypes(self):
        for subtype,label in (('Bushfire','vegetation_fire_candidate'),('Building','structure_fire'),
                              ('False Alarm','reported_false_alarm'),('Other','fire_unspecified'),
                              ('Unknown future value','fire_unspecified'),(None,'fire_unspecified')):
            with self.subTest(subtype=subtype):
                self.assertEqual(inspect_record({'category1':'Fire','category2':subtype}).category,label)

    def test_no_free_text_or_agency_inference(self):
        for category,label in (('Medical','medical'),('Accident / Rescue','accident_rescue'),
                               ('Other','other'),('Planned Burn','unknown'),(' fire ','unknown'),(None,'unknown')):
            record={'category1':category,'category2':'Bushfire','name':'TEST ONLY bushfire',
                    'agency':'Fire','incidentStatus':'Safe'}
            self.assertEqual(inspect_record(record).category,label)

    def test_source_is_retained_unchanged(self):
        record={'category1':'Fire','category2':'Bushfire','name':'NO ACTION REQUIRED',
                'latitude':-37.5,'longitude':145.5,'incidentStatus':'Safe'}
        result=inspect_record(record)
        self.assertEqual(dict(result.upstream),record)
        self.assertEqual(result.category,'vegetation_fire_candidate')
        self.assertEqual((result.latitude,result.longitude),(-37.5,145.5))

    def test_global_bounds_without_jurisdiction_guess(self):
        for lat,lon in ((-90,-180),(90,180),(0,0),(51,0)):
            result=inspect_record({'latitude':lat,'longitude':lon})
            self.assertEqual(result.location_status,'valid_point')
            self.assertEqual((result.latitude,result.longitude),(lat,lon))

    def test_invalid_not_swapped_clamped_or_coerced(self):
        for lat,lon in ((145,-37),(91,1),(1,181),(True,1),('12',1),(1,'12'),
                        (float('nan'),1),(1,float('inf')),(10**400,1)):
            with self.subTest(lat=lat,lon=lon):
                result=inspect_record({'latitude':lat,'longitude':lon})
                self.assertEqual(result.location_status,'invalid')
                self.assertIsNone(result.latitude);self.assertIsNone(result.longitude)

    def test_missing_partial_and_no_home_fallback(self):
        self.assertEqual(inspect_record({}).location_status,'missing')
        for record in ({'latitude':1},{'longitude':1},{'latitude':None,'longitude':1}):
            result=inspect_record(record)
            self.assertEqual(result.location_status,'incomplete')
            self.assertIsNone(result.latitude);self.assertIsNone(result.longitude)

    def test_aggregate_does_not_leak_unknown_fields(self):
        rows=[{'category1':'PRIVATE','name':'SECRET','latitude':-37.123,'longitude':145.123},
              {'category1':'Fire','category2':'Building'}]
        self.assertEqual(summarize_spatial(rows),{'status':'experimental',
            'production_readiness':'not_established','record_count':2,
            'categories':{'structure_fire':1,'unknown':1},'locations':{'missing':1,'valid_point':1}})
