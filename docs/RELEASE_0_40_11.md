# 0.40.11 — Clearer Sentinel-3 guidance

Location summaries and their setup reviews now explain recognized Sentinel-3
failures in Hungarian and English. Network errors, server errors, timeouts,
request limits and invalid responses receive specific guidance instead of the
same generic retrieval-failure message.

Guidance uses the diagnostic codes introduced in 0.40.10 only for matching
Sentinel-3 providers in failed states. Authentication guidance takes precedence.
Unknown codes and other providers retain generic guidance; successful sources
do not display stale failure advice. This explains reported failures and does
not itself restore an unavailable upstream service.

## Validation

Implementation PR #216 passed all 27 automated checks. All 51 frontend unit tests
passed, including provider and failure-state guards, both languages, unknown
codes and authentication precedence. Packaged frontend files are synchronized.
The release candidate has not been installed on production Home Assistant.

## Update

Update through HACS, restart Home Assistant, and fully reload the browser or
Companion App frontend. Existing summary cards and bindings remain valid; no
configuration save or storage migration is required. For resource cache recovery,
see [card resources](CARD_RESOURCES.md#later-updates-and-rollback).

When a recognized Sentinel-3 failure occurs, inspect its guidance in the location
summary or setup review. Do not provoke failures or bypass retry waits to test it.
This release does not change polling, providers, radii, notifications or history.
