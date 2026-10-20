# 0.40.13 — Copy combined dashboard configuration

After generating a combined map and location-summary configuration, use
**Copy configuration** to copy it to the clipboard. Hungarian and English
feedback confirms success only after the browser completes the write.

If clipboard access is unavailable or denied, including on local HTTP
installations, the text is selected and manual-copy instructions are shown.
Use Ctrl+C, ⌘C, or the mobile Copy command. Review the configuration in a
new Manual card before saving. Generation and copying do not save a dashboard.

The map still shows all enabled IGNIS locations; the summary retains its
selected location and forecast binding. No provider, radius, notification,
storage or history changes are included.

## Validation

Implementation PR #221 passed all 27 automated checks, 52 frontend unit tests,
and browser checks for successful clipboard writes and rejected clipboard
access. These are automated checks; production clipboard behavior and unaided
onboarding remain separate acceptance steps.

## Update

Update through HACS, restart Home Assistant and fully reload the browser or
Companion App frontend. Existing cards and resource registrations remain valid.
No configuration migration is required. See [summary setup](LOCATION_SUMMARY_CARD.md).
