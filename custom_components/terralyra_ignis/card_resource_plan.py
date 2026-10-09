"""Offline resource registration planning; never mutate HA resource storage."""
from urllib.parse import urlsplit, unquote

CARDS = {
    'summary': 'ignis-location-summary.js',
    'map': 'ignis-report-map.js',
    'bm': 'ignis-bm-reports.js',
}


def plan_card_resource(card: str, resources: list[dict]) -> dict:
    """Require a reviewed inventory before suggesting a missing module.

    Known legacy filename variants block addition. Arbitrarily renamed files
    cannot be identified without reading their contents, so an add candidate
    always requires user confirmation that no renamed copy is loaded.
    """
    if card not in CARDS:
        raise ValueError('Unknown IGNIS card')
    if not isinstance(resources, list) or any(
        not isinstance(item, dict) or not isinstance(item.get('url'), str)
        or not isinstance(item.get('type'), str) for item in resources
    ):
        raise ValueError('Complete resource inventory required')
    filename = CARDS[card]
    canonical = '/terralyra_ignis/cards/' + filename
    matches = []
    for item in resources:
        try:
            path = unquote(urlsplit(item['url']).path)
        except ValueError as err:
            raise ValueError('Invalid resource URL') from err
        basename = path.rsplit('/', 1)[-1]
        stem = filename[:-3]
        if basename == filename or (basename.startswith(stem + '-') and basename.endswith('.js')):
            matches.append((item, path))
    if len(matches) > 1:
        status = 'duplicate_review'
    elif matches:
        item, path = matches[0]
        if item['type'] != 'module':
            status = 'type_review'
        elif path != canonical or urlsplit(item['url']).netloc:
            status = 'legacy_review'
        else:
            status = 'already_registered'
    else:
        status = 'confirm_no_renamed_copy'
    return {'status': status, 'url': canonical, 'type': 'module',
            'matching_urls': [item['url'] for item, _ in matches]}
