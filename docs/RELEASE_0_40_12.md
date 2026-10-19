# 0.40.12 — Combined map and summary setup

The location-summary editor can generate one combined configuration containing a
native Home Assistant map and the explicitly selected location summary. It retains
the summary title, forecast binding and other saved options without changing the
original card. The map requires no additional JavaScript module.

The map shows satellite detections and monitoring circles for all enabled IGNIS
locations; it is not filtered to the summary location. The summary remains bound
to the selected place. This distinction is explained in Hungarian and English.

## Use

Select a location in the summary editor, expand **Map and summary together**, and
choose **Generate configuration**. Copy the selected text into a new Manual card,
review its preview and save it yourself. JSON is accepted by the YAML editor.
Generate again after changing settings: the output is a snapshot. If replacing
an existing summary, avoid leaving an unwanted duplicate card.

Generation does not save a dashboard, enable providers, configure notifications,
change monitoring radii or modify history. No storage migration is required.

## Validation

Implementation PR #219 passed all 27 automated checks. All 52 frontend unit tests
passed. Browser coverage verifies generation, valid output and narrow-screen
layout. Tests also cover explicit binding rejection, nested configuration
preservation and quoted titles. This is automated coverage, not unaided setup
acceptance or a production installation of the release candidate.

## Update

Update through HACS, restart Home Assistant and fully reload the browser or
Companion App frontend. Existing cards and resource registrations remain valid.
Using the new combined configuration is optional; existing dashboards are not
changed automatically. See [summary setup](LOCATION_SUMMARY_CARD.md).
