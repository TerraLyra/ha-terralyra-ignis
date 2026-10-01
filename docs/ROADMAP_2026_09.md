# IGNIS public development roadmap

Status reconciled on 2026-10-01: stable integration 0.32.0, with separately
updated optional dashboard resources. Main-branch changes after the release
are not automatically part of a HACS installation.

## Delivered

- Optional BM report card shipped in 0.30.0, with clearer accident labels in
  0.30.1. Display filtering preserves original reports and history. See
  [BM card](BM_REPORT_CARD.md) and [0.30.1 notes](RELEASE_0_30_1.md).
- Optional per-location summary card (#75, #77, #80) shipped in 0.31.0. It shows
  satellite counts, source health and the nearest active tracked incident inside
  the selected location's radius. An explicitly verified near-home FRMv3 binding
  shows forecast validity and receipt freshness; other locations do not gain a
  forecast automatically. Official restrictions remain unconnected.
- Sampled post-installation validation on 2026-09-30 confirmed the summary distance
  matches its location sensor attribute. See [0.31.0 notes](RELEASE_0_31_0.md).
- Report-map source visibility (#76) shipped in 0.31.0 and is separately installed:
  Canada/NIFC controls follow explicit map-switch associations. Disabled or
  unavailable sources are hidden; enabled sources with no reports remain
  selectable. See [map configuration](REPORT_DETAILS_CARD.md).

- Optional NIFC / WFIGS source status, timed calendar and location-aware report map
  shipped in 0.27.0. Administrator first-use initialization, bounded shared retrieval,
  persisted cooldowns and recovery diagnostics are included. See [NIFC usage](NIFC_USAGE.md).
- Initial live smoke checks confirmed a later successful retrieval and one matching
  map/calendar report with consistent location-relative distance and source time.
  This is sampled validation, not continuous uptime or exhaustive coverage evidence.
- Standalone basic observation-model packaging pilot builds a wheel from an
  allowlisted source archive. Shared consumer checks cover bundled and installed
  models on supported CI environments. See [package scope](BASIC_MODEL_PACKAGE.md).
- HA compatibility imports, existing IDs/history handling and per-location source
  health remain covered. No Cloud account or private runtime package is required.
- Current repository links and pinned CI tools are in place.

## Open work and limitations

- [Historical counter discontinuity](https://github.com/TerraLyra/ha-terralyra-ignis/issues/41):
  the original historical cause remains unproven. Investigation is deferred at
  the user's request; resume only when useful evidence is available;
  do not delete or rewrite user history, or assume access to an old machine/backup.
- Live smoke checks do not prove full history equivalence, restart/outage recovery
  or uninterrupted operation. Those scenarios have automated coverage but are not
  claimed as completed live acceptance tests.
- Source receipt freshness is not incident freshness, national completeness or an
  emergency all-clear. Map/calendar limits remain documented per provider.
- The standalone package is an unpublished experimental model subset, not a complete
  independently deployable Core or stable SDK. The integration parent still uses HA.
- PyTurboJPEG 1.8.3 remains a required test dependency through HA camera imports,
  matching the tested HA 2026.9.3 camera manifest. Reassess together with HA;
  no separate JPEG runtime requirement is added to IGNIS.

## Australian provider queue

| Source | Current position | Next gate |
| --- | --- | --- |
| NSW RFS / Queensland QFD | Existing optional report calendars | Maintain compatibility and source-specific semantics |
| Victoria | Offline inspectors complete; product-specific terms unresolved | Await developer terms and resolve remaining time/schema evidence before runtime work |
| ACT | Offline experimental research only | Real timestamp semantics and DST evidence; no production entities/calendar |
| Tasmania TasALERT | Product-specific access unresolved | Verify supported endpoints and terms |
| Western Australia DFES | Product-specific access unresolved | Clarify dataset approval and distributed local authentication |
| South Australia CFS | Product-specific reuse unresolved | Resolve product-specific reuse terms |
| Northern Territory | Access preflight complete | Confirm supported feed and reuse scope |

See [access preflight](PROVIDER_ACCESS_PREFLIGHT.md) for product-specific technical
and licensing gates. A publicly reachable endpoint alone does not establish reuse rights.

## Development sequence

1. Resolve product-specific access gates before implementing new adapters.
2. Investigate reproducible defects and dependency maintenance independently of
   external permissions; retain focused identity/history regression checks.
3. After access is settled, implement the next eligible provider with verified
   timestamps, categories, geometry and completeness. Keep warnings, planned burns
   and official reports distinct from satellite detections.
4. Assess other severely fire-affected countries with the same access/quality gates.
   Country priority remains a research decision, not a rollout commitment.
5. Expand the public model boundary only for a demonstrated consumer need. Do not
   publish an SDK or create another repository merely to complete the packaging pilot.

Optimization remains paused. Advanced service-side algorithms and evaporation,
solar-radiation and vegetation products are outside this integration's roadmap.
New releases and live deployment require their own validation and authorization.

## Maintenance release 0.27.1

Source retrieval diagnostics for current counts and the partial-restart regression
shipped in 0.27.1. Sampled live checks confirmed all three count types expose the
new attributes. See [release validation](NEXT_RELEASE_READINESS.md).

## Country-level place-name coverage (approved 2026-09-24)

- [x] Start with Hungary: filtered GeoNames country supplement, stable upstream
  identifiers, attribution, reproducible build and offline BM name-review option.
- [ ] Validate Hungary against new independent BM RSS notices, including inflected
  names, homonyms, route references and responding-unit names. Name recognition
  alone must not authorize an incident marker or a fire classification.
- [ ] Extend other countries when a provider demonstrates missing place coverage.
  Review source/license, feature selection, package size, language-specific aliases
  and ambiguity per country. Reuse the existing GeoNames build approach; do not
  load the full world extract by default.
- [x] Assess whether richer data should also serve nearest-settlement labels;
  check label changes separately before changing that runtime behavior.

The Hungarian supplement serves offline research. It shipped with 0.30.0,
but production BM map geolocation and runtime nearest-settlement changes
remain outside the delivered scope.

## BM fire scope (requested 2026-09-24)

- [x] Add offline evidence-only vegetation/local-asset/mixed/unknown categorization.
- [ ] Validate on independent vegetation-fire reports; distinguish burned area
  from threatened/property area before setting any large-extent flag.
- [x] Deliver an optional landscape-fire-focused view retaining uncertain and
  mixed reports for review. Do not discard source records or user history.

## Work ordering update — 2026-09-25

At the user's request, further independent BM sample validation was deferred
until the next development item completes. Existing Érd/Törökbálint alias changes
remain offline research; they do not authorize production geolocation.

The next item, nearest-settlement label impact assessment, is now complete.
See [Hungarian label impact](HU_LABEL_IMPACT.md). Keep the runtime resolver
unchanged: a denser gazetteer has not been shown to improve label usefulness.
Return to BM independent samples after this item; there is no new release or
production installation from this assessment.

### 2026-09-25 follow-up

The user deferred additional BM validation again after the initial return sample.
Keep independent vegetation-fire validation open for a later session; do not
promote the offline location candidates to production. Unresolved provider access gates remain open.

## Next eligible work — 2026-09-30

1. The summary forecast and nearest-distance extension is complete in 0.31.0.
   Keep its explicit location association and missing-data behavior when extending it.
2. Per-location FRMv3 forecasts and explicit summary bindings shipped in 0.32.0.
   Complete installation-specific dashboard bindings and acceptance separately.
   See [implementation](LOCATION_FORECAST_IMPLEMENTATION.md).
3. BM fixes from #82 and subsequent reviewed name forms have shipped. Keep
   independent vegetation-fire validation deferred; offline location candidates
   do not enable automatic production geolocation.
4. Resolve France/Germany product access and technical gates before runtime
   integration. Existing offline research is not production approval.
5. GWIS remains a worldwide forecast candidate, not an active provider. The
   [service spike](GWIS_TECHNICAL_SPIKE.md) now includes a working query-layer
   research client with bounded requests and explicit zero/nodata handling.
   The remaining gate is the time contract: responses do not return model issuance
   or a valid date. Requested dates and retrieval times must remain distinct from
   verified forecast validity. Establish dated evidence and operational validation
   before a runtime adapter.
6. Brazil INPE Eventos de Fogo has offline KML/centroid inspection, bounded
   state-scoped snapshots and an explicit-location preview (#96–#99). Resolve
   stable identity, collection transitions, unqualified timestamps and supported
   polling/caching before runtime activation. Preserve representative-point and
   estimated-area semantics; do not import derived events into satellite counters.
   See [Brazil requirements](BRAZIL_ACCESS_PREFLIGHT.md).
7. Castilla y León has a bounded explicit-date research client (#101), tested
   against a live daily bulletin response. Resolve coordinate provenance, stable
   incident identity, bulletin completeness and field-level timezone semantics
   before map/calendar integration. Bulletin rows are not distinct incident counts.
   See [Spain requirements](SPAIN_ACCESS_PREFLIGHT.md).
8. Himawari JAXA WLF and CAMS FRP remain separate inactive candidates. Establish
   each exact product's access, licence mapping and current endpoint before its
   decoder/runtime work. See [product terms](HIMAWARI_PRODUCT_TERMS.md).

CodeQL maintenance is complete in #100: init/analyze use the same pinned release,
and future CodeQL updates are grouped. The superseded separate updates #78/#79
are closed. This maintenance and the offline research do not require a HA update.

The remaining provider work above depends on source evidence, not merely parser
implementation. Keep technical limitations in this roadmap; correspondence and
outreach tracking are not repository documentation.

Do not restart the paused optimization work or historical-counter investigation
merely to fill the waiting period. Preserve user history.
