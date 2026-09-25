"""Render a standalone, network-free HTML review of a bounded JCyL sample."""
import argparse
from html import escape
from pathlib import Path
from spain_cyl_review import inspect_response, MAX_BYTES
from spain_cyl_snapshot import latest_bulletin_indexes


def render(raw):
    review = inspect_response(raw)
    selection = latest_bulletin_indexes(review)
    cards = []
    labels = {
        'extinction_time_status_conflict': 'Az állapot és az eloltási idő ellentmondhat egymásnak.',
        'geometry_semantics_unverified': 'A koordináta jelentése nem igazolt; térképes tűzjelölés nincs.',
    }
    def text(value):
        return escape('Nincs megadva' if value is None else str(value), quote=True)
    for index in selection['indexes']:
        item = review['results'][index]
        row = item['source']
        if item['record_kind'] == 'no_incident_notice':
            heading = 'Nincs esemény a jelentéssor szerint'
        else:
            heading = row.get('termino_municipal') or 'Ismeretlen település'
        provinces = row.get('provincia')
        province_label = ', '.join(provinces) if isinstance(provinces, list) and all(isinstance(p, str) for p in provinces) else provinces
        fields = [
            ('Tartomány – forrás szerinti', province_label),
            ('Jelentés dátuma', row.get('fecha_del_parte')),
            ('Jelentés ideje – forrás szerinti', row.get('hora_del_parte')),
            ('Kezdet dátuma', row.get('fecha_de_inicio')),
            ('Kezdet ideje – forrás szerinti', row.get('hora_de_inicio')),
            ('Állapot – eredeti szöveg', row.get('situacion_actual')),
            ('Eloltás dátuma – forrás szerinti', row.get('fecha_extinguido')),
            ('Eloltás ideje – forrás szerinti', row.get('hora_extinguido')),
            ('Érintett terület – eredeti szöveg', row.get('tipo_y_has_de_superficie_afectada')),
        ]
        details = ''.join(f'<dt>{text(k)}</dt><dd>{text(v)}</dd>' for k, v in fields)
        warnings = ''.join(f'<li>{text(labels.get(i, "Ellenőrizendő adat: " + i))}</li>' for i in item['issues'])
        cards.append(f'<article><h2>{text(heading)}</h2><dl>{details}</dl><ul>{warnings}</ul></article>')
    collection = review.get('collection_status')
    reasons = {'count_reached': 'A jelzett számú sor megérkezett', 'page_error': 'A lekérés hibával megszakadt', 'page_limit': 'Elértük a lekérési korlátot', 'byte_limit': 'Elértük az adatméretkorlátot', 'total_changed': 'A találatszám lekérés közben változott', 'overlapping_pages': 'A válaszoldalak átfednek', 'short_page': 'A vártnál kevesebb adat érkezett'}
    receipt = ('<p>Lekérési eredmény: ' + text(reasons.get(collection.get('reason'), 'A válasz további ellenőrzést igényel')) + '. A találatszám egyezése nem igazolja, hogy az adatok közben változatlanok maradtak.</p>') if collection else ''
    return '''<!doctype html><html lang="hu"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Castilla y León – jelentések előnézete</title>
<style>body{font:17px system-ui;max-width:850px;margin:32px auto;padding:0 20px;color:#172d34;background:#f5f8f9}article{background:white;border:1px solid #b9ccd1;border-radius:12px;padding:20px;margin:20px 0}h1{font-size:28px}h2{font-size:21px}dt{font-weight:600;margin-top:12px}dd{margin:3px 0;overflow-wrap:anywhere}li{margin:8px 0}a{color:#006879}</style>
<h1>Castilla y León – hivatalos jelentések</h1>
<p>Offline kutatási előnézet, mentett mintából. Nem élő állapot és nem teljes eseménylista.</p>
<p>A sorok jelentések, nem ellenőrzött számú különálló tüzek. Az időpontok a forrás eredeti értékei; időzóna-átváltás nem történt.</p>
''' + f'<p>{review["inspected_rows"]} vizsgált sor / {review["total_count"]} API-találat a lekéréskor.</p>' + ('<p>A teljes válaszon belüli legfrissebb jelentések tartományi csoportonként; a hiányos időadatú sorok megmaradnak. Ez nem élő frissességi garancia.</p>' if selection['applied'] else '<p>Részleges vagy nem igazoltan változatlan adatcsomag: minden mintasor látható; legfrissebbként való kiválasztás nincs.</p>') + receipt + ''.join(cards) + '''
<footer><p>Forrás: <a href="https://analisis.datosabiertos.jcyl.es/explore/dataset/incendios-forestales/">Junta de Castilla y León</a> · <a href="https://creativecommons.org/licenses/by/4.0/">CC BY 4.0</a>. Magyar feliratokkal és ellenőrzési megjegyzésekkel átalakított megjelenítés. Nem jelent szolgáltatói jóváhagyást.</p></footer></html>'''


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('sample', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    with args.sample.open('rb') as stream:
        html = render(stream.read(MAX_BYTES + 1))
    args.output.write_text(html)
