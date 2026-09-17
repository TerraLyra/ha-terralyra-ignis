import json
import unittest
from victoria_feed import inspect_feed, summarize_feed, InvalidFeed

class VictoriaFeedTests(unittest.TestCase):
    def test_original_fields_preserved_without_semantic_inference(self):
        record={'incidentNo':'synthetic-1','category1':'Unknown future type',
                'lastUpdatedDt':123,'name':'TEST ONLY – unchanged','extra':None}
        self.assertEqual(inspect_feed(json.dumps({'results':[record]}).encode()),(record,))

    def test_empty_success_is_distinct_from_bad_response(self):
        self.assertEqual(inspect_feed(b'{"results":[]}'),())
        for raw in (b'{}',b'[]',b'{"results":null}',b'{"results":{}}',
                    b'{"results":[],"error":"partial"}',b'<html>error</html>'):
            with self.subTest(raw=raw), self.assertRaises(InvalidFeed):
                inspect_feed(raw)

    def test_duplicate_fields_and_nonfinite_rejected(self):
        for raw in (b'{"results":[],"results":[]}',
                    b'{"results":[{"x":1,"x":2}]}',
                    b'{"results":[{"x":NaN}]}',b'{"results":[{"x":1e999}]}'):
            with self.subTest(raw=raw), self.assertRaises(InvalidFeed):
                inspect_feed(raw)

    def test_no_partial_results(self):
        for bad in ({},[],None,{'nested':{'x':1}},{'nested':[1]}):
            with self.subTest(bad=bad), self.assertRaises(InvalidFeed):
                inspect_feed(json.dumps({'results':[{'incidentNo':'ok'},bad]}).encode())

    def test_limits_and_encoding(self):
        for kwargs in ({'max_bytes':True},{'max_records':0}):
            with self.assertRaises(ValueError): inspect_feed(b'{}',**kwargs)
        with self.assertRaises(InvalidFeed): inspect_feed(b'{"results":[]}',max_bytes=2)
        with self.assertRaises(InvalidFeed): inspect_feed(b'{"results":[{"x":1},{"x":2}]}',max_records=1)
        with self.assertRaises(InvalidFeed): inspect_feed(b'\xff')
        with self.assertRaises(InvalidFeed): inspect_feed(b'['*2000+b']'*2000)
        self.assertEqual(inspect_feed(b'\xef\xbb\xbf{"results":[]}'),())

    def test_summary_does_not_disclose_incident_content(self):
        summary=summarize_feed(b'{"results":[{"incidentNo":"secret","latitude":12,"name":"private"}]}')
        self.assertEqual(summary,{'purpose':'offline_source_research','status':'experimental',
                                 'production_readiness':'not_established','record_count':1})
