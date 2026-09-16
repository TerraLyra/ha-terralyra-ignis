import unittest
from nifc_pages import inspect_pages


def page(ids=(), flag=True):
    value={'objectIdFieldName':'OBJECTID','geometryType':'esriGeometryPoint',
           'spatialReference':{'wkid':4326},
           'features':[{'attributes':{'OBJECTID':oid}} for oid in ids]}
    if flag is not None: value['exceededTransferLimit']=flag
    return value


class SequenceTests(unittest.TestCase):
    def test_terminal_sequence_not_snapshot_proof(self):
        result=inspect_pages((page((1,3)),page((5,),False)))
        self.assertEqual((result.page_count,result.record_count,result.outcome),(2,3,'terminal_reported'))
        self.assertEqual(result.snapshot_consistency,'not_established')

    def test_missing_terminal_and_no_pages(self):
        self.assertEqual(inspect_pages((page((1,)),)).outcome,'incomplete')
        self.assertEqual(inspect_pages(()).outcome,'no_pages')
        self.assertEqual(inspect_pages((page((),None),)).outcome,'continuation_unknown')

    def test_empty_intermediate_page_not_terminal(self):
        result=inspect_pages((page((1,)),page(),page((2,),False)))
        self.assertEqual(result.record_count,2)
        self.assertEqual(result.outcome,'terminal_reported')

    def test_cross_page_duplicates_and_reversal_rejected(self):
        for ids in ((2,3),(1,)):
            with self.assertRaises(ValueError): inspect_pages((page((1,2)),page(ids,False)))
        with self.assertRaises(ValueError):
            inspect_pages((page((1,2)),page(),page((2,),False)))

    def test_late_error_cannot_return_partial_success(self):
        with self.assertRaises(ValueError): inspect_pages((page((1,)),{'error':{'code':500}}))

    def test_no_pages_after_terminal_or_unknown(self):
        for flag in (False,None):
            with self.assertRaises(ValueError): inspect_pages((page((1,),flag),page((2,),False)))

    def test_limits(self):
        pages=(page((1,)),page((2,),False))
        with self.assertRaises(ValueError): inspect_pages(pages,max_pages=1)
        with self.assertRaises(ValueError): inspect_pages(pages,max_records=1)
        with self.assertRaises(ValueError): inspect_pages((page((1,2),False),),max_page_records=1)
        for field in ('max_pages','max_records','max_page_records'):
            for value in (True,0,-1,1.5):
                with self.assertRaises(ValueError): inspect_pages((),**{field:value})

    def test_input_is_not_mutated(self):
        original=page((1,),False)
        import copy
        before=copy.deepcopy(original)
        inspect_pages((original,))
        self.assertEqual(original,before)
