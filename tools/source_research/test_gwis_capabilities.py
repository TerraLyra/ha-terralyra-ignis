"""Synthetic evidence checks: no live traffic and no HA import."""
import unittest
from gwis_capabilities import inspect_capabilities, MAX_BYTES


def document(layer=''):
    return ('<WMS_Capabilities xmlns="http://www.opengis.net/wms" version="1.3.0">'
            '<Capability><Layer>' + layer + '</Layer></Capability></WMS_Capabilities>').encode()


def layer(queryable='0', time='2018-01-01/2099-12-31'):
    return ('<Layer queryable="' + queryable + '"><Name>ecmwf.fwi</Name>'
            '<Dimension name="time" default="2019-01-01">' + time + '</Dimension></Layer>')


class GwisCapabilitiesTests(unittest.TestCase):
    def test_advertised_range_does_not_establish_freshness(self):
        result = inspect_capabilities(document(layer()))
        self.assertFalse(result['queryable_explicit'])
        self.assertEqual(result['time_expression'], '2018-01-01/2099-12-31')
        self.assertEqual(result['time_default'], '2019-01-01')
        self.assertFalse(result['production_ready'])
        self.assertIn('actual_product_dates', result['unresolved'])

    def test_queryable_and_date_still_do_not_authorize_runtime(self):
        result = inspect_capabilities(document(layer('1', '2026-09-30')))
        self.assertTrue(result['queryable_explicit'])
        self.assertFalse(result['production_ready'])

    def test_service_formats_do_not_override_layer_queryability(self):
        raw = document(layer()).replace(b'<Capability>', b'<Capability><Request>'
            b'<GetMap><Format>image/tiff</Format></GetMap>'
            b'<GetFeatureInfo><Format>text/plain</Format></GetFeatureInfo></Request>')
        result = inspect_capabilities(raw)
        self.assertEqual(result['map_formats'], ['image/tiff'])
        self.assertEqual(result['feature_info_formats'], ['text/plain'])
        self.assertFalse(result['queryable_explicit'])
        self.assertFalse(result['production_ready'])

    def test_missing_attributes_remain_unknown(self):
        result = inspect_capabilities(document('<Layer><Name>ecmwf.fwi</Name></Layer>'))
        self.assertIsNone(result['queryable_explicit'])
        self.assertIsNone(result['time_expression'])

    def test_rejects_errors_missing_and_duplicate_layers(self):
        for raw in (b'<ServiceExceptionReport/>', b'<html/>', b'', document(), document(layer()*2)):
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                inspect_capabilities(raw)

    def test_rejects_ambiguous_dimension(self):
        raw = document(layer().replace('</Layer>', '<Dimension name="time">2026-09-30</Dimension></Layer>'))
        with self.assertRaises(ValueError):
            inspect_capabilities(raw)

    def test_rejects_hostile_and_oversized_xml(self):
        for raw in (b'<!DOCTYPE x>' + document(layer()), b'\x00', b'\xff',
                    b'x' * (MAX_BYTES + 1), document('<Layer>' * 40 + '</Layer>' * 40)):
            with self.subTest(size=len(raw)), self.assertRaises(ValueError):
                inspect_capabilities(raw)


if __name__ == '__main__':
    unittest.main()
