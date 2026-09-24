# 0.30.1 — Clearer BM accident reports

The optional BM card labels explicit accident reports without detected fire
wording as “Baleseti jelentés · tűz nincs említve”. These candidates remain under
All reports but are hidden in the default focus view. No source records or history
are deleted. Smoke, fire, extinguishing clues, uncertainty and missing/truncated
descriptions prevent this label. It does not prove there was no fire.

Update the integration through HACS and restart HA. Replace the separately
installed `/config/www/ignis-bm-reports.js` with the attached file, change the
existing module resource URL to `/local/ignis-bm-reports.js?v=0.30.1`, and fully
reload the browser. Do not create a duplicate resource. HACS does not replace
this frontend file automatically. The existing report-map card is unchanged.

Validation includes 241 offline research tests and browser coverage of display-only
filtering, safe text/links, explicit retrieval, mobile layout and failure clearing.
The HA response regression verifies original notices and shared cache are preserved.
Live verification of this revision follows installation.
