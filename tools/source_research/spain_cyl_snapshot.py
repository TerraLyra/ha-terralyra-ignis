"""Select latest bulletin rows per exact province scope, not unique incidents."""
from datetime import date, time


def latest_bulletin_indexes(review):
    # A bounded sample cannot establish the newest complete bulletin.
    if not review['response_complete']:
        return dict(applied=False, reason='partial_response', indexes=list(range(len(review['results']))))
    latest = {}
    keys = []
    unresolved = []
    for index, item in enumerate(review['results']):
        row = item['source']
        provinces = row.get('provincia')
        day, hour = row.get('fecha_del_parte'), row.get('hora_del_parte')
        try:
            if (not isinstance(provinces, list) or not provinces
                    or any(not isinstance(p, str) or not p.strip() for p in provinces)
                    or not isinstance(day, str) or len(day) != 10
                    or not isinstance(hour, str) or len(hour) != 5):
                raise ValueError()
            timestamp = (date.fromisoformat(day), time.fromisoformat(hour))
            # Preserve exact scope including historical spelling differences.
            scope = tuple(sorted(set(provinces)))
        except ValueError:
            unresolved.append(index)
            keys.append(None)
            continue
        keys.append((scope, timestamp))
        latest[scope] = max(timestamp, latest.get(scope, timestamp))
    chosen = [i for i, key in enumerate(keys) if key is None or latest[key[0]] == key[1]]
    return dict(applied=True, reason='latest_in_supplied_complete_response', indexes=chosen,
                unresolved_indexes=unresolved, incident_deduplication=False)
