# 0.40.14 — Regenerate configuration after edits

Changing settings in the location-summary editor now clears the previously
generated combined map/summary configuration and hides its Copy button.
A Hungarian or English message asks you to generate the configuration again.
This prevents accidental reuse of an older location, title or forecast binding.

Routine source-status updates preserve the generated text. Late clipboard
completion feedback cannot replace the changed-settings message. Text already
copied to the clipboard cannot be revoked: generate and copy again after edits.

## Validation

Implementation PR #223 passed all 27 automated checks and 52 frontend unit tests.
Browser checks cover editing after generation, regeneration with the new title,
pending clipboard completion and ordinary background updates. Production use of
this change and unaided onboarding remain separate acceptance steps.

## Update

Update through HACS, restart Home Assistant and fully reload the browser or
Companion App frontend. Existing cards and resource registrations remain valid.
No provider, radius, notification, storage or history changes are included.
The editor does not save dashboards automatically. See
[summary setup](LOCATION_SUMMARY_CARD.md).
