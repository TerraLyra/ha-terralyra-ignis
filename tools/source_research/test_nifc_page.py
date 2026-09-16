import unittest
from nifc_page import inspect_page


def page(ids=(), **extra):
    return dict(objectIdFieldName='OBJECTID', geometryType='esriGeometryPoint',
                spatialReference={'wkid':4326},
                features=[{'attributes':{'OBJECTID':i}} for i in ids], **extra)


class PageTests(unittest.TestCase):
    def test_short_and_empty_pages_can_have_more(self):
        for ids in ((), (1,)):
            self.assertEqual(inspect_page(page(ids,exceededTransferLimit=True)).continuation,'more')

    def test_missing_flag_never_means_complete(self):
        for ids in ((),(1,2)):
            self.assertEqual(inspect_page(page(ids)).continuation,'unknown')

    def test_explicit_terminal_report(self):
        result=inspect_page(page((1,2),exceededTransferLimit=False))
        self.assertEqual(result.continuation,'terminal_reported')
        self.assertEqual(result.record_count,2)
        self.assertEqual(result.object_ids,(1,2))

    def test_error_response_is_not_empty_success(self):
        for value in ({'error':{'code':500}},None,[],dict(page(),error={})): 
            with self.assertRaises(ValueError): inspect_page(value)

    def test_id_and_order_problems(self):
        for ids in ((1,1),(2,1),(True,),(-1,),('1',),(None,)):
            with self.subTest(ids=ids), self.assertRaises(ValueError): inspect_page(page(ids))

    def test_flags_are_strict_booleans(self):
        for flag in (0,1,'false',None):
            with self.assertRaises(ValueError): inspect_page(page(exceededTransferLimit=flag))

    def test_bounds(self):
        with self.assertRaises(ValueError): inspect_page(page((1,2)),max_records=1)
        for limit in (True,0,-1,1.5):
            with self.assertRaises(ValueError): inspect_page(page(),max_records=limit)

    def test_schema_and_crs(self):
        for key,value in [('geometryType','esriGeometryPolygon'),('objectIdFieldName','other'),
                          ('spatialReference',{'wkid':4269}),('features',{}),
                          ('spatialReference',{'wkid':4326,'latestWkid':4269})]:
            bad=page();bad[key]=value
            with self.assertRaises(ValueError): inspect_page(bad)
