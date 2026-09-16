# ACT paired-feed time evidence — 2026-09-16

Research only; no CAP adapter or licence conclusion.

The [official ESA feed page](https://esa.act.gov.au/be-emergency-ready/warnings-alerts)
links both products. Sequential bounded HTTPS reads (25 seconds, 1 MiB each, no
redirect following) returned HTTP 200: Current Incidents 5,664 bytes, CAP 27,427 bytes.
Endpoints: https://esa.act.gov.au/feeds/currentincidents.xml and
https://data.esa.act.gov.au/feeds/esa-cap-incidents.xml .

RSS contained seven items: one HOUSE FIRE and six AMBULANCE RESPONSE. The house fire
is not a vegetation-fire example and must not enter the vegetation-fire category.
CAP contained seven CAP 1.2 alerts inside an EDXL-DE 1.0 EDXLDistribution envelope.
All had Actual/Alert/Public metadata. Event categories were Structure Fire (one) and
Other Urgent Alerts (six). Raw payloads, locations and identifiers are not committed.

CAP sent/effective/expiry strings had explicit +10:00 offsets. Each RSS guid occurred
in exactly one sampled CAP identifier. Using this provisional substring join, all
seven CAP sent clock readings equalled RSS Time of Call; none equalled RSS Updated.
CAP sent and effective matched. The requests were not an atomic snapshot, and this
join is not a verified production identity mapping.

Do not replace RSS update time with CAP sent to resolve timezone uncertainty: the
sample shows different time meanings. An explicit offset establishes representation,
not event-revision semantics or RSS summer/DST behavior. Keep call, update, publication,
CAP sent/effective and retrieval dates separate. CAP expiry does not prove closure.
Actual is message metadata, not independent evidence of an active wildfire. The two
feeds must not be counted as independent observations merely because formats differ.

Remaining gates: authoritative CAP licence scope, identifier mapping, update/cancel/test
examples, vegetation-fire sample, RSS timezone and CAP timestamp semantics. The explicit
CC BY 4.0 statement for Current Incidents is not assumed to cover CAP automatically.
No agency contact, HA change, release or production adapter was made in this review.

## Offline classification update

The observed RSS HOUSE FIRE type now maps to structure_fire, independently from
vegetation-fire candidates and planned burns. Test markers remain independent.
No unobserved STRUCTURE FIRE spelling or other fire subtype is assumed equivalent.
Three synthetic regression tests cover category separation, source type precedence
and exercise flags. All 41 offline tests pass with system Python.
