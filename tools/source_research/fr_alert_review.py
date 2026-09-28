"""Bounded offline FR-Alert detail inspection; no network or HA integration."""
import argparse
from copy import deepcopy
from datetime import datetime, timezone
from html.parser import HTMLParser
import json
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

MAX_BYTES = 1024 * 1024


class SettingsParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=False)
        self.active = False
        self.parts = []
        self.blocks = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'script' and attrs.get('data-drupal-selector') == 'drupal-settings-json':
            self.active = True
            self.parts = []

    def handle_data(self, data):
        if self.active:
            self.parts.append(data)

    def handle_endtag(self, tag):
        if tag == 'script' and self.active:
            self.blocks.append(''.join(self.parts))
            self.active = False


def value(row, key):
    entries = row.get(key)
    if isinstance(entries, list) and len(entries) == 1 and isinstance(entries[0], dict):
        return entries[0].get('value')
    return None


def inspect_detail(raw):
    if len(raw) > MAX_BYTES:
        raise ValueError('Detail exceeds 1 MiB')
    parser = SettingsParser()
    parser.feed(raw.decode('utf-8'))
    parser.close()
    if parser.active or len(parser.blocks) != 1:
        raise ValueError('Expected one complete settings block')
    settings = json.loads(parser.blocks[0])
    entity = settings.get('alert_entity') if isinstance(settings, dict) else None
    infos = entity.get('infos') if isinstance(entity, dict) else None
    reviewed = review_infos(infos)
    return dict(schema_version=1, source_path=deepcopy(settings.get('path')),
                results=reviewed, runtime_eligible=False,
                warning='Research only: timestamps are candidate interpretations; raw HTML text is not safe to render.')


def timezone_value(info):
    """Accept only the two observed timezone encodings; never use display text."""
    entries = info.get('timezone')
    if isinstance(entries, dict):
        if not set(entries).issubset({'0', 'translate'}) or not isinstance(entries.get('0'), dict):
            return None
        return entries['0'].get('value')
    return value(info, 'timezone')


def review_infos(infos):
    if not isinstance(infos, list) or not 1 <= len(infos) <= 20 or any(not isinstance(i, dict) for i in infos):
        raise ValueError('Expected 1–20 info objects')
    reviewed = []
    for info in infos:
        candidates = {}
        issues = ['alert_lifecycle_unverified', 'geometry_semantics_unverified']
        for key in ('effective', 'onset', 'expires', 'created', 'updated'):
            source = value(info, key)
            if source is None:
                continue
            try:
                if not isinstance(source, str) or not source.isascii() or not source.isdigit():
                    raise ValueError()
                candidates[key] = datetime.fromtimestamp(int(source), timezone.utc).isoformat()
            except (ValueError, OverflowError, OSError):
                issues.append('invalid_epoch_candidate_' + key)
        for start in ('effective', 'onset'):
            if start in candidates and 'expires' in candidates:
                if datetime.fromisoformat(candidates['expires']) < datetime.fromisoformat(candidates[start]):
                    issues.append('expires_before_' + start)
        local_candidates = {}
        zone = timezone_value(info)
        try:
            if not isinstance(zone, str) or not zone:
                raise ValueError()
            tz = ZoneInfo(zone)
            local_candidates = {k: datetime.fromisoformat(v).astimezone(tz).isoformat()
                                for k, v in candidates.items()}
        except (ValueError, ZoneInfoNotFoundError):
            issues.append('missing_or_invalid_timezone')
        reviewed.append(dict(local_time_candidates=local_candidates, source=deepcopy(info), epoch_seconds_candidates=candidates,
                             timestamp_semantics_verified=False,
                             is_test=True if value(info, 'level') == 'EXERCISE' else None,
                             test_evidence='level=EXERCISE' if value(info, 'level') == 'EXERCISE' else None,
                             active=None, incident_id_verified=False,
                             issues=issues))
    return reviewed


if __name__ == '__main__':
    args = argparse.ArgumentParser(description=__doc__)
    args.add_argument('sample', type=Path)
    sample = args.parse_args().sample
    with sample.open('rb') as stream:
        result = inspect_detail(stream.read(MAX_BYTES + 1))
    print(json.dumps(result, ensure_ascii=False, indent=2))
