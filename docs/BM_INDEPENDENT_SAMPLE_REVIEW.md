# BM OKF independent sample review — 2026-09-24

Source: https://www.katasztrofavedelem.hu/10466/RSS_VESZ (BM OKF).
Three notices were evaluated before adapting the reviewed alias vocabulary.
Linked event pages were not fetched. Original RSS and evaluation output remain
local; the repository contains only observations and synthetic regression tests.

## Frozen baseline

| Notice ID | Human interpretation of RSS | Existing matcher |
| --- | --- | --- |
| 92249 | House fire in Gersekarát; several responding-unit towns | No mentions |
| 92248 | Road collision near Somlóvásárhely | No mentions |
| 92247 | Railway collision in Berettyóújfalu; travel/disruption route towns also mentioned | Berettyóújfalu and Biharkeresztes, both from route wording |

Gersekarát and Somlóvásárhely are absent from the inspected bundled cities500
extract. The other gaps include unlisted inflections. The railway result is not
an event-location success simply because its town also appears in a bus route.
This is three observations, not a statistically useful accuracy estimate.
No automatic fire classifier exists in this prototype; the two accident reports
must not be advertised as proof of tested fire/non-fire classification.

## Changes after evaluation

Add manually reviewed forms for Vasvár, Körmend, Zalaegerszeg, Szombathely, Ajka,
Berettyóújfalu and Püspökladány already present in the existing database. Synthetic
regressions preserve route ambiguity and ensure recognized responders do not
supply a missing event location. All 220 offline source tests pass.
These three reports are now development examples, not a future independent test
set. New held-out events are required for further evaluation.

## Remaining gates

- Fill demonstrated settlement coverage gaps using a reviewed, licensed supplement
  or a broader update to the existing GeoNames bundle; do not invent coordinates.
- Add explicit route-context clues and handle complex responder grammar, including
  missing/shared nouns. Retain evidence and unresolved ambiguity.
- Keep mention recognition distinct from event-location verification and incident
  category. No production map wiring is authorized by a text match alone.

The existing database is unchanged. This work adds no requests, HA entities,
calendar changes, history mutations or source-page scraping.

## Fuller GeoNames coverage audit

The official HU.zip extract inspected on 2026-09-24 contains both gaps:

| Primary name | GeoNames ID | Feature | Population field |
| --- | --- | --- | --- |
| Gersekarát | 3052299 | PPL | 0 |
| Somlóvásárhely | 3045268 | PPL | 0 |

Zero is the upstream field value, not evidence that these settlements have no
inhabitants. The country file includes 9,816 PPL records and 5,964 PPLX records,
plus administrative seats and other populated-place types. It is not a list of
municipalities. cities1000/cities5000 are narrower population-threshold products,
not upgrades in coverage. Source and CC BY 4.0 terms:
https://download.geonames.org/export/dump/readme.txt

Reproduce the read-only audit with a locally downloaded official HU.zip:

```sh
python tools/source_research/bm_geonames_coverage.py /path/to/HU.zip Gersekarát Somlóvásárhely
```

Inspected HU.txt SHA-256:
`ffa610721cad39a9f5c4d17f398d8ef7344180b2797e25d34bd23fac79176264`.
No full upstream extract is committed. The audit outputs provenance and name
coverage, not incident coordinates or confidence scores.

Recommended implementation: extend the existing database build with a separately
selectable Hungarian name-lookup table retaining upstream IDs and feature codes.
Keep the existing nearest-place table until label-impact tests justify changing
it. Filter populated-place types explicitly; do not indiscriminately import all
country features, historical settlements or sublocalities. Retain homonyms and
review ambiguity. The current 5,000-record research guard must be deliberately
reworked before using the full set, never bypassed by silent truncation.
Inflected forms such as Gersekaráton still need reviewed handling; database
coverage alone does not fix suffix matching, route/responder ambiguity, or event
location verification. No production database replacement is made by this audit.

### Hungarian supplement implementation

