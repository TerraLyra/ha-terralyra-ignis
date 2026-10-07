"""Satellite-first BM town/time context; no incident creation or location rewrite."""
from dataclasses import dataclass
from datetime import datetime, timedelta

from .report_context import IncidentContext, MAX_INCIDENTS, MAX_REPORTS, _time
import re

NOTICE_URL = re.compile(r'https://www\.katasztrofavedelem\.hu/modules/vesz/esemeny/[0-9]+')

# Initial heuristic: publication may precede or follow observations by six hours.
PUBLICATION_WINDOW = timedelta(hours=6)


@dataclass(frozen=True)
class BMTownReport:
    url: str
    published_at: datetime
    event_settlement_ids: frozenset[str]
    fire_report: bool
    title: str = ''

    def __post_init__(self):
        if not NOTICE_URL.fullmatch(self.url):
            raise ValueError('Original BM event URL required')
        _time(self.published_at)
        if not isinstance(self.event_settlement_ids, frozenset) or any(
            not isinstance(s,str) or not s.strip() for s in self.event_settlement_ids
        ):
            raise ValueError('Explicit event settlement identities required')
        if type(self.fire_report) is not bool:
            raise ValueError('Explicit fire relevance required')


def bm_reports_for_satellite(incident_id, incidents, settlement_ids_by_incident, reports):
    """Town IDs must share one gazetteer namespace; responders are not event IDs.

    A matching municipality + nearby publication is a probable *context* link.
    Actual competing detections are disclosed, not silently chosen or rejected.
    This is a heuristic label, not calibrated probability or official confirmation.
    """
    if len(incidents)>MAX_INCIDENTS or len(reports)>MAX_REPORTS:
        raise ValueError('Context input exceeds limit')
    ids=[i.incident_id for i in incidents]
    if len(set(ids))!=len(ids) or incident_id not in ids:
        raise ValueError('Select a unique existing satellite incident')
    for identity in ids:
        towns=settlement_ids_by_incident.get(identity,frozenset())
        if not isinstance(towns,frozenset) or any(not isinstance(t,str) or not t.strip() for t in towns):
            raise ValueError('Satellite settlement identities must be explicit sets')
    output=[]
    for report in reports:
        if not report.fire_report or not report.event_settlement_ids:
            continue
        candidates=[]
        for incident in incidents:
            same_town=report.event_settlement_ids & settlement_ids_by_incident.get(incident.incident_id,frozenset())
            if same_town and incident.first_seen-PUBLICATION_WINDOW <= report.published_at <= incident.last_seen+PUBLICATION_WINDOW:
                candidates.append(incident.incident_id)
        if incident_id in candidates:
            output.append(dict(report_url=report.url,title=report.title,
                published_at=report.published_at.isoformat(), relation='probable',
                basis='event_settlement_and_publication_window',
                candidate_incident_ids=sorted(candidates), ambiguous=len(candidates)>1,
                official_confirmation=False))
    return dict(incident_id=incident_id, reports=output, creates_incident=False)
