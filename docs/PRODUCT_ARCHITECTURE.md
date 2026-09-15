# TerraLyra IGNIS architecture

This public Home Assistant integration provides useful local wildfire monitoring
without a TerraLyra Cloud account. It retains direct provider access, normalized
observations, basic incident tracking, existing local evidence/trend features,
location matching, history, reports and HA automation support.

General geographic functions and location value objects belong to the public
basic layer. HA configuration, entities, storage and attribute projection belong
to the HA adapter. The package is not yet a standalone Core SDK.

Optional external services may consume the same public models and return
versioned results. They are not dependencies of local operation. Advanced
service-side implementation is outside this repository.

The integration domain remains `terralyra_ignis`. Repository relocation must
preserve config-entry IDs, entity IDs, event contracts and user history. Moving a
repository is not authorization to remove/re-add the integration or purge data.

Source observations retain provider attribution and timing. Official reports,
satellite observations and forecasts remain distinct. See SNAPSHOT_PROVENANCE.md
for the original source and migration readiness.
