# 0.41.11 — BM accident-review context

The offline BM review recognizes Tárnokon and the responding-unit adjectives balmazújvárosi and kőszegi. Responding brigade mentions remain separate from incident-place evidence, including lists of brigades.

The shared fire-scope review classifier recognizes the accident expressions árokba hajtott and balesethez. Traffic permission phrased as lehet közlekedni no longer makes the incident classification uncertain. Other uncertainty, negation, exercise, smoke/fire and truncation safeguards remain in place.

## Upgrade

Update in HACS and restart Home Assistant. No card regeneration or configuration changes are required.

## Validation

All 152 local BM tests passed. Original RSS samples 93315, 93314 and 93397 were replayed against the bundled GeoNames data. These remain review candidates, not verified incident coordinates or automatic alert decisions.
