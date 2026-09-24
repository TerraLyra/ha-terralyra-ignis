GeoNames cities500 data
=======================

Source: https://download.geonames.org/export/dump/cities500.zip
Project: https://www.geonames.org/
License: Creative Commons Attribution 4.0 International (CC BY 4.0)
License URL: https://creativecommons.org/licenses/by/4.0/

The bundled SQLite database is a derived, reduced copy containing only the
coordinates, primary place name, country code, first-order administrative code,
and population needed for offline nearest-settlement lookup.

Natural Earth country boundaries
================================

Source: https://www.naturalearthdata.com/downloads/110m-cultural-vectors/110m-admin-0-boundary-lines/
Dataset: Natural Earth 1:110m Admin 0 boundary lines
Version: 5.1.0
License: Public domain

country_borders.json is a reduced European extract containing only rounded
longitude/latitude line geometry needed by the static FRMv3 map renderer.

GeoNames Hungarian name supplement (research consumer only)
===========================================================

File: geonames_hu_names.sqlite3
Source: https://download.geonames.org/export/dump/HU.zip
Project: https://www.geonames.org/
License: Creative Commons Attribution 4.0 International (CC BY 4.0)
License URL: https://creativecommons.org/licenses/by/4.0/

Reduced country extract inspected 2026-09-24. Contains primary name, GeoNames ID,
feature code, admin1 code and settlement coordinates for HU populated features
PPL/PPLA/PPLA2/PPLA3/PPLA4/PPLA5/PPLC/PPLL. Other classes, historical/abandoned
places and PPLX sublocalities are excluded. This is not a municipality register.
Upstream content hash and selection are recorded in the metadata table.
Rebuild with tools/source_research/bm_hu_gazetteer.py HU.zip destination.sqlite3.
The research matcher returns names and IDs only. Coordinates describe the place,
not an incident. This file does not change runtime nearest-settlement lookup.
