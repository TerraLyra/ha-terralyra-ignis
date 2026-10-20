import json
from unittest import TestCase
from inpe_detail import parse_detail_times, time_report


def payload(**patch):
    return json.dumps(dict(id_evento=12, data_min='2026-10-01',
        data_max='2026-10-19', data_ultimo_foco='2026-10-20 04:30:00', **patch)).encode()


class DetailTests(TestCase):
    def test_hotspot_can_be_newer_than_geometry_day_range(self):
        r = time_report(parse_detail_times(payload(), expected_id=12))
        self.assertEqual(r['source_last_day_utc'], '2026-10-19')
        self.assertEqual(r['latest_hotspot_at_utc'], '2026-10-20T04:30:00+00:00')
        self.assertTrue(r['provisional'])
        self.assertNotIn('extinguished_at', r)

    def test_missing_times_stay_unknown(self):
        r = time_report(parse_detail_times(b'{"id_evento":12}', expected_id=12))
        self.assertIsNone(r['latest_hotspot_at_utc'])
        self.assertIsNone(r['source_first_day_utc'])

    def test_wrong_ids_and_envelopes(self):
        for raw in (b'{"id_evento":13}', b'{"id_evento":true}',
                    b'{"id_evento":12,"error":"bad"}', b'[]',
                    b'{"id_evento":12,"id_evento":12}', b'{'):
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                parse_detail_times(raw, expected_id=12)

    def test_wrong_precision_and_order_are_rejected(self):
        for patch in ({'data_min':'2026-10-01T00:00:00'},
                      {'data_ultimo_foco':'2026-10-20'},
                      {'data_min':'2026-10-21'}, {'data_max':'bad'}):
            data=json.loads(payload()); data.update(patch)
            with self.subTest(patch=patch), self.assertRaises(ValueError):
                parse_detail_times(json.dumps(data).encode(), expected_id=12)

    def test_unrelated_geometry_is_not_rendered_or_followed(self):
        times = parse_detail_times(payload(wkt='<script>ignored</script>'), expected_id=12)
        self.assertNotIn('wkt', time_report(times))
