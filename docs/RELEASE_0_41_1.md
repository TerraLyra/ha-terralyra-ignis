# 0.41.1 — Correct INPE license label

The INPE event detail card now labels its license link **CC BY-SA 4.0**.
The link already pointed to the correct license page; its displayed text was
incorrectly shared with CC BY 4.0 sources. Other source labels are unchanged.

No collection, map selection, notification or history behavior changes.
The INPE settings and monitored locations saved in 0.41.0 are retained.

## Update

Update through HACS, restart Home Assistant and fully reload the browser or
Companion App frontend. Open an INPE marker to verify the corrected license text.

## Validation

The existing INPE frontend test checks the corrected label and verifies that
other source labels retain CC BY 4.0. The bundled frontend file is synchronized
with the source. Candidate CI must pass before publication; live verification
of the label follows the upgrade.
