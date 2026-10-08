"""Explicit projected QFD coordinates; no guessing from coordinate magnitude."""
from datetime import UTC, datetime
import json
import pytest
from custom_components.terralyra_ignis.official_sources.queensland import parse_feed

NOW = datetime(2026, 10, 8, tzinfo=UTC)

def feed(coords, crs='EPSG:3857', warning=False):
    doc={'type':'FeatureCollection','features':[{'type':'Feature',
        'geometry':{'type':'Polygon' if warning else 'Point','coordinates':coords},
        'properties':{'UniqueID':'synthetic','EventType':'Fire','GroupedType':'FIRE VEGETATION',
            'WarningLevel':'Advice' if warning else 'Information','WarningTitle':'Synthetic',
            'ItemDateTimeLocal_ISO':'2026-10-08T10:00:00+10:00'}}]}
    if crs is not None:doc['crs']={'type':'name','properties':{'name':crs}}
    return json.dumps(doc).encode()

def test_proj_reference_and_third_ordinate():
    # Published PROJ reference: 2 degrees east, 49 north -> 222638.98, 6274861.39.
    r=parse_feed(feed([222638.98,6274861.39,7]),retrieved_at=NOW).records[0]
    assert r.geometry.coordinates == pytest.approx((2,49,7),abs=1e-6)
    assert r.event_updated_at == datetime(2026,10,8,tzinfo=UTC)

def test_projected_polygon_and_geographic_compatibility():
    ring=[[0,0],[1000,0],[1000,-1000],[0,0]]
    r=parse_feed(feed([ring],warning=True),retrieved_at=NOW).records[0]
    assert r.geometry.coordinates[0][0] == r.geometry.coordinates[0][-1]
    assert 0 < r.geometry.coordinates[0][1][0] < .01
    assert -.01 < r.geometry.coordinates[0][2][1] < 0
    assert parse_feed(feed([150,-25],None),retrieved_at=NOW).records[0].geometry.coordinates == (150,-25)

@pytest.mark.parametrize('coords,crs', [([1e30,0],'EPSG:3857'),([222638.98,6274861.39],None),([150,-25],'EPSG:9999'),([True,0],'EPSG:3857')])
def test_unknown_or_unbounded_coordinates_fail_closed(coords,crs):
    with pytest.raises(ValueError):parse_feed(feed(coords,crs),retrieved_at=NOW)


def test_explicit_crs84_keeps_longitude_latitude_order():
    record = parse_feed(
        feed([150, -25], 'urn:ogc:def:crs:OGC:1.3:CRS84'), retrieved_at=NOW
    ).records[0]
    assert record.geometry.coordinates == (150, -25)
