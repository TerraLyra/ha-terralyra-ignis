# Reading source health

Each location sensor exposes source_health in its Details view. Two independent
fields explain each source without changing existing status values or automations:

- retrieval_status: successful means a successful response is retained with no
  current reported retrieval failure; it may be a cached response. failed means
  the latest source attempt failed (including no usable product). unknown means
  success has not been established. This is not a live connectivity probe.
- data_freshness: within_provider_threshold or older_than_provider_threshold
  describes the snapshot according to that provider's threshold. unknown is used
  when the source result cannot currently be assessed.

Sentinel-3 uses the newest returned detection product time, or the service
response timestamp for an empty collection. Thus a successful response containing
old detections can be delayed. An empty current response is not proof of a fresh
satellite pass or that no fires exist. These are source-snapshot assessments,
not proof of complete observation coverage at each monitored location.

Read product_timestamp and received_timestamp together. A retained success
timestamp during an outage does not mean the latest request succeeded. The
existing available/degraded/partial state, freshness thresholds, requests and
history retention are unchanged.
