# JAXA WLF adapter contract (not active)

This is a separate product from the IPMA/KCL FRP-PIXEL foundation. No production
provider, entity, map layer or notification is enabled by this document.

## Verified format

The official [Level 2 README](https://www.eorc.jaxa.jp/ptree/documents/README_Himawari_L2WLF.txt)
describes version 1.00 CSV, ten-minute observations, and filenames identifying
Himawari-8/9, observation time, version and grid dimensions. Two comment headers
precede rows; acquisition/processing times and row dates are UTC. Coordinates
are grid centres. Preserve observation and processing times separately.

FRP is documented in W/m², and grid area in km². It is not directly a MW value.
The README defines cluster totals as the sum of area times FRP for matching HC.
With those units, the numerical product is MW; confirm the current file's units
before implementing conversion. HC denotes the hottest grid, not necessarily
the grid with maximum FRP, and is not a persistent incident identifier.

Preserve fire level, reliability, volcano count and quality flags. The published
quality codes distinguish normal, saturation and low confidence. Do not treat
missing rows as proof of no fire or infer event extinction from feed disappearance.

## Next implementation gates

1. Obtain a recent authenticated WLF L2 CSV and its original filename/header.
   Verify current column spelling, date format, units, empty-file representation,
   missing values and agreement between filename/header/row times. Until then,
   do not invent a production parser from prose alone.
2. Accept only timezone-aware observation times on/after 2026-02-01T00:00:00Z;
   test the exact cutoff, offset conversion, older/missing/naive timestamps.
3. Build an offline bounded decoder with synthetic malformed-input tests and a
   provenance-preserving normalized model. Determine conservative quality handling
   from the product specification and representative rows, not CAMS flag meanings.
4. Validate secure P-Tree transport, per-user credentials, timeouts, bounded size,
   retries and redacted diagnostics. Never fall back silently to plaintext FTP.
5. Only then add opt-in configuration, source health, correlation and display tests.
   Keep original satellite identity and required JAXA/JMA credits visible.

A licence clarification does not itself validate a transport or decoder. No raw
imagery download is needed for this small CSV product. Existing historical data
and unrelated source settings must remain untouched.
