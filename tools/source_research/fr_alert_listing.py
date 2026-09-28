"""Inspect a bounded local FR-Alert homepage snapshot, never an active-fire census."""
from copy import deepcopy
import json
from fr_alert_review import SettingsParser, MAX_BYTES, value, review_infos


def inspect_listing(raw):
    if len(raw) > MAX_BYTES:
        raise ValueError('Listing exceeds 1 MiB')
    parser = SettingsParser()
    parser.feed(raw.decode('utf-8'))
    parser.close()
    if parser.active or len(parser.blocks) != 1:
        raise ValueError('Expected one complete settings block')
    settings = json.loads(parser.blocks[0])
    entity = settings.get('alert_entity') if isinstance(settings, dict) else None
    alerts = entity.get('alerts') if isinstance(entity, dict) else None
    if not isinstance(alerts, list) or len(alerts) > 200 or any(not isinstance(a, dict) for a in alerts):
        raise ValueError('Expected at most 200 alert objects')
    results = []
    seen = set()
    for alert in alerts:
        identifier = value(alert, 'identifier')
        issues = ['lifecycle_unverified']
        if not isinstance(identifier, str) or not identifier.strip():
            issues.append('missing_identifier')
        elif identifier in seen:
            issues.append('duplicate_identifier')
        else:
            seen.add(identifier)
        info_reviews = []
        try:
            info_reviews = review_infos(alert.get('infos'))
        except ValueError:
            issues.append('missing_or_invalid_infos')
        status = value(alert, 'status')
        results.append(dict(source=deepcopy(alert),
                            is_test=True if status == 'Exercice' else None,
                            test_evidence='status=Exercice' if status == 'Exercice' else None,
                            active=None, info_reviews=info_reviews, issues=issues))
    return dict(schema_version=1, results=results, inspected_alerts=len(results),
                snapshot_complete=False, runtime_eligible=False)
