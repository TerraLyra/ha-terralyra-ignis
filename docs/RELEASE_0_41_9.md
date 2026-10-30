# 0.41.9 — More compact summary counters

Stacked summary counters now have less vertical whitespace. Explicit paragraph margins and a smaller row gap keep the numbers and their labels readable without excessive empty space. Text-relative wrapping from 0.41.8 is preserved.

The offline BM review vocabulary now recognizes Pakson/paksi and Erdőkertesen/erdőkertesi, with responder context for gödöllői. The production satellite-first matcher already supported the locative forms; new regressions verify event-town matching and rejection of responder-only clauses. No BM-created events or language-model dependency are added.

## Upgrade

Update in HACS and restart Home Assistant. Refresh the summary card using the administrator card-registration action (`card: summary`, `refresh_existing: true`), then reload the browser, including on the phone.

## Validation

All 27 checks passed for the implementation PR. The offline BM suite and targeted event/responder regressions passed. Summary browser checks passed in Hungarian and English at 16px and 32px text on a 390px viewport, including bounded counter spacing. Bundled frontend assets match their sources.

Physical iPhone verification of the reduced spacing remains after deployment. This does not add iOS Dynamic Type support or change language preferences.
