# 0.40.1 — TasALERT mixed-feed fix

TasALERT responses containing warning records no longer fail with
`invalid_snapshot`. Warning records are retained alongside incidents and burnt
areas, but only eligible incident points become map candidates.

Update through HACS and restart Home Assistant. Existing locations, source
switches and storage remain valid; do not reinitialize or delete storage.
Persisted retry deadlines are respected, so the next retrieval may not happen
immediately after restart.

Validation: all 54 TasALERT tests passed locally, including a mixed-feed
regression test. Offline replay of an official response accepted 18 records and
produced 11 incident candidates before location filtering.