The first implementation now provides `geonames_hu_names.sqlite3` with 10,048
filtered records, stable GeoNames IDs, source hash and license metadata. The
existing cities500 table is unchanged. Rebuild with:

```sh
python tools/source_research/bm_hu_gazetteer.py /path/to/HU.zip custom_components/terralyra_ignis/data/geonames_hu_names.sqlite3
python tools/source_research/bm_review_sample.py /path/to/sample.json --hungary-supplement
```

This is an explicit offline research option. Both missing names and their reviewed
inflected forms are recognized; results remain unverified location candidates.
The bounded matcher now accepts up to 20,000 places and rejects excess input,
rather than silently truncating. Homonyms retain separate IDs. The builder stages
and replaces output only after successful validation; an invalid rebuild preserves
the previous database. All 223 research tests pass, including the complete bundled
Hungarian lookup and synthetic filtering/identity/failure cases. These checks do
not constitute independent real-report accuracy validation.

Coverage comparison also found legacy cities500 names outside the selected country
feature types, including Budapest districts. The expanded research option retains
all baseline names absent from the supplement, with their old IDs. Country records
supply exact-name matches and preserve their homonyms. Both database hashes are
reported. This union avoids losing existing name coverage while excluding bulk
import of additional sublocalities; it is not coordinate/identity reconciliation.
The added coverage-preservation regression brings the suite to 224 passing tests.

### Independent follow-up, 2026-09-24 09:36 UTC

RSS notices 92253 (Komoró road collision, 10:57 +0200) and 92252 (Debrecen
four-vehicle collision, 10:22 +0200) were evaluated without vocabulary changes.
No linked pages were fetched; raw samples and outputs remain local.

- Baseline: no mention for Komoró; Debrecen recognized in title and description.
- Expanded: Komoró recognized in the description's primary-name occurrence;
  title form `Komorónál` and responding-unit adjective `kisvárdai` remain unmatched.
- Expanded: Debrecen recognized, but the title's `Négyes` also matches a real
  settlement name. Human reading identifies it as the vehicle-count adjective,
  not a second incident location. This is a concrete lexical false positive
  introduced by broader coverage, not an upstream coordinate error.

All results stay unverified. These notices describe accidents, not fires; the
prototype still has no automatic fire classifier. Before production, resolve
common-word/settlement ambiguity conservatively with contextual evidence. Do not
blacklist the real settlement Négyes globally. Preserve this frozen outcome for
subsequent comparisons and use fresh notices for future independent evaluation.

### Context follow-up after the frozen 92252/92253 evaluation

Added an evidence-preserving `possible_vehicle_count` hint for the exact adjacent
`Négyes karambol` construction (case-insensitive, same line). It does not delete
mentions, change the multiple-candidate flag, or verify a location. Other uses,
including `Négyes közelében` and `Négyesen`, stay eligible candidates. This narrow
clue does not solve general common-word disambiguation.

Reviewed Komoró/Kisvárda forms now recognize `Komorónál` and attach the existing
responder hint to `kisvárdai hivatásos tűzoltók`. The retained RSS sample confirms
these effects and the count hint in the Debrecen title. These two reports are now
development examples, not held-out validation. The original pre-change findings
above remain unchanged. All 227 offline research tests pass, including separate
count/town occurrences in one sentence and boundaries preventing clue propagation.

### Shared responder nouns with mixed qualifiers

The previously observed `ajkai hivatásos és a somlóvásárhelyi önkéntes
tűzoltókat` construction now gives both known adjectives a shared
`responder_list_reference` hint. Each list member may have its own explicit unit
qualifier and a conjunction may be followed by an article. Unknown adjectives,
other nouns, sentence boundaries and line breaks block this propagation.
Original mentions and exact shared evidence remain intact. A separate primary
Somlóvásárhely mention outside the list remains unmarked and unverified.

Replaying retained notice 92248 confirms the shared responder hints. This is a
regression replay of a development example, not new independent validation.
All 230 offline research tests pass. No production provider or HA state changes.
