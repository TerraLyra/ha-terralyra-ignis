"""Offline location-specific presentation; no HA entities or source requests."""
from dataclasses import dataclass
from html import escape
import math
from inpe_snapshot import report


@dataclass(frozen=True)
class Location:
    name: str
    latitude: float
    longitude: float
    radius_km: float


def _finite(value):
    if type(value) not in (int, float):
        raise ValueError('Expected numeric coordinate/radius')
    try:
        value = float(value)
    except OverflowError as exc:
        raise ValueError('Number out of bounds') from exc
    if not math.isfinite(value):
        raise ValueError('Non-finite coordinate/radius')
    return value


def distance_km(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = map(_finite, (lat1, lon1, lat2, lon2))
    if not (-90 <= lat1 <= 90 and -90 <= lat2 <= 90
            and -180 <= lon1 <= 180 and -180 <= lon2 <= 180):
        raise ValueError('Invalid coordinate bounds')
    p1, p2 = math.radians(lat1), math.radians(lat2)
    a = math.sin((p2-p1)/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(math.radians(lon2-lon1)/2)**2
    return 6371.0088 * 2 * math.asin(math.sqrt(min(1, max(0, a))))


def location_report(snapshot, location):
    """Centroid-in-radius only, not footprint intersection or risk assessment.

    States are explicit snapshot scope, not automatically inferred coverage of
    the radius. No global/home fallback exists for reference coordinates.
    """
    if not isinstance(location.name, str) or not location.name.strip() or len(location.name) > 200:
        raise ValueError('Invalid location name')
    radius = _finite(location.radius_km)
    if not 0 < radius <= 2000:
        raise ValueError('Radius must be >0 and <=2000 km')
    distance_km(location.latitude, location.longitude, location.latitude, location.longitude)
    result = report(snapshot)
    selected = []
    for event in result['events']:
        distance = distance_km(location.latitude, location.longitude,
                               event['representative_latitude'], event['representative_longitude'])
        if distance <= radius:
            selected.append(dict(event, distance_km=distance))
    result['events'] = sorted(selected, key=lambda e: (e['distance_km'], e['source_id']))
    result.update(location_name=location.name, radius_km=radius,
                  reference_latitude=location.latitude, reference_longitude=location.longitude,
                  selection='representative_point_within_radius',
                  empty_message='A lekért államok adataiban nincs ide eső eseményjelölő. Ez nem igazolja a tűz hiányát.')
    return result


def render_preview(snapshot, location):
    """Self-contained Hungarian offline preview with escaped upstream labels."""
    data = location_report(snapshot, location)
    statuses = {'Ativo': 'Aktív a szolgáltató besorolása szerint',
                'Nova frente isolada': 'Új, elkülönült tűzfront',
                'Observação': 'Megfigyelés alatt'}
    cards = []
    for event in data['events']:
        status = statuses.get(event['status'], 'Ismeretlen szolgáltatói státusz')
        area = ('Nincs adat' if event['estimated_area_ha'] is None
                else f"{event['estimated_area_ha']:,.1f} ha")
        cards.append(f'''<article><h2>{escape(event['municipality'])} · {event['source_id']}</h2>
<p>{escape(status)} · Eredeti: {escape(event['status'])}</p>
<p>Szolgáltatói kategória: {escape(event['category'])}</p>
<dl><dt>Jelölőpont távolsága a kiválasztott helytől</dt><dd>{event['distance_km']:.1f} km</dd>
<dt>Szolgáltató által becsült terület</dt><dd>{area}</dd></dl></article>''')
    body = ''.join(cards) or f"<p>{escape(data['empty_message'])}</p>"
    return f'''<!doctype html><html lang="hu"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>INPE események – offline előnézet</title>
<style>body{{font:17px system-ui;margin:32px auto;padding:0 20px;max-width:850px;color:#17343c;background:#f4f8f8}}
article{{background:white;border:1px solid #b8cecf;border-radius:12px;padding:18px;margin:16px 0}}
h1{{font-size:28px}}h2{{font-size:21px}}dd{{margin:4px 0 14px;font-weight:600}}footer{{font-size:14px}}</style>
<h1>INPE események · {escape(data['location_name'])}</h1>
<p>Offline fejlesztői előnézet · Előzetes, műholdas eredetű eseménytermék</p>
<p>Kiválasztott államok: {escape(', '.join(data['requested_states']))} · Sugár: {data['radius_km']:g} km</p>
<p>A szűrés a jelölőpontokra vonatkozik, nem a tűz teljes területére. A lefedettség nem igazolt teljesnek.</p>
<p>Lekérés ideje: {escape(data['retrieved_at'])} · Az észlelés pontos ideje nincs igazolva.</p>
{body}<footer><p>{escape(data['attribution'])} · <a href="{data['source_url']}">Hivatalos forrás</a> ·
<a href="{data['license_url']}">CC BY-SA 4.0</a></p>
<p>Módosítások: állam- és távolságszűrés, mezőválogatás, ismétlődő rekordok összevonása; magyar felületi címkék.</p>
<p>A megfigyelési státusz nem igazolja az eloltást. Az előnézet nem hivatalos riasztás.</p></footer></html>'''
