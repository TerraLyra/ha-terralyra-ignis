import unittest
from datetime import date, datetime, timedelta, timezone
from urllib.parse import urlsplit, parse_qs
from urllib.error import HTTPError
from gwis_point import LABELS, MAX_BYTES, InvalidPoint, parse_point, point_url
from gwis_fetch import fetch_cycle


def table(value='0'):
    return ('<H2>Fire Danger</H2><table id="main">'+''.join(
        '<tr><td>'+label+'</td><td>'+value+'</td></tr>' for label in LABELS)+'</table>').encode()


class PointTests(unittest.TestCase):
    def test_zero_missing_and_empty_are_distinct(self):
        self.assertEqual(parse_point(table()).fwi, 0)
        self.assertEqual(parse_point(table()).status, 'numeric_evidence')
        self.assertEqual(parse_point(table('-9999')).status, 'nodata')
        self.assertIsNone(parse_point(table('-9999')).fwi)
        self.assertEqual(parse_point(b' \n').status, 'no_feature')

    def test_preserves_raw_numeric_evidence(self):
        result = parse_point(table('17.294014'))
        self.assertEqual(result.fwi, 17.294014)
        self.assertEqual(result.raw_values[0], (LABELS[0], '17.294014'))

    def test_rejects_bad_numbers(self):
        for value in ['nan', 'inf', '1e999', '-1', '1,2', '', 'True']:
            with self.subTest(value=value), self.assertRaises(InvalidPoint):
                parse_point(table(value))

    def test_rejects_html_injection_errors_and_ambiguous_tables(self):
        for raw in [b'<html>maintenance</html>', b'<ServiceExceptionReport/>',
                    table()+table(), table().replace(b'0</td>', b'<script>0</script></td>', 1),
                    table().replace(b'</table>',b''), table().replace(b'id="main"',b'id="other"'),
                    table().replace(b'Fire Weather Index (FWI)',b'unknown'),
                    b'<!DOCTYPE html>'+table(), b'<!--comment-->'+table(), b'\xff',
                    table()+b'\x00', b'x'*(MAX_BYTES+1)]:
            with self.subTest(size=len(raw)), self.assertRaises(InvalidPoint):
                parse_point(raw)

    def test_request_axis_order_and_exact_day(self):
        query = parse_qs(urlsplit(point_url(45,15,date(2026,10,1))).query)
        self.assertEqual(query['BBOX'], ['14.9500000000,44.9500000000,15.0500000000,45.0500000000'])
        self.assertEqual(query['TIME'], ['2026-10-01'])
        self.assertEqual(query['QUERY_LAYERS'], ['ecmwf.query'])
        self.assertEqual(query['X'], ['50'])

    def test_rejects_unsupported_geometry(self):
        for lat,lon in [(True,1),(float('nan'),1),(86,1),(0,180),(0,float('inf'))]:
            with self.assertRaises(ValueError): point_url(lat,lon,date(2026,10,1))


class CycleTests(unittest.TestCase):
    def setUp(self):
        self.clock = datetime(2026,10,1,12,tzinfo=timezone.utc)
        self.calls=[]
        self.sleeps=[]

    def run_cycle(self, **kw):
        return fetch_cycle(45,15,self.clock.date(), sleep=self.sleeps.append,
            now=lambda:self.clock, **kw)

    def test_bounded_ten_days_preserve_unknown_issuance(self):
        def reader(url): self.calls.append(url); return table()
        result=self.run_cycle(reader=reader)
        self.assertEqual(len(self.calls),10)
        self.assertEqual(self.sleeps,[1]*9)
        self.assertIsNone(result.model_issued_at)
        self.assertIsNone(result.returned_valid_date)
        self.assertFalse(result.production_ready)
        self.assertEqual(result.days[-1].requested_date,date(2026,10,10))

    def test_stops_on_rate_limit_without_retry(self):
        def reader(url): self.calls.append(url); raise HTTPError(url,429,'limited',{},None)
        with self.assertRaises(HTTPError): self.run_cycle(reader=reader)
        self.assertEqual(len(self.calls),1)
        self.assertEqual(self.sleeps,[])

    def test_missing_is_not_zero_or_cycle_failure(self):
        result=self.run_cycle(reader=lambda u:b'',days=1)
        self.assertEqual(result.days[0].evidence.status,'no_feature')
        self.assertIsNone(result.days[0].evidence.fwi)

    def test_invalid_window_never_fetches(self):
        for days in [0,11,True,1.5]:
            with self.assertRaises(ValueError): self.run_cycle(days=days,reader=lambda u:self.fail('network'))
        with self.assertRaises(ValueError):
            fetch_cycle(45,15,date(2020,1,1),now=lambda:self.clock,reader=lambda u:self.fail('network'))

    def test_midnight_rejects_result(self):
        clocks=iter([self.clock,self.clock+timedelta(days=1)])
        with self.assertRaises(ValueError):
            fetch_cycle(45,15,self.clock.date(),days=1,reader=lambda u:table(),now=lambda:next(clocks))

    def test_malformed_day_does_not_return_partial_cycle(self):
        payloads=iter([table(),b'<html>error</html>'])
        with self.assertRaises(InvalidPoint): self.run_cycle(days=2,reader=lambda u:next(payloads))


if __name__=='__main__': unittest.main()
