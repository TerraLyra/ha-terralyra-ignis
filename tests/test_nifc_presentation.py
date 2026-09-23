"""Source timestamps and monitored-location geometry remain distinct from Home."""
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import pytest

from custom_components.terralyra_ignis.core.locations import MonitoredLocation
from custom_components.terralyra_ignis.nifc_calendar import render_nifc_events
from custom_components.terralyra_ignis.nifc_map import NifcMapRecord
from custom_components.terralyra_ignis.nifc_presentation import project_nifc, record_attributes
from custom_components.terralyra_ignis.official_sources.nifc.query import FetchResult
from custom_components.terralyra_ignis.official_sources.nifc.records import IncidentRecord

NOW=datetime(2026,9,16,15,30,tzinfo=UTC)
LOC=MonitoredLocation('california','California',38,-122,50,True,'manual')
HOME=MonitoredLocation('home','Home',47.5,19,50,True,'home_assistant')
RECORD=IncidentRecord('12345678-1234-1234-1234-123456789012','wildfire',-122,38,
                      NOW-timedelta(days=2),NOW,False,None)

def result(*records):
    return FetchResult(tuple(records),3,100,'terminal_reported',retrieval_method='verified_id_inventory')


def test_each_matched_location_is_preserved_and_home_is_not_fallback():
    near=replace(LOC,id='near',name='Near',latitude=38.01)
    items=project_nifc(result(RECORD),(HOME,LOC,near,replace(LOC,id='disabled',enabled=False)))
    assert len(items)==1
    attrs=record_attributes(items[0])
    assert attrs['distance_reference_id']=='california'
    assert [m['location_id'] for m in attrs['location_matches']]==['california','near']
    assert items[0].matches[0].distance_km==0
    assert project_nifc(result(RECORD),(HOME,))==()
    assert project_nifc(result(replace(RECORD,longitude=None,latitude=None)),(LOC,))==()


def test_complex_parent_members_and_prescribed_fire_remain_separate():
    parent=replace(RECORD,irwin_id='parent',category='incident_complex')
    child=replace(RECORD,complex_child=True,parent_complex_id='parent')
    burn=replace(RECORD,irwin_id='burn',category='prescribed_fire')
    items=project_nifc(result(parent,child,burn),(LOC,))
    assert [item.complex_role for item in items]==['complex_container','linked_complex_member','reported_non_child']
    assert [item.record.category for item in items]==['incident_complex','wildfire','prescribed_fire']


def test_timed_calendar_uses_modified_then_discovery_and_no_clock_fallback():
    events=render_nifc_events(result(RECORD),(HOME,LOC),NOW-timedelta(hours=1),NOW+timedelta(hours=1),language='hu')
    assert len(events)==1
    assert events[0].start==NOW
    assert events[0].end==NOW+timedelta(seconds=1)
    assert 'Adatlap frissítése' in events[0].summary
    assert 'California' in events[0].description and 'Home' not in events[0].description
    assert 'nem a tűz időtartama' in events[0].description
    fallback=replace(RECORD,modified_at=None,discovered_at=NOW)
    events=render_nifc_events(result(fallback),(LOC,),NOW,NOW+timedelta(hours=1),retained=True)
    assert 'Discovery reported' in events[0].summary
    assert 'Retained earlier response' in events[0].description
    assert render_nifc_events(result(replace(fallback,discovered_at=None)),(LOC,),NOW,NOW+timedelta(days=1))==[]
    assert render_nifc_events(result(RECORD),(LOC,),NOW-timedelta(days=1),NOW)==[]


def test_duplicate_locations_and_naive_dates_rejected():
    with pytest.raises(ValueError):project_nifc(result(RECORD),(LOC,LOC))
    with pytest.raises(ValueError):
        render_nifc_events(result(RECORD),(LOC,),NOW.replace(tzinfo=None),NOW+timedelta(days=1))


def test_map_distance_and_source_do_not_claim_satellite_detection():
    item=project_nifc(result(RECORD),(HOME,LOC))[0]
    manager=SimpleNamespace(entry=SimpleNamespace(entry_id='ABC'),hass=SimpleNamespace(config=SimpleNamespace(language='hu')),
                            runtime=SimpleNamespace(owner=SimpleNamespace(state=SimpleNamespace(status='retrieved',received_at=None))))
    entity=NifcMapRecord(manager,item)
    assert entity.distance==0
    assert entity.source=='terralyra_ignis_nifc_reports'
    assert entity.extra_state_attributes['distance_reference_name']=='California'
    assert entity.extra_state_attributes['active_fire_status']=='not_established'
    assert entity.extra_state_attributes['last_success_at'] is None
    assert entity.latitude==38 and entity.longitude==-122
    assert entity.entity_id==entity.entity_id.lower()
