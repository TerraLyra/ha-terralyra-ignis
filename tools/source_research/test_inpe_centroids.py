import json
from unittest import TestCase
from unittest.mock import patch
from urllib.error import HTTPError
from inpe_centroids import parse_centroids, InvalidCentroids, compare_kml
from inpe_fetch import fetch_centroids, _NoRedirect
from test_gwis_transport import Response
from inpe_events import inspect_events
from test_inpe_events import event, wrap


def feature():
    return {'type':'Feature','geometry':{'type':'Point','coordinates':[-50,-10]},
            'properties':{'id_evento':1,'tipo':'Incêndio','status':'Observação',
                          'area_ha':12.5,'duracao_dias':3,'estado':'PARÁ','municipio':'Example'}}


def payload(features=None, **extra):
    return json.dumps(dict(type='FeatureCollection',features=[feature()] if features is None else features,
                           **extra)).encode()


class CentroidTests(TestCase):
    def test_preserves_observation_and_unknown_categories_without_dates(self):
        f=feature(); f['properties']['tipo']='New category'; f['properties']['area_ha']=None
        record=parse_centroids(payload([f]))[0]
        self.assertEqual(record.category,'New category')
        self.assertEqual(record.status,'Observação')
        self.assertIsNone(record.area_ha)
        self.assertIsNone(record.observed_at)
        self.assertTrue(record.provisional)

    def test_rejects_empty_duplicates_and_error_envelopes(self):
        for raw in (payload([]),payload([feature(),feature()]),payload(error='broken'),
                    payload(next='page2'),payload(crs={}),b'{"type":1,"type":2}',b'{'):
            with self.subTest(raw=raw[:30]),self.assertRaises(InvalidCentroids): parse_centroids(raw)

    def test_invalid_properties(self):
        for field,value in [('id_evento',True),('id_evento',0),('area_ha',-1),
                            ('area_ha',10**400),('duracao_dias',float('nan')),('tipo',''),('status',None)]:
            f=feature(); f['properties'][field]=value
            with self.subTest(field=field),self.assertRaises(InvalidCentroids): parse_centroids(payload([f]))

    def test_invalid_geometry(self):
        for c in ([181,0],[0,91],[True,0],[0,float('inf')],[1,2,3]):
            f=feature(); f['geometry']['coordinates']=c
            with self.subTest(c=c),self.assertRaises(InvalidCentroids): parse_centroids(payload([f]))

    def test_byte_limit(self):
        with patch('inpe_centroids.MAX_BYTES',10),self.assertRaises(InvalidCentroids): parse_centroids(payload())

    def test_overlap_is_diagnostic_only(self):
        before=parse_centroids(payload())
        kml=inspect_events(wrap(event()+event('2')),collection='active')
        report=compare_kml(before,kml)
        self.assertEqual(report['shared_ids'],1)
        self.assertEqual(report['only_kml'],1)
        self.assertEqual(len(before),1)

    def test_transport(self):
        response=Response(payload(),content_type='application/json')
        with patch('inpe_fetch.build_opener') as opener:
            opener.return_value.open.return_value=response
            self.assertEqual(len(fetch_centroids()),1)
            self.assertEqual(opener.return_value.open.call_count,1)

    def test_transport_rejects_wrong_type_compression_truncation(self):
        cases=[Response(payload()),Response(payload(),content_type='application/json',encoding='gzip')]
        truncated=Response(payload(),content_type='application/json')
        truncated.headers['Content-Length']=str(len(payload())+1); cases.append(truncated)
        for response in cases:
            with patch('inpe_fetch.build_opener') as opener,self.assertRaises(ValueError):
                opener.return_value.open.return_value=response
                fetch_centroids()

    def test_rate_limit_no_retry_and_no_redirect(self):
        with patch('inpe_fetch.build_opener') as opener:
            opener.return_value.open.side_effect=HTTPError('url',429,'limited',{},None)
            with self.assertRaises(HTTPError): fetch_centroids()
            self.assertEqual(opener.return_value.open.call_count,1)
        self.assertIsNone(_NoRedirect().redirect_request(None,None,302,'',{},'https://elsewhere.invalid'))
