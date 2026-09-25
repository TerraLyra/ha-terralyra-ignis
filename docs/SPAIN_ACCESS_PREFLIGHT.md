# Spain source preflight — 2026-09-25

## National sources

MITECO daily intervention reports cover fires involving ministry resources,
not all Spanish fires. EGIF is historical/statistical; neither should be
presented as a complete live national incident feed.
https://www.miteco.gob.es/eu/biodiversidad/temas/incendios-forestales/estadisticas-actuaciones.html
https://www.miteco.gob.es/eu/biodiversidad/temas/incendios-forestales/estadisticas-datos.html

## Castilla y León: promising regional candidate

Official product:
https://analisis.datosabiertos.jcyl.es/explore/dataset/incendios-forestales/information/
Metadata/API:
https://analisis.datosabiertos.jcyl.es/api/explore/v2.1/catalog/datasets/incendios-forestales

Read-only anonymous requests succeeded. Dataset metadata explicitly lists
Junta de Castilla y León as publisher, CC BY 4.0 with its licence URL, and
Europe/Madrid as dataset timezone. No separate individual permission requirement
was identified for reuse under that licence. Retain attribution, licence link,
change indication and source timestamps; do not imply endorsement.

The description still refers to twice-daily publication through October 2025,
but a bounded query ordered by fecha_del_parte and hora_del_parte returned
2026-09-25 10:00 reports. This verifies sampled current data, not future cadence
or guaranteed availability. The 29,106-row dataset includes historical snapshots;
a default first record is not the latest report.

## Gates before an adapter

- Confirm whether posicion is incident geometry or a municipality reference.
  Do not use it as a precise fire point solely because it has coordinates.
- No documented stable incident identifier was found in the schema. orden
  includes report date/time and province; it must not be assumed unique.
- Preserve separate report and onset times. Dataset timezone metadata is useful
  but field-specific DST/time interpretation still needs testing/evidence.
- Handle SIN INCIDENCIAS as a report row without an incident, not a fire marker.
- A sampled CONTROLADO record also has an extinction timestamp. Preserve both
  and flag the inconsistency; do not silently promote one to definitive status.
- The severity field changed meaning under INFOCAL in May 2025. Do not flatten
  historical and current severity scales into a single undocumented ranking.
- Verify snapshot completeness, paging, revisions and supported polling limits.
- Keep region-specific coverage explicit; this is not all-Spain coverage.

Decision: eligible for bounded offline schema/semantics research. Runtime, map
entities and release remain absent. A general permission request is not warranted
solely because it is a new provider; unresolved technical questions come first.

## Offline inspector completed

`tools/source_research/spain_cyl_review.py` reads a bounded local API JSON sample
(maximum 1 MiB / 100 rows), preserves upstream fields, distinguishes no-incident
notices, flags status/extinction conflicts and checks coordinate/time syntax.
It never promotes coordinates, timestamps or IDs to verified incident semantics.
`response_complete` describes only whether returned row count equals API total;
it is not an assertion of complete regional incident coverage.

Replay of the three sampled 2026-09-25 records flags the CONTROLADO/extinction
conflict, marks both point geometries as unverified, and treats SIN INCIDENCIAS
as a non-incident notice. The response is partial (3 of 29,106 historical rows).
The full offline suite passes 258 tests. DST-edge local times are preserved
without guessing an offset. This is local research code, not a runtime adapter.

## Shared coordinate evidence — 2026-09-25

A bounded query for codigo_municipio_ine=47116 (Pesquera de Duero), ordered by
report date/time descending, returned 30 of 31 rows. All 30 share exactly
lat=41.641261, lon=-4.155937 despite four different onset date/time pairs across
2025–2026. This is consistent with a locality reference point, but does not
prove a centroid or independently confirm four distinct fires. Coordinates
must remain unverified; neither coordinate equality nor differing onset values
is a sufficient incident identity rule.

The offline inspector now reports shared-point evidence with row indexes and
counts of distinct onset values. It retains every row and performs no incident
merging. Repeated snapshots with identical onset do not trigger this evidence.
All 260 offline tests pass. No current precise-point map adapter is justified
by this sample. A report-list-first design is feasible while geometry and
identity questions remain unresolved; production implementation is not included.

## Standalone report preview

`spain_cyl_preview.py SAMPLE OUTPUT.html` renders a network-free standalone
review page from bounded JSON, reusing the inspector. It escapes all source
values, retains raw status/area wording and separate report/onset/extinction
times, and labels the sample as offline and incomplete. No coordinate plotting,
UTC conversion or incident deduplication is performed. Source and CC BY links
and a transformation notice are included. HTML escaping and conflict display
are regression tested; all 262 offline tests pass. This is a local preview,
not an installed HA card or finished provider.

## Latest bulletin selection

Added `spain_cyl_snapshot.py`: selects all rows at the newest report date/time
per exact province-set scope only when the supplied response row count equals
its reported total. Partial samples remain unfiltered, invalid/missing scope
or report times remain visible for review, and multiple incidents at the same
bulletin time are retained. This is neither incident deduplication nor proof
that the upstream collection or network pagination is complete or fresh.
Multi-province scopes stay distinct from individual provinces. Original spelling
is preserved; historical spelling normalization requires separate evidence.

The preview displays province names, selection scope and partial-sample warning.
All 267 offline tests pass. The real three-row sample remains unfiltered since
it is partial. No live retrieval loop or HA provider has been introduced.

## Bounded paging collector

`spain_cyl_paging.py` accepts a caller-supplied page fetcher and enforces at most
five pages, 100 rows and 1 MiB cumulative response bytes. It stops on errors,
changing totals, overlap, short/oversized pages and count overruns. Partial rows
are retained for diagnostics, never labelled count-complete. Even matching
counts retain snapshot_verified=false: offset paging can miss equal-count
revisions and the source has no established stable unique ordering key.

A one-off anonymous API check filtered to 2026-09-25 returned 18 rows in one
page. This validates basic retrieval, not live multi-page consistency; multi-page
failure cases are covered by synthetic tests. No periodic fetching was enabled.
All 272 offline research tests pass. The collector result must not be passed as
a verified current snapshot merely because its count_complete flag is true.

## End-to-end collection review

The saved 18-row retrieval contains nine province names, with 2 ACTIVO,
6 CONTROLADO, 6 EXTINGUIDO and 4 null status rows. These are report rows,
not independently verified unique fires or current conditions.

Fixed a collector-to-preview boundary issue: matching row counts previously
allowed collection uncertainty to be dropped by the generic response inspector.
Collected envelopes now retain collection status and never authorize latest-row
filtering merely through count equality. An initial retrieval failure remains
visible as a failed collection, not a successful empty result. Three pipeline
regressions cover matching totals, older-row retention and failure propagation.
The standalone preview uses Hungarian retrieval messages and all 18 sample rows.
All 275 offline research tests pass; no HA changes or new release.
