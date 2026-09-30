# GWIS forecast access spike

Status: research only, checked 2026-09-30. No HA provider, entities, scheduled
requests or automatic fallback are enabled.

## Access and attribution evidence

The [JRC dataset catalogue](https://data.jrc.ec.europa.eu/dataset/4b4f1ea6-da7b-4870-9be4-aa5b9a2a4b70)
identifies anonymous access and the European Commission reuse notice for the view
and download services. The [GWIS licence](https://gwis.jrc.ec.europa.eu/about-gwis/data-license)
permits reuse of EU-owned content under CC BY 4.0, subject to individual notices
and third-party rights. Retain product attribution and indicate transformations;
this evidence is not a provider quota or availability guarantee.

## Observed service

The official [data page](https://gwis.jrc.ec.europa.eu/applications/data-and-services)
and its linked `gwis_data_services.js` publish an HTTPS WMS endpoint:
`https://maps.effis.emergency.copernicus.eu/gwis`, layer `ecmwf.fwi`.
The download page currently requests PNG maps, not numerical TIFF data. Its
script chooses tomorrow using browser-local date arithmetic; do not copy that
as evidence of model issuance or UTC product semantics.

A bounded WMS 1.3.0 GetCapabilities request showed:

- `ecmwf.fwi` explicitly has `queryable="0"`. Service-wide GetFeatureInfo formats
  do not imply that this particular layer permits point queries.
- Global geographic bounds are advertised, but have not been validated at all
  target regions or at the poles.
- Time is advertised as `2018-01-01/2099-12-31`, default `2019-01-01`.
  This is not an inventory of actual forecasts or evidence of freshness.
- The layer abstract says reanalysis, whereas the download page says forecast.
  Resolve this mismatch before relying on date semantics.
- Advertised operation links use HTTP. Inspection never follows them; retain the
  verified HTTPS endpoint rather than downgrading transport from metadata.

Two small 64 × 64 WMS 1.1.1 GetMap requests used an impersonal test bounding box
`10,40,20,50` (longitude/latitude), PNG, transparent, empty style:

| Requested TIME | Result | SHA-256 |
| --- | --- | --- |
| 2026-10-01 | HTTP 200, 970-byte coloured PNG | `edaa130142b7e7ba634bd6f4e5d04487837cdfff797bd431ee25cc1b14746306` |
| 2099-12-31 | HTTP 200, empty-looking PNG | `8d447892b6efbc450beab391a7003090694cfcd0014d20766150112cab1675a0` |

The first response advertises `Cache-Control: public, max-age=3600`. This is HTTP
cache lifetime, not issuance time or guaranteed model freshness. The control
response demonstrates that HTTP success and a valid image do not establish a
valid forecast. An empty image must never become low danger. These are isolated
samples, not a soak test or proof that current and future dates are authoritative.

## Numerical TIFF control

The advertised `image/tiff` format was also tested with the same parameters.
Unlike the download page's PNG, this returned a single 32-bit IEEE floating-point
band with georeferencing, so a numerical route is a viable candidate:

| TIME | Bytes | Observed values | SHA-256 |
| --- | --- | --- | --- |
| 2026-10-01 | 16810 | 0 to 56.51939010620117 | `78b944a7430868c13562c6f65ca7596971b223a2010366cfbe6fe11bf1407d02` |
| 2099-12-31 | 16810 | All 4096 pixels equal 0 | `ca03e40b7acada95fcc781b0724d7f9efd2a0226736b4c0de7bdc7ecfd2926b6` |

Both samples have one uncompressed band, sample-format tag 339 = 3, and no
GDAL_NODATA tag (42113). Thus an absent product can look like a legitimate zero-FWI
raster. Do not turn these responses into low-risk sensors. A nonzero raster alone
also does not establish issuance or the semantics of the requested date.
A production decoder needs independent product availability and a supported
nodata/mask convention before it can distinguish valid zero from missing data.
Do not solve this by declaring every zero invalid: genuine zero FWI is possible.
The original numerical values remain unclassified research evidence.

## Offline tool

Run `python tools/source_research/gwis_capabilities.py saved-capabilities.xml`.
The tool reads at most 3 MB, rejects DTD/entity declarations, malformed/error XML,
excessive depth/nodes and duplicate target layers/time dimensions. It preserves
advertised evidence and always reports `production_ready: false`. It neither
fetches data nor follows metadata links. Synthetic tests run in source-research CI.

## Initial gates (updated by the point-query findings below)

1. Establish a supported numerical query/download route, or a documented stable
   class palette and nodata semantics. Do not infer a numerical FWI from colour.
2. Prove actual product availability, forecast valid dates and model issuance;
   include missing/expired/future-date controls.
3. Validate representative global regions with public test points, then bound
   request counts, response sizes, cache lifetime and failure handling.
4. Keep the GWIS six-class scale separate from FRMv3's five classes. The current
   [technical page](https://gwis.jrc.ec.europa.eu/about-gwis/technical-background/fire-danger-forecast)
   includes Very Extreme; the catalogue's older classification differs. Boundary
   values also need precise machine-readable semantics before classification.
5. Check product-specific notices, attribution and operational stability before
   proposing an opt-in runtime adapter. No HA location data is used by this spike.

## Follow-up: dedicated point-query layer

The official viewer's linked `static/js/app.bundle-2.11.5.js` maps `ecmwf.fwi`
to the **separate** `ecmwf.query` information layer on the same HTTPS endpoint.
Capabilities explicitly mark that layer queryable. Thus the earlier observation
about `ecmwf.fwi` does not rule out supported point access.

WMS 1.1.1 GetFeatureInfo, EPSG:4326, `INFO_FORMAT=text/html` returns a small
`Fire Danger` table with numeric FWI and seven companion indices. GML/text/plain
responses tested did not contain the numeric attributes. Use the dedicated HTML
schema defensively; do not scrape arbitrary viewer text or execute HTML.

Observed 2026-10-01 requests using public, impersonal test points:

| Longitude, latitude | FWI |
| --- | --- |
| 15, 45 (Europe) | 17.294014 |
| -120, 38 (California) | 52.370739 |
| 139.7, 35.7 (Japan) | 0.23292935 |
| 149, -33 (Australia) | 20.311758 |
| 25, -25 (southern Africa) | 5.4818907 |
| -140, 0 (ocean control) | -9999 (nodata) |

A 2099-12-31 point request returned an empty body, unlike the ambiguous zero-filled
TIFF. These routes are not interchangeable. A ten-request cycle for 2026-09-30
through 2026-10-09 returned numeric evidence at the European test point; no
user-configured HA coordinates were involved. This is sampled coverage, not a
global completeness or service-availability guarantee.

`gwis_point.py` validates the exact bounded table, preserves raw numeric strings,
keeps genuine zero, distinguishes empty/no-feature and -9999/nodata, and rejects
malformed/error/duplicate tables, unexpected markup and non-finite values.
`gwis_fetch.py` performs an explicit research cycle of at most ten requests,
spaced by one second, without redirects, retries, persistence or HA activation.
It aborts on transport/schema errors and rejects a cycle crossing UTC midnight.
The socket timeout is not a guaranteed total wall-clock deadline.

Remaining **time-contract gate**: the response contains neither model issuance
nor a returned valid date. Store `requested_date` separately from `retrieved_at`;
leave `model_issued_at` and `returned_valid_date` unknown. The viewer constructs
its own dates and does not independently validate them. The separate query layer
resolves the tested zero/nodata ambiguity but does not establish model freshness,
update schedule or date-selection guarantees. No forecast is marked production
ready. A current supported product time contract or independent dated metadata,
plus repeated operational validation, is still required for runtime activation.
