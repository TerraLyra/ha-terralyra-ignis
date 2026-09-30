# Germany: BBK/NINA preflight — 2026-09-28

## Existing Home Assistant support

https://www.home-assistant.io/integrations/nina
The built-in NINA integration provides city/county warning slots, warning IDs,
headline/sender/severity/timestamps and a nina.get_details action including
full description, recommended actions and affected-area text. The documented
polling interval is five minutes. This is an implementation precedent, not a
publisher rate-limit grant. Do not duplicate this generic feature set by default.

IGNIS-specific value could be fire/smoke filtering and unified report display.
Evaluate optional consumption of existing NINA detail responses before adding
another network poller. Do not assume the built-in integration is installed,
that county coverage equals a radius around an IGNIS location, or that textual
affected areas provide exact geometry. Warning slots are reusable: use warning
identity, never the entity slot alone, when distinguishing source reports.
No production adapter or NINA configuration change is authorized by this note.

## Publisher scope remains distinct

https://warnung.bund.de/api/appdata/gsb/html/DE/app/impressum.html
Federal official warnings may be redistributed unchanged with attribution under
the published notice. Do not extend that statement automatically to every
regional/third-party warning, imagery, API contract or polling pattern.
https://www.bbk.bund.de/DE/Warnung-Vorsorge/Warnung-in-Deutschland/Warnmultiplikatoren/warnmultiplikatoren_node.html
Direct MoWaS multiplier connection requires an agreement; this does not itself
establish whether public local RSS/API consumption needs the same agreement.

Verified contact: nina@bbk.bund.de (official NINA legal notice).
Remaining technical gates: supported
public RSS/API access for user-local Home Assistant installations, whether
regional warning redistribution is covered, attribution/original-text retention,
polling/cache guidance, and update/cancellation/expiry identifiers. IGNIS must separate official reports from satellite observations.

Decision: continue bounded offline design; no duplicated runtime poller until
access and added value are settled. Existing HA support is not source permission.
