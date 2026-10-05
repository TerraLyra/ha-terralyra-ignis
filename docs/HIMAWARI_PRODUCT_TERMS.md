# Himawari product access boundaries

Checked 2026-10-05. Two different derived fire products must not inherit each
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
- Apply these terms to JAXA WLF specifically, with the date boundary and credits
  above. Do not extend this scope to raw HSD, other model products or the separate
  KCL/IPMA product. Retain the general site-policy link for downstream users;
  a change of intended use needs its own terms review.
- The [2018 P-Tree service terms](https://www.eorc.jaxa.jp/ptree/terms.html) require
  registration and credential responsibility. Their section 6 restriction on
  redistribution explicitly names **Himawari Standard Data**, not all derived WLF
  products; do not misreport it as a blanket ban on WLF redistribution.

Implementation boundary: target JAXA WLF Level 2 only, with observation times
at or after 2026-02-01T00:00:00Z. Reject missing/ambiguous times and earlier data
from this adapter rather than inferring eligibility from download time. This
restriction does not delete existing user history. Use each installation's own
registered access, never distributed project credentials. Preserve JAXA P-Tree,
WLF and JMA provenance in source details and exported observations. User Guide
section 3 and FAQ Q4-2 define reporting/credit expectations. No account is needed
for offline development; authenticated transport and real-file validation remain
separate implementation gates. See [WLF adapter contract](JAXA_WLF_ADAPTER.md).

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

Both routes remain inactive. JAXA WLF now proceeds through its technical
validation gates; the separate CAMS route retains its access/licence gates.
JAXA WLF and CAMS FRP need separate decoders, quality handling and attribution.
Neither constitutes a fire-danger forecast: both report satellite observations.
