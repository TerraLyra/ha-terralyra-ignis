# ACT Current Incidents — questions needed for production use

Prepared 2026-09-16. Unsent technical question list, not provider correspondence.
The current feed is publicly readable; GitHub or Home Assistant access does not
resolve these source-data questions.

1. Does `Updated` and `Time of Call` use ACT local civil time (including AEDT),
   fixed AEST, or another convention? Does `pubDate` reliably switch its label?
   How are repeated or nonexistent times at daylight-saving transitions represented?
   An official schema/time specification or offset-bearing examples covering both
   seasons and the transitions would resolve this without guessing.
2. Is `GRASS AND BUSH FIRE` the complete relevant vegetation-fire type, and can an
   anonymized Current Incidents XML example or official type dictionary be supplied?
   Keep planned burns and structure fires separate; editorial news pages do not
   establish the XML field contract.
3. Optional validation, not a research blocker: how are test, exercise, drill and cancelled records identified in Current
   Incidents? Are they excluded upstream, or is there a documented structured flag?
   Absence of TEST wording must not be treated as confirmation of a real event.
4. Are `guid` and `cadid` stable for the lifetime of an incident, and can they be
   reused? What does removal from the feed mean? Removal must not imply closure.

Current Incidents alone is the proposed source. CAP is a separate product: its
licence, record linkage and timestamp meaning would require separate confirmation
if it were introduced. An observed CAP call-time offset does not establish the
RSS update-time convention.

## Development decision if evidence is unavailable

A limited, explicitly labelled research/diagnostic component can be developed
without converting dates or publishing calendar events. It would not constitute
completion of the production ACT source. A map-only scope would also need an
explicit treatment of unverified exercise metadata, incident identity and freshness;
removing the calendar does not automatically resolve those uncertainties.

For the complete dated production adapter, obtain the source contract or equivalent
verifiable evidence first. Existing incident history must remain untouched.
