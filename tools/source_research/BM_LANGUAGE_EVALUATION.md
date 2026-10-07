# Offline Hungarian language evaluation

No production dependency, model redistribution, event-coordinate inference or HA
configuration change. `bm_language_probe.py` runs an explicitly installed local
spaCy-compatible model and preserves original text, character spans, lemmas,
entity labels and dependency edges. It does not fetch models or event pages.

## Reproduce

Use an isolated environment; install the selected model separately. Run:

```
python tools/source_research/bm_language_probe.py tools/source_research/fixtures/bm_language_development.json
```

The fixture is synthetic development material, not an independent holdout or
representative accuracy benchmark. Real RSS samples remain local. No accuracy
percentage is justified from these small, previously inspected samples.

## Initial probe, 2026-10-07

HuSpaCy hu_core_news_md 3.8.1 (model metadata: CC BY-SA 4.0), spaCy 3.8-compatible.
Official metadata: https://huggingface.co/huspacy/hu_core_news_md/blob/main/meta.json
The downloaded model wheel was 126,995,383 bytes, excluding dependencies. It is
not added to the integration. Redistribution requirements for code, model and
any derived resources must be reviewed independently before packaging.

Seven synthetic notices and four saved RSS notices were inspected. Model load
was about 1 second and analysis about 0.33 / 0.32 seconds respectively in this
local run; this excludes Python/import startup and is not an HA device benchmark.

- Real Gyöngyösön and Nagylókon mentions were recognized, with useful base forms.
- Synthetic “Gyöngyös Tűzoltóság” was ORG, not LOC.
- Synthetic Nagylókon recognition varied with the surrounding sentence.
- Negated Dabason and directional Budapest were still LOC. LOC is not an incident role.
- Street names and M5-ös also received LOC: a gazetteer link must distinguish
  settlements from other geographic objects.
- Firefighter adjectives were not consistently reduced to settlement names.
- No fire-type prediction is provided by this general-language model.

## Required next layer

Link mentions to the packaged gazetteer without coordinates in the review output.
Keep mention roles separate: event candidate, responder/organization, direction,
street, negated, historical, unknown. Multiple mentions of one place may have
*different* roles; never blacklist the whole settlement because responders also
come from it. Organization recognition is only supporting evidence, not a guarantee.

Required role cases include settlement + tűzoltóság, inflected organization names,
adjectival firefighters, shared-noun responder lists and cross-sentence boundaries.
A responder-only article must retain an unknown event location.

Model fire involvement separately from reported state: vegetation/building/vehicle
may coexist; threatened does not mean burning; negated ignition is not ignition;
extinguished refers to the report time, not independently verified current status.

Before implementation selection: annotate a larger development corpus, reserve
unseen notices for holdout evaluation, compare baseline and hybrid outputs for
missed places, wrong event-place promotion and multi-label fire involvement.
Measure memory and startup cost on representative hardware. Do not tune on the
holdout and then describe it as independent validation.

## Experimental role annotations

`--roles` adds `bm_language_roles.py` output using the packaged HU gazetteer.
Exact/lemma matches and narrowly marked adjectival candidates are retained with
original spans. Organization, responder/list, direction, street and immediate
negation hints are separate from identity. All other mentions stay unknown;
there is deliberately no event-location promotion or coordinate output.

The seven development cases identify the expected responder lists and direct
negation/direction hints. Nagylókon remains missed in one synthetic description
because the model leaves its lemma inflected. These are development observations,
not holdout accuracy. Fire involvement/state classification is still pending.
No production module imports the optional NLP model or role annotator.

## Experimental involvement evidence

The `--roles` probe also emits clause-local `fire_review` hints: multiple object
categories, threatened objects and reported extinguishing. Evidence spans remain
available. Neither active nor extinguished *current* status is asserted.

On the synthetic development pair, HuSpaCy lemmas allowed vegetation+building
spread and vegetation-only burning with a threatened/non-ignited building to be
distinguished. However, “elfojtották” was lemmatized as “elfojtot”; extinguishing
was missed. Do not count idealized-lemma unit tests as model accuracy. Wider
negation/modal scope, cross-clause references, separated verb particles and
unseen reports remain unvalidated. This module is not a production classifier.

## Frozen unseen-sample probe, 2026-10-07

Evaluated commit 728d603 against six newly retrieved RSS notices 92638–92643.
Manual expectations were written before inspecting model predictions. No role,
lemma or fire rule was changed on the basis of this batch. The corpus is now
seen and cannot remain a holdout if subsequently used for development.

Across the six records, all eight expected event-place names were present in the
hybrid mentions (seven in the baseline). This is name coverage, NOT event-role
accuracy or verified incident geography. Kecskemétnél accounts for the difference.
Between-town corridors remain unresolved geography, not town-centre coordinates.

Only three of nine annotated municipality responder targets received responder
hints. All six targets in the long Szeged–Algyő notice were missed as responders;
several names were recognized but remained unknown. The current list grammar and
adjective/gazetteer linkage are inadequate. Rózsadomb was additionally proposed
as a responder district, which the municipality-target annotation did not cover.

Union of title/description fire categories matched the manual category sets in
these six cases (two fire notices, four accidents). Empty category output does
not confirm absence of fire, and these notices do not validate mixed-fire,
threatened-building or extinguishing behavior. The Budapest building category
came from the title; the body was missed.

Decision: keep experimental. Next research should use dependency/clause structure
for shared-noun responder coordination, preserve unmatched list members, and
explicitly model geographic corridors. Freeze this batch as a regression corpus
if used for tuning; collect a new holdout afterward. Do not present a general
accuracy percentage or integrate this model into HA on these results.

`bm_language_score.py GOLD PROBE` reproduces the bounded comparison. Raw RSS,
manual labels and model outputs are retained locally, not packaged with IGNIS.
