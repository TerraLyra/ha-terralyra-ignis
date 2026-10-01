"""Per-location satellite alert transitions, independent of observation events."""
from __future__ import annotations

from collections import OrderedDict

from .core.locations import MonitoredLocation
from .models import FireCluster, FireLifecycle, IncidentLocationMatch


class AlertTracker:
    """Baseline after restart/configuration changes; never send historical alerts.

    Source track IDs retain continuity when multiple sources form one incident.
    A bounded in-memory cache survives temporary missing/inactive snapshots.
    It is independent of persisted user history.
    """

    def __init__(self) -> None:
        self._configuration = None
        self._previous = OrderedDict()

    def update(
        self, incidents: list[FireCluster], locations: tuple[MonitoredLocation, ...]
    ) -> list[tuple[FireCluster, tuple[IncidentLocationMatch, ...]]]:
        configuration = tuple(sorted(
            (loc.id, loc.latitude, loc.longitude, loc.radius_km,
             loc.effective_alert_radius_km, loc.enabled) for loc in locations
        ))
        baseline = configuration != self._configuration
        if baseline:
            self._previous.clear()
        alerts = []
        for incident in incidents:
            if incident.lifecycle not in (FireLifecycle.NEW, FireLifecycle.CONTINUING):
                continue
            members = incident.source_track_ids or (incident.track_id,)
            members = tuple(member for member in members if member)
            if not members:
                continue
            affected = []
            for match in incident.location_matches:
                radius = match.alert_radius_km if match.alert_radius_km is not None else match.radius_km
                inside = match.inside_radius and match.distance_km <= radius
                keys = tuple((member, match.location_id) for member in members)
                previous = [self._previous[key] for key in keys if key in self._previous]
                # An added corroborating source must not repeat an existing alert.
                was_inside = any(value[0] for value in previous)
                newer = not previous or incident.acquired > max(value[1] for value in previous)
                if not baseline and inside and not was_inside and newer:
                    affected.append(match)
                for key in keys:
                    old = self._previous.get(key)
                    if old is None or incident.acquired > old[1] or baseline:
                        self._previous[key] = (inside, incident.acquired)
                    self._previous.move_to_end(key)
                    if len(self._previous) > 10000:
                        self._previous.popitem(last=False)
            if affected:
                alerts.append((incident, tuple(affected)))
        self._configuration = configuration
        return alerts
