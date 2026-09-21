import unittest
from geometry import point_coordinates

class GeometryTests(unittest.TestCase):
    def test_geojson_order(self):
        self.assertEqual(point_coordinates({'geometry':{'type':'Point','coordinates':[-123.5,49.2]}}),(-123.5,49.2))

    def test_invalid_points(self):
        for coordinates in ([0,91],[181,0],[float('nan'),0],[True,45],[0,float('inf')],[1],['1',2],[1,2,3]):
            with self.subTest(coordinates=coordinates), self.assertRaises(ValueError):
                point_coordinates({'geometry':{'type':'Point','coordinates':coordinates}})

    def test_missing_or_other_geometry(self):
        for geometry in (None,{}, {'type':'Polygon','coordinates':[]}):
            with self.subTest(geometry=geometry), self.assertRaises(ValueError):
                point_coordinates({'geometry':geometry})
