"""Offline geographic validation, independent of user locations."""
import math

def point_coordinates(feature):
    geometry = feature.get('geometry')
    if not isinstance(geometry, dict) or geometry.get('type') != 'Point':
        raise ValueError('Expected Point geometry')
    coordinates = geometry.get('coordinates')
    if not isinstance(coordinates, list) or len(coordinates) != 2:
        raise ValueError('Expected two coordinates')
    lon, lat = coordinates
    if not all(type(v) in (int, float) and math.isfinite(v) for v in coordinates):
        raise ValueError('Coordinates must be finite numbers')
    if not -180 <= lon <= 180 or not -90 <= lat <= 90:
        raise ValueError('Coordinate bounds')
    return lon, lat
