"""Independent observation/alert radii and alert transition contracts."""
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import pytest

from custom_components.terralyra_ignis.alerting import AlertTracker
from custom_components.terralyra_ignis.core.locations import (
    MonitoredLocation, monitored_location_from_dict, validate_monitored_location,
)
from custom_components.terralyra_ignis.models import FireCluster, FireLifecycle, IncidentLocationMatch
from custom_components.terralyra_ignis.monitoring import resolve_monitored_locations, update_primary_location_radius
from custom_components.terralyra_ignis.geo_location import IgnisAlertArea

NOW = datetime(2026, 10, 1, tzinfo=UTC)
LOC = MonitoredLocation('home', 'Home', 47, 19, 100, True, 'home_assistant', 25)


def incident(distance=10, *, track='one', stamp=NOW, members=(), matches=None):
    return FireCluster(latitude=47, longitude=19, distance_km=distance, confidence=1,
        frp_mw=5, acquired=stamp, pixel_count=1, track_id=track,
        source_track_ids=members, lifecycle=FireLifecycle.CONTINUING,
        location_matches=matches if matches is not None else (
            IncidentLocationMatch(track, 'home', 'Home', distance, 100, 'N', distance<=100,
                                  alert_radius_km=25),))


@pytest.mark.parametrize('radius', [0, -1, 101, float('nan'), float('inf'), True])
def test_invalid_alert_radius_rejected(radius):
    with pytest.raises(ValueError):
        validate_monitored_location(replace(LOC, alert_radius_km=radius))


@pytest.mark.parametrize('radius', [.1, 25, 100])
def test_equal_or_smaller_radius_roundtrips(radius):
    value = replace(LOC, alert_radius_km=radius)
    assert monitored_location_from_dict(value.as_dict()) == value


def test_legacy_storage_and_home_coordinate_resolution():
    old = replace(LOC, alert_radius_km=None).as_dict()
    assert 'alert_radius_km' not in old
    assert monitored_location_from_dict(old).effective_alert_radius_km == 100
    hass = SimpleNamespace(config=SimpleNamespace(latitude=48, longitude=20))
    entry = SimpleNamespace(options={'monitored_locations': [LOC.as_dict()]})
    resolved = resolve_monitored_locations(hass, entry)[0]
    assert resolved.latitude == 48
    assert resolved.alert_radius_km == 25
    with pytest.raises(ValueError):
        update_primary_location_radius(entry.options, 20)
    assert entry.options['monitored_locations'][0]['radius_km'] == 100


def test_startup_stays_quiet_and_new_incident_alerts_once():
    tracker = AlertTracker()
    assert tracker.update([incident()], (LOC,)) == []
    later = incident(track='two')
    assert tracker.update([incident(), later], (LOC,)) == [(later, later.location_matches)]
    assert tracker.update([incident(), later], (LOC,)) == []


def test_boundary_entry_requires_new_observation():
    tracker = AlertTracker()
    assert tracker.update([incident(30)], (LOC,)) == []
    assert tracker.update([incident(30)], (LOC,)) == []
    entered = incident(25, stamp=NOW+timedelta(minutes=5))
    assert tracker.update([entered], (LOC,)) == [(entered, entered.location_matches)]
    assert tracker.update([entered], (LOC,)) == []


def test_configuration_change_does_not_send_historical_alerts():
    tracker = AlertTracker()
    tracker.update([incident(30)], (LOC,))
    expanded = replace(LOC, alert_radius_km=50)
    changed = incident(30, matches=(replace(incident(30).location_matches[0], alert_radius_km=50),))
    assert tracker.update([changed], (expanded,)) == []
    assert AlertTracker().update([changed], (expanded,)) == []


def test_each_location_uses_its_own_radius_and_alerts_are_combined():
    cabin = replace(LOC, id='cabin', name='Cabin', alert_radius_km=60)
    tracker = AlertTracker()
    tracker.update([], (LOC,cabin))
    home_match = replace(incident(30).location_matches[0], distance_km=30)
    cabin_match = replace(home_match, location_id='cabin', location_name='Cabin', distance_km=50, alert_radius_km=60)
    fire = incident(matches=(home_match,cabin_match))
    assert tracker.update([fire], (LOC,cabin)) == [(fire,(cabin_match,))]
    tracker = AlertTracker(); tracker.update([], (LOC,cabin))
    fire = incident(matches=(replace(home_match,distance_km=20),cabin_match))
    assert tracker.update([fire], (LOC,cabin)) == [(fire,fire.location_matches)]


def test_corroboration_does_not_repeat_alert_and_inactive_is_excluded():
    tracker = AlertTracker()
    tracker.update([incident(members=('sat-a',))], (LOC,))
    merged = incident(track='merged', members=('sat-a','sat-b'), stamp=NOW+timedelta(minutes=5))
    assert tracker.update([merged], (LOC,)) == []
    assert tracker.update([replace(merged,lifecycle=FireLifecycle.INACTIVE)], (LOC,)) == []


def test_inner_circle_uses_alert_metres_and_preserves_observation_radius():
    entry = SimpleNamespace(entry_id='test',data={},runtime_data=SimpleNamespace(coordinator=None))
    entity = IgnisAlertArea(entry, LOC, home_latitude=47, home_longitude=19)
    assert entity.extra_state_attributes['gps_accuracy'] == 25000
    assert entity.extra_state_attributes['monitoring_radius_km'] == 100
    assert entity.extra_state_attributes['alert_radius_km'] == 25


def test_missing_and_inactive_snapshots_do_not_repeat_returning_alert():
    tracker = AlertTracker()
    tracker.update([], (LOC,))
    fire = incident()
    assert tracker.update([fire], (LOC,))
    assert tracker.update([], (LOC,)) == []
    assert tracker.update([replace(fire, lifecycle=FireLifecycle.INACTIVE)], (LOC,)) == []
    assert tracker.update([fire], (LOC,)) == []
    assert tracker.update([replace(fire, acquired=NOW+timedelta(minutes=5))], (LOC,)) == []


def test_older_outside_observation_cannot_reset_inside_state():
    tracker = AlertTracker()
    tracker.update([incident()], (LOC,))
    tracker.update([incident(30, stamp=NOW-timedelta(minutes=5))], (LOC,))
    assert tracker.update([incident(stamp=NOW+timedelta(minutes=5))], (LOC,)) == []


def test_real_exit_then_reentry_alerts_again():
    tracker = AlertTracker()
    tracker.update([incident()], (LOC,))
    assert tracker.update([incident(30, stamp=NOW+timedelta(minutes=5))], (LOC,)) == []
    inside = incident(stamp=NOW+timedelta(minutes=10))
    assert tracker.update([inside], (LOC,)) == [(inside, inside.location_matches)]
