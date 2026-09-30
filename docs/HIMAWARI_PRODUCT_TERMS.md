# Himawari product access boundaries

Checked 2026-09-30. Two different derived fire products must not inherit each
other's terms, credentials or algorithms. Neither is an enabled IGNIS provider.
This records product/access requirements, not correspondence or account details.

## JAXA P-Tree Wild Fire (WLF)

- The [FAQ](https://www.eorc.jaxa.jp/ptree/faq.html), Q3-3-6-1, describes WLF as
  CSV. Q1-2 requires an account for data access; Q1-8 supports FTPS/SFTP.
- Q4-1 explicitly permits commercial use of qualifying Himawari products from
  2026-02-01 00:00 UTC, including geophysical parameters. Older observations
  remain subject to the previous non-profit restriction. Never apply this date
  change indiscriminately to other products or archived data.
- The FAQ routes FTP research data to the
  [research-data terms](https://earth.jaxa.jp/en/data/policy/index.html).
  Section 2 allows use, modification and redistribution without fees, with JAXA,
  research-product and other contributor credits. Section 2.3 requires advance
  notification of commercial use; it does not itself describe an approval queue.
  Section 2.2 requests publication notification where possible.
- These research terms also require compliance with the
  [general site policy](https://global.jaxa.jp/policy.html), whose generic
  commercial-use clause requires prior permission and whose generic modification
  clause is restrictive. The specific research grant appears intended to permit
  derived-data use, but the relationship of these clauses for a distributed
  software product should be confirmed rather than silently assuming precedence.
- The [2018 P-Tree service terms](https://www.eorc.jaxa.jp/ptree/terms.html) require
  registration and credential responsibility. Their section 6 restriction on
  redistribution explicitly names **Himawari Standard Data**, not all derived WLF
  products; do not misreport it as a blanket ban on WLF redistribution.

Implementation boundary: restrict any future adapter to the confirmed WLF
product/version and allowed observation dates; use each installation's own
registered access rather than distributing project credentials. Clarify whether
local caching, parsed map markers and a public open-source client fall under the
specific research-data grant, and whether notification alone suffices for any
commercial deployment. Open-source distribution by itself does not establish
that every downstream use is non-commercial. No credentials or account creation
are needed for offline development.

## KCL/IPMA CAMS FRP-PIXEL List Product

- The [KCL access page](https://wildfire.geog.kcl.ac.uk/products-and-data/) describes
  near-real-time Himawari FRP and directs users to discuss access with the group.
  That is an access instruction, not a complete reusable-client licence.
- The [NASA product description](https://firms.modaps.eosdis.nasa.gov/descriptions/FIRMS_GOES_JAXA_Himawari-9.html)
  attributes Himawari-9 FRP-PIXEL to IPMA under CAMS using KCL algorithms. Its
  display in FIRMS does not make it a documented FIRMS Area API source.
- The historical CAMS GOES/Himawari user manual describes a public FTP List
  Product and scientific citations. It concerns older product generations and
  does not establish a current secure Himawari-9 endpoint/service contract.
- The [Copernicus product licence](https://ecds.ecmwf.int/licences/licence-to-use-copernicus-products)
  permits lawful use, distribution and adaptation without fees for products
  within its stated scope, except separately flagged items. It requires visible
  CAMS attribution, modified-data notices where applicable and the stated
  responsibility disclaimer. CAMS affiliation alone is not sufficient evidence
  that the exact current third-party endpoint/product carries that licence.

Implementation boundary: establish the current Himawari-9 List Product version,
secure machine endpoint, authentication, request limits and its explicit licence
mapping or separate terms. If the standard Copernicus grant applies without an
exception, a bespoke reuse permission may not be needed; access provisioning and
product confirmation remain distinct requirements. Do not label the licence
uncertainty as proof that reuse is forbidden, or borrow LSA SAF's CC BY 4.0 grant.

## Runtime decision

Both routes remain inactive until these product-specific gates are settled.
JAXA WLF and CAMS FRP need separate decoders, quality handling and attribution.
Neither constitutes a fire-danger forecast: both report satellite observations.
