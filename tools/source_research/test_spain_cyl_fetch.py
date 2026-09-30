import json
from datetime import date,datetime
from unittest import TestCase
from unittest.mock import Mock,patch
from urllib.parse import parse_qs,urlsplit
from urllib.error import HTTPError
from spain_cyl_fetch import page_url,collect_date,_read,_NoRedirect
from spain_cyl_review import MAX_BYTES
from test_gwis_transport import Response

DAY=date(2026,9,29)


def sample(total=1,day='2026-09-29'):
    return json.dumps({'total_count':total,'results':[{'fecha_del_parte':day,'hora_del_parte':'19:00',
                      'provincia':['VALLADOLID'],'termino_municipal':'SIN INCIDENCIAS'}]}).encode()


class DateClientTests(TestCase):
    def test_explicit_query(self):
        query=parse_qs(urlsplit(page_url(DAY,0,100)).query)
        self.assertEqual(query['where'],["fecha_del_parte=date'2026-09-29'"])
        self.assertEqual(query['limit'],['100'])

    def test_invalid_input_before_io(self):
        for day in ('2026-09-29',datetime(2026,9,29),None):
            reader=Mock()
            with self.assertRaises(ValueError):collect_date(day,reader=reader)
            reader.assert_not_called()

    def test_counts_never_promote_snapshot(self):
        result=collect_date(DAY,reader=lambda _:sample())
        self.assertTrue(result['count_complete'])
        self.assertFalse(result['snapshot_verified'])
        self.assertEqual(result['requested_date'],DAY.isoformat())

    def test_partial_and_wrong_date(self):
        partial=collect_date(DAY,reader=lambda _:sample(total=101))
        self.assertFalse(partial['count_complete'])
        wrong=collect_date(DAY,reader=lambda _:sample(day='2026-09-28'))
        self.assertEqual(wrong['reason'],'page_error')
        self.assertEqual(wrong['results'],[])

    def test_http_failure_is_not_empty_success(self):
        reader=Mock(side_effect=HTTPError('url',429,'limited',{},None))
        result=collect_date(DAY,reader=reader)
        self.assertFalse(result['count_complete'])
        self.assertEqual(result['reason'],'page_error')
        self.assertEqual(reader.call_count,1)

    def test_transport_and_redirect(self):
        with patch('spain_cyl_fetch.build_opener') as opener:
            opener.return_value.open.return_value=Response(sample(),content_type='application/json')
            self.assertEqual(_read(page_url(DAY,0,100)),sample())
        self.assertIsNone(_NoRedirect().redirect_request(None,None,302,'',{},'https://other.invalid'))

    def test_transport_rejects_html_and_compressed(self):
        for response in (Response(sample()),Response(sample(),content_type='application/json',encoding='gzip')):
            with patch('spain_cyl_fetch.build_opener') as opener,self.assertRaises(ValueError):
                opener.return_value.open.return_value=response
                _read(page_url(DAY,0,100))

    def test_empty_is_not_verified_all_clear(self):
        result=collect_date(DAY,reader=lambda _:b'{"total_count":0,"results":[]}')
        self.assertTrue(result['count_complete'])
        self.assertFalse(result['snapshot_verified'])

    def test_transport_rejects_status_and_oversize(self):
        for response in (Response(status=503,content_type='application/json'),
                         Response(b'x'*(MAX_BYTES+1),content_type='application/json')):
            with patch('spain_cyl_fetch.build_opener') as opener,self.assertRaises(ValueError):
                opener.return_value.open.return_value=response
                _read(page_url(DAY,0,100))
