# Offline official-source research

These standard-library tools inspect supplied ACT RSS bytes. They are outside the
Home Assistant integration and do not fetch feeds, publish alerts or write history.

Run the synthetic tests from the repository root:

```sh
python3 -m unittest discover -s tools/source_research -v
```

The `Official source research` workflow runs the same suite on Python 3.11 and 3.14
without HA dependencies, source credentials, live feed requests or artifact uploads.

`act_summary.summarize_feed(payload)` returns aggregate diagnostic counts only.
Its result is JSON serializable; categories, exercise flags, identities, coordinates
and three source-time fields are independent dimensions, not additive event totals.
No raw source IDs, coordinates, titles or dates appear in the summary. Underlying
inspection helpers retain raw fields in memory and should not be logged as summaries.

A malformed or over-limit feed raises `InvalidFeed`; callers must not replace that
with a successful zero-count result. Default bounds are 1 MiB and 10,000 items.

Important limits:

- Fire classification is a narrow candidate mapping, not a complete type dictionary.
- Textual test markers are heuristic; an unmarked item is not confirmed real.
- Parsed dates are unresolved wall-clock readings, unsuitable for freshness checks.
- Matching IDs in one sample do not establish stability across time.
- Repeated matching IDs are counted, not merged; inconsistent ID pairs remain errors.
- Global coordinate validity does not establish ACT membership or spatial accuracy.

See `docs/ACT_ADAPTER_READINESS.md` for dated evidence and remaining production gates.

## NIFC query-page inspection

`nifc_page.inspect_page` checks an already decoded, bounded JSON point-query page
requested with OBJECTID ascending and outSR=4326. It rejects error envelopes,
invalid/repeated/unordered object IDs, excessive records and unexpected spatial
references. This is a page-envelope check, not full geometry/incident validation.
Its ID tuple is transient paging metadata, not a durable incident identity or a
privacy-filtered output suitable for publishing.

An explicit transfer-limit true means more results, even on a short/empty page.
Missing transfer-limit metadata remains unknown. Explicit false reports a terminal
response only: it does not certify a complete, consistent multi-page snapshot.
No network client, next-offset calculation or automatic history reconciliation exists.
Future retrieval must bound pages/bytes and handle changing source data; missing
records must never imply incident closure or trigger history deletion.

Reference: https://developers.arcgis.com/rest/services-reference/enterprise/query-feature-service-layer/
Validation: eight synthetic NIFC tests, 49 total offline tests passed locally. The
five-record live sample was correctly classified as requiring continuation. No
additional pages or full incident dataset were fetched.
