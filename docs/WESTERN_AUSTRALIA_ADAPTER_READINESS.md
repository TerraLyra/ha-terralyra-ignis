# Western Australia adapter readiness — 2026-09-16

Status: official products identified; access approval required; no live sample.

| Product | Meaning | Catalogue licence | Access |
| --- | --- | --- | --- |
| [DFES-066 Incident Points](https://catalogue.data.wa.gov.au/dataset/dfes-emergencywa-incident-points-dfes-066) | Approximate reported incident location; accuracy varies | CC BY 4.0 now offered alongside the original BY-ND licence | SLIP account and DFES dataset approval |
| [DFES-064 Incident Areas](https://catalogue.data.wa.gov.au/dataset/dfes-emergencywa-incident-areas-dfes-064) | Selected observed incident extents; coverage and update timing vary | CC BY 4.0 now offered alongside the original BY-ND licence | SLIP account and DFES dataset approval |
| [DFES-068 Warning Areas](https://catalogue.data.wa.gov.au/dataset/dfes-emergencywa-warning-areas-dfes-068) | Community warning extent, not a fire perimeter | CC BY-ND 4.0 | SLIP account and DFES dataset approval |

The catalogue also labels individual service resources Government Use Only. Clarify
that mismatch with the broader applicant description before choosing a service.
Open metadata is not anonymous access to the data. The pages require Emergency WA
terms and attribution in addition to the listed licences.

## Implementation decision

Begin with DFES-066 after approved access and permitted distributed-client use are
confirmed. Do not embed a developer account credential in the public integration.
Determine whether each HA user needs their own account; do not introduce a required
Cloud account or relay as an assumed solution.

Keep incident areas and warning areas separate. The existing report model represents
incident points and warning areas; incident-area support needs an explicit model and
presentation extension. Do not relabel DFES-064 as a warning polygon. Its mapped extent
cannot establish property damage, and missing polygons do not mean no incident.

Warning-area transformation and redistribution require a separate assessment of the
BY-ND conditions and Emergency WA terms. Do not copy the incident product licence
onto warning products. No legal conclusion about a particular transformation is made.

## Required access and next checks

The catalogue directs applicants to register with SLIP, request membership of the
DFES Restricted EmergencyWA User Group and request the specific dataset. The request
needs entity/role details and the proposed use. No account was created, no request was
sent and no agreement was accepted in this review.

After approval, inspect the documented ArcGIS/WFS service and a bounded sample:
IDs and update semantics; fire versus other incident categories; planned burns;
time zone; coordinate reference system; pagination/completeness; request limits;
authentication renewal; attribution; caching and retention conditions. Keep schema
fixtures synthetic until sample redistribution is permitted. WMS map images alone
are not a structured event feed.

The [DFES FAQ](https://www.dfes.wa.gov.au/emergencywa/faq) documents SLIP and also
points to RSS/CAP options. These are separate products whose current endpoints and
conditions still need verification, not an assumed equivalent anonymous fallback.

No production adapter, release, HA change or history migration is included.
