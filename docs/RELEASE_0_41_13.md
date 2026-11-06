# 0.41.13 — BM place and traffic-context review

The offline BM review recognizes Gyálnál, Tuzséron and Siófokon, plus the siófoki and záhonyi brigade adjectives. The existing reviewed-name list rule now separates Kisvárda and Záhony in their shared responding-brigade phrase. Szeged felé remains a direction reference rather than incident-place evidence.

The shared fire-scope classifier no longer treats the exact traffic phrase “forgalmi akadályra lehet számítani” as uncertainty about the incident. Other uncertainty, negation, exercise and truncation safeguards remain in place.

## Upgrade

Update in HACS and restart Home Assistant. No card regeneration or configuration changes are required.

## Validation

All 161 local BM tests passed, including location, direction, responding-brigade list and genuine-uncertainty regressions. The current three RSS samples were reviewed using the bundled GeoNames data without downloading linked event pages. Results remain review candidates, never verified incident coordinates or automatic alert decisions.
