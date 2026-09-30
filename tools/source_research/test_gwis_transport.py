"""Transport boundaries use synthetic responses, never live requests."""
from email.message import Message
from unittest import TestCase
from unittest.mock import patch
from urllib.error import HTTPError
from gwis_fetch import read_point, _NoRedirect
from gwis_point import MAX_BYTES


class Response:
    def __init__(self, body=b'', status=200, content_type='text/html', encoding='identity'):
        self.status=status
        self.body=body
        self.headers=Message()
        self.headers['Content-Type']=content_type
        self.headers['Content-Encoding']=encoding
        self.read_sizes=[]
    def __enter__(self): return self
    def __exit__(self,*args): return False
    def read(self,size): self.read_sizes.append(size); return self.body[:size]


class TransportTests(TestCase):
    def call(self,response):
        with patch('gwis_fetch.build_opener') as opener:
            opener.return_value.open.return_value=response
            result=read_point('https://maps.effis.emergency.copernicus.eu/gwis?test')
            req=opener.return_value.open.call_args.args[0]
            self.assertEqual(req.get_header('Accept-encoding'),'identity')
            self.assertEqual(opener.return_value.open.call_args.kwargs['timeout'],20)
            return result

    def test_bounded_empty_html_is_preserved(self):
        r=Response()
        self.assertEqual(self.call(r),b'')
        self.assertEqual(r.read_sizes,[MAX_BYTES+1])

    def test_wrong_mime_compression_status_and_oversize(self):
        for r in [Response(status=503),Response(content_type='image/png'),
                  Response(encoding='gzip'),Response(body=b'x'*(MAX_BYTES+1))]:
            with self.subTest(response=r),self.assertRaises(ValueError): self.call(r)

    def test_redirect_handler_does_not_follow(self):
        self.assertIsNone(_NoRedirect().redirect_request(None,None,302,'',{},'https://elsewhere.invalid/'))

    def test_http_failure_propagates_without_retry(self):
        with patch('gwis_fetch.build_opener') as opener:
            opener.return_value.open.side_effect=HTTPError('url',429,'limited',{},None)
            with self.assertRaises(HTTPError): read_point('https://maps.effis.emergency.copernicus.eu/gwis')
            self.assertEqual(opener.return_value.open.call_count,1)

    def test_other_endpoints_rejected_before_network(self):
        for url in ['http://maps.effis.emergency.copernicus.eu/gwis',
                    'https://example.org/gwis',
                    'https://user@maps.effis.emergency.copernicus.eu/gwis',
                    'https://maps.effis.emergency.copernicus.eu/other',
                    'https://maps.effis.emergency.copernicus.eu/gwis#fragment']:
            with self.subTest(url=url), patch('gwis_fetch.build_opener') as opener:
                with self.assertRaises(ValueError): read_point(url)
                opener.assert_not_called()
